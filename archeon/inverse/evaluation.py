"""Evaluation metrics for inverse cosmology models.

Provides comprehensive comparison of CNN predictions vs MCMC
posterior and Planck published values.

Metrics:
- RMSE per parameter
- Bias (systematic offset)
- Calibration error (are uncertainties honest?)
- Coverage probability (do intervals contain truth?)
- Speed comparison (CNN vs MCMC wall-clock time)
- Planck tension (sigma distance from published values)
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np

from archeon.inverse.bayesian_cnn import PARAM_NAMES, N_PARAMS


# ---------------------------------------------------------------------------
# Planck 2018 reference values (TT,TE,EE+lowE+lensing)
# ---------------------------------------------------------------------------

PLANCK_2018 = {
    "H0":           (67.36, 0.54),
    "Omega_b_h2":   (0.02237, 0.00015),
    "Omega_cdm_h2": (0.1200, 0.0012),
    "n_s":          (0.9649, 0.0042),
    "ln10As":       (3.044, 0.014),
    "tau_reio":     (0.0544, 0.0073),
}


# ---------------------------------------------------------------------------
# Per-parameter metrics
# ---------------------------------------------------------------------------

@dataclass
class ParameterMetric:
    name: str
    rmse: float
    bias: float
    mean_sigma: float
    planck_tension: float     # n-sigma from Planck
    coverage_68: float
    coverage_95: float


@dataclass
class EvaluationReport:
    """Full evaluation report for an inverse cosmology model."""
    param_metrics: list[ParameterMetric]
    total_rmse: float
    total_ece: float
    mean_coverage_68: float
    mean_coverage_95: float
    inference_time_ms: float
    n_samples: int
    model_type: str

    def summary(self) -> str:
        lines = [
            f"Evaluation Report: {self.model_type}",
            "=" * 60,
            f"  Samples evaluated: {self.n_samples}",
            f"  Inference time:    {self.inference_time_ms:.1f} ms",
            f"  Total RMSE:        {self.total_rmse:.6f}",
            f"  ECE:               {self.total_ece:.4f}",
            f"  Mean 68% coverage: {self.mean_coverage_68:.3f} (target: 0.680)",
            f"  Mean 95% coverage: {self.mean_coverage_95:.3f} (target: 0.950)",
            "",
            f"  {'Parameter':>15s}  {'RMSE':>10s}  {'Bias':>10s}  "
            f"{'Mean σ':>10s}  {'Planck Δ':>8s}  {'Cov68':>6s}  {'Cov95':>6s}",
            "  " + "-" * 70,
        ]
        for pm in self.param_metrics:
            lines.append(
                f"  {pm.name:>15s}  {pm.rmse:>10.6f}  {pm.bias:>+10.6f}  "
                f"{pm.mean_sigma:>10.6f}  {pm.planck_tension:>7.2f}σ  "
                f"{pm.coverage_68:>6.3f}  {pm.coverage_95:>6.3f}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate_predictions(
    mu_pred: np.ndarray,
    sigma_pred: np.ndarray,
    theta_true: np.ndarray,
    model_type: str = "BayesianCNN",
    inference_time_ms: float = 0.0,
    param_names: list[str] | None = None,
) -> EvaluationReport:
    """Evaluate model predictions against ground truth.

    Parameters
    ----------
    mu_pred : array of shape (N, n_params)
        Predicted parameter means.
    sigma_pred : array of shape (N, n_params)
        Predicted parameter uncertainties.
    theta_true : array of shape (N, n_params)
        True parameter values.
    model_type : str
        Label for the model.
    inference_time_ms : float
        Wall-clock inference time in milliseconds.

    Returns
    -------
    EvaluationReport with per-parameter and aggregate metrics.
    """
    if param_names is None:
        param_names = PARAM_NAMES

    n = len(theta_true)
    param_metrics = []

    for i, name in enumerate(param_names):
        residuals = mu_pred[:, i] - theta_true[:, i]
        rmse = float(np.sqrt(np.mean(residuals**2)))
        bias = float(np.mean(residuals))
        mean_sigma = float(np.mean(sigma_pred[:, i]))

        # Coverage
        z68 = 1.0
        z95 = 1.96
        in_68 = np.mean(np.abs(residuals) <= z68 * sigma_pred[:, i])
        in_95 = np.mean(np.abs(residuals) <= z95 * sigma_pred[:, i])

        # Planck tension: how far is our mean from Planck?
        planck_val, planck_err = PLANCK_2018.get(name, (0, 1))
        mean_pred = np.mean(mu_pred[:, i])
        tension = abs(mean_pred - planck_val) / planck_err if planck_err > 0 else 0.0

        param_metrics.append(ParameterMetric(
            name=name,
            rmse=rmse,
            bias=bias,
            mean_sigma=mean_sigma,
            planck_tension=float(tension),
            coverage_68=float(in_68),
            coverage_95=float(in_95),
        ))

    total_rmse = float(np.sqrt(np.mean(
        [(pm.rmse)**2 for pm in param_metrics]
    )))

    from archeon.inverse.uncertainty import expected_calibration_error
    ece = expected_calibration_error(mu_pred, sigma_pred, theta_true)

    mean_cov68 = np.mean([pm.coverage_68 for pm in param_metrics])
    mean_cov95 = np.mean([pm.coverage_95 for pm in param_metrics])

    return EvaluationReport(
        param_metrics=param_metrics,
        total_rmse=total_rmse,
        total_ece=float(ece),
        mean_coverage_68=float(mean_cov68),
        mean_coverage_95=float(mean_cov95),
        inference_time_ms=inference_time_ms,
        n_samples=n,
        model_type=model_type,
    )


# ---------------------------------------------------------------------------
# CNN vs MCMC comparison
# ---------------------------------------------------------------------------

@dataclass
class ComparisonReport:
    cnn_report: EvaluationReport
    mcmc_report: EvaluationReport | None
    speedup: float
    agreement_sigma: np.ndarray  # per-param sigma distance between CNN and MCMC


def compare_cnn_vs_mcmc(
    cnn_mu: np.ndarray,
    cnn_sigma: np.ndarray,
    mcmc_means: np.ndarray,
    mcmc_stds: np.ndarray,
    theta_true: np.ndarray,
    cnn_time_ms: float,
    mcmc_time_ms: float,
) -> ComparisonReport:
    """Side-by-side comparison of CNN and MCMC.

    Key question: does the CNN match MCMC accuracy
    while being orders of magnitude faster?
    """
    cnn_report = evaluate_predictions(
        cnn_mu, cnn_sigma, theta_true,
        model_type="BayesianCNN",
        inference_time_ms=cnn_time_ms,
    )

    mcmc_report = evaluate_predictions(
        mcmc_means, mcmc_stds, theta_true,
        model_type="MCMC (emcee)",
        inference_time_ms=mcmc_time_ms,
    )

    combined_sigma = np.sqrt(cnn_sigma.mean(axis=0)**2 + mcmc_stds.mean(axis=0)**2)
    agreement = np.abs(cnn_mu.mean(axis=0) - mcmc_means.mean(axis=0)) / combined_sigma

    speedup = mcmc_time_ms / max(cnn_time_ms, 0.001)

    return ComparisonReport(
        cnn_report=cnn_report,
        mcmc_report=mcmc_report,
        speedup=speedup,
        agreement_sigma=agreement,
    )


# ---------------------------------------------------------------------------
# Benchmark utility
# ---------------------------------------------------------------------------

def benchmark_inference(model, x_batch, n_repeats: int = 100,
                         device: str = "cpu") -> float:
    """Measure average inference time in milliseconds."""
    import torch
    model = model.to(device)
    model.eval()
    x_batch = x_batch.to(device)

    # Warmup
    with torch.no_grad():
        for _ in range(10):
            model(x_batch)

    start = perf_counter()
    with torch.no_grad():
        for _ in range(n_repeats):
            model(x_batch)
    elapsed = perf_counter() - start

    return (elapsed / n_repeats) * 1000
