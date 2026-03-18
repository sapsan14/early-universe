"""Uncertainty calibration for Bayesian CNN predictions.

Three complementary methods for reliable uncertainty estimation:

1. MC Dropout — run N forward passes with dropout active, measure spread
2. Deep Ensembles — train M independent models, combine predictions
3. Calibration metrics — verify that stated uncertainties match reality

Well-calibrated uncertainty is CRITICAL for scientific claims:
  "We measure H0 = 67.4 ± 0.5 km/s/Mpc"
  If the ±0.5 is wrong, the scientific result is meaningless.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
import torch.nn as nn

from archeon.inverse.bayesian_cnn import BayesianCosmologyCNN, N_PARAMS


# ---------------------------------------------------------------------------
# MC Dropout
# ---------------------------------------------------------------------------

@dataclass
class MCDropoutResult:
    """Result container for MC Dropout inference."""
    mu_mean: np.ndarray       # (batch, n_params) mean of predictions
    mu_std: np.ndarray        # (batch, n_params) std of predictions (epistemic)
    aleatoric: np.ndarray     # (batch, n_params) mean aleatoric variance
    epistemic: np.ndarray     # (batch, n_params) epistemic variance
    total_std: np.ndarray     # (batch, n_params) total uncertainty
    all_mus: np.ndarray       # (n_samples, batch, n_params) raw samples


def mc_dropout_predict(model: BayesianCosmologyCNN, x: torch.Tensor,
                        n_samples: int = 100,
                        device: str = "cpu") -> MCDropoutResult:
    """Run MC Dropout: N stochastic forward passes with dropout enabled.

    Epistemic uncertainty emerges from the variation between passes.
    In the limit of infinite samples, this approximates variational inference.
    """
    model = model.to(device)
    x = x.to(device)
    model.train()  # keep dropout active

    all_mus = []
    all_log_sigmas = []

    with torch.no_grad():
        for _ in range(n_samples):
            mu, log_sigma = model(x)
            all_mus.append(mu.cpu().numpy())
            all_log_sigmas.append(log_sigma.cpu().numpy())

    all_mus = np.stack(all_mus)               # (n_samples, batch, n_params)
    all_log_sigmas = np.stack(all_log_sigmas)

    mu_mean = all_mus.mean(axis=0)
    epistemic = all_mus.var(axis=0)
    aleatoric = np.exp(2 * all_log_sigmas).mean(axis=0)
    total_var = epistemic + aleatoric

    return MCDropoutResult(
        mu_mean=mu_mean,
        mu_std=all_mus.std(axis=0),
        aleatoric=aleatoric,
        epistemic=epistemic,
        total_std=np.sqrt(total_var),
        all_mus=all_mus,
    )


# ---------------------------------------------------------------------------
# Deep Ensembles
# ---------------------------------------------------------------------------

@dataclass
class EnsembleResult:
    """Result container for Deep Ensemble prediction."""
    mu_mean: np.ndarray       # (batch, n_params)
    mu_std: np.ndarray        # (batch, n_params)
    aleatoric: np.ndarray     # (batch, n_params)
    epistemic: np.ndarray     # (batch, n_params)
    total_std: np.ndarray     # (batch, n_params)
    member_mus: np.ndarray    # (n_members, batch, n_params)


class DeepEnsemble:
    """Ensemble of independently trained BayesianCosmologyCNNs.

    Deep Ensembles (Lakshminarayanan et al. 2017) provide
    better-calibrated uncertainty than MC Dropout in practice.

    Each member sees different random initialization and data shuffling,
    so disagreement between members captures epistemic uncertainty.
    """

    def __init__(self, n_members: int = 5, **model_kwargs):
        self.n_members = n_members
        self.model_kwargs = model_kwargs
        self.members: list[BayesianCosmologyCNN] = [
            BayesianCosmologyCNN(**model_kwargs) for _ in range(n_members)
        ]

    def predict(self, x: torch.Tensor, device: str = "cpu") -> EnsembleResult:
        """Combine predictions from all ensemble members."""
        x = x.to(device)

        member_mus = []
        member_log_sigmas = []

        for model in self.members:
            model = model.to(device)
            model.eval()
            with torch.no_grad():
                mu, log_sigma = model(x)
                member_mus.append(mu.cpu().numpy())
                member_log_sigmas.append(log_sigma.cpu().numpy())

        member_mus = np.stack(member_mus)
        member_log_sigmas = np.stack(member_log_sigmas)

        mu_mean = member_mus.mean(axis=0)
        epistemic = member_mus.var(axis=0)
        aleatoric = np.exp(2 * member_log_sigmas).mean(axis=0)
        total_var = epistemic + aleatoric

        return EnsembleResult(
            mu_mean=mu_mean,
            mu_std=member_mus.std(axis=0),
            aleatoric=aleatoric,
            epistemic=epistemic,
            total_std=np.sqrt(total_var),
            member_mus=member_mus,
        )

    def save(self, directory: str):
        """Save all ensemble member weights."""
        import os
        os.makedirs(directory, exist_ok=True)
        for i, model in enumerate(self.members):
            torch.save(model.state_dict(), os.path.join(directory, f"member_{i}.pt"))

    def load(self, directory: str, device: str = "cpu"):
        """Load all ensemble member weights."""
        import os
        for i, model in enumerate(self.members):
            path = os.path.join(directory, f"member_{i}.pt")
            model.load_state_dict(torch.load(path, map_location=device, weights_only=True))


# ---------------------------------------------------------------------------
# Calibration metrics
# ---------------------------------------------------------------------------

@dataclass
class CalibrationMetrics:
    """Calibration assessment results."""
    ece: float                        # expected calibration error
    coverage: dict[float, float]      # {confidence_level: actual_coverage}
    sharpness: np.ndarray             # mean predicted sigma per parameter
    overconfident: bool               # True if coverage < target
    details: str = ""


def expected_calibration_error(
    mu_pred: np.ndarray,
    sigma_pred: np.ndarray,
    theta_true: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error (ECE) for regression.

    For a well-calibrated model, the fraction of true values falling
    within the p-confidence interval should be exactly p, for all p.

    ECE measures the average deviation from perfect calibration:
      ECE = (1/B) * sum |freq_b - conf_b|

    where freq_b is the observed frequency and conf_b is the predicted
    confidence level for bin b.
    """
    confidence_levels = np.linspace(0.05, 0.95, n_bins)
    ece = 0.0

    for conf in confidence_levels:
        from scipy.stats import norm
        z = norm.ppf((1 + conf) / 2)
        lower = mu_pred - z * sigma_pred
        upper = mu_pred + z * sigma_pred
        fraction_in = np.mean((theta_true >= lower) & (theta_true <= upper))
        ece += abs(fraction_in - conf)

    return ece / n_bins


def coverage_probability(
    mu_pred: np.ndarray,
    sigma_pred: np.ndarray,
    theta_true: np.ndarray,
    levels: list[float] | None = None,
) -> dict[float, float]:
    """Compute coverage probabilities at specified confidence levels.

    For each confidence level p:
      coverage(p) = fraction of true values within p-sigma interval.

    Perfect calibration: coverage(0.68) = 0.68, coverage(0.95) = 0.95, etc.
    """
    if levels is None:
        levels = [0.50, 0.68, 0.90, 0.95, 0.99]

    from scipy.stats import norm
    result = {}

    for level in levels:
        z = norm.ppf((1 + level) / 2)
        lower = mu_pred - z * sigma_pred
        upper = mu_pred + z * sigma_pred
        fraction = np.mean((theta_true >= lower) & (theta_true <= upper))
        result[level] = float(fraction)

    return result


def calibrate_uncertainties(
    mu_pred: np.ndarray,
    sigma_pred: np.ndarray,
    theta_true: np.ndarray,
) -> CalibrationMetrics:
    """Full calibration assessment.

    Returns ECE, coverage at standard levels, sharpness, and
    a diagnostic flag for overconfidence.
    """
    ece = expected_calibration_error(mu_pred, sigma_pred, theta_true)
    coverage = coverage_probability(mu_pred, sigma_pred, theta_true)
    sharpness = sigma_pred.mean(axis=0)

    overconfident = coverage.get(0.95, 1.0) < 0.90

    lines = [
        f"ECE = {ece:.4f}",
        "Coverage:",
    ]
    for level, cov in sorted(coverage.items()):
        status = "OK" if abs(cov - level) < 0.05 else ("OVER" if cov < level else "UNDER")
        lines.append(f"  {level:.0%}: {cov:.3f} [{status}]")
    lines.append(f"Mean sharpness: {sharpness}")
    lines.append(f"Overconfident: {overconfident}")

    return CalibrationMetrics(
        ece=ece,
        coverage=coverage,
        sharpness=sharpness,
        overconfident=overconfident,
        details="\n".join(lines),
    )


# ---------------------------------------------------------------------------
# Temperature scaling (post-hoc calibration)
# ---------------------------------------------------------------------------

def temperature_scale(
    mu_pred: np.ndarray,
    sigma_pred: np.ndarray,
    theta_true: np.ndarray,
) -> float:
    """Find optimal temperature T to recalibrate uncertainties.

    sigma_calibrated = T * sigma_pred

    Optimizes T to minimize NLL on a validation set.
    T > 1 means model is overconfident, T < 1 means underconfident.
    """
    from scipy.optimize import minimize_scalar

    def nll(log_T):
        T = np.exp(log_T)
        sigma = T * sigma_pred
        return 0.5 * np.mean(
            ((theta_true - mu_pred)**2 / sigma**2) + 2 * np.log(sigma)
        )

    result = minimize_scalar(nll, bounds=(-3, 3), method="bounded")
    return float(np.exp(result.x))
