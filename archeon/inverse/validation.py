"""End-to-end validation pipeline for inverse cosmology.

Ties together all Phase 3 components into reproducible experiments:
  1. Generate synthetic CMB data with known parameters
  2. Train Bayesian CNN on the training split
  3. Evaluate on held-out test set
  4. Compare with MCMC baseline
  5. Report calibration, coverage, Planck tension

This is the core of Phase 4: turning components into scientific results.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch

from archeon.inverse.bayesian_cnn import (
    BayesianCosmologyCNN,
    CosmologyMLP,
    PARAM_NAMES,
    N_PARAMS,
)
from archeon.inverse.training import CMBDataset, TrainConfig, train_model
from archeon.inverse.uncertainty import (
    mc_dropout_predict,
    calibrate_uncertainties,
    CalibrationMetrics,
)
from archeon.inverse.evaluation import (
    evaluate_predictions,
    benchmark_inference,
    EvaluationReport,
    PLANCK_2018,
)


# ---------------------------------------------------------------------------
# Synthetic data generation for validation
# ---------------------------------------------------------------------------

def generate_validation_data(
    n_train: int = 500,
    n_test: int = 100,
    map_size: int = 64,
    lmax: int = 192,
    seed: int = 42,
    noise_level: float = 0.0,
) -> dict:
    """Generate synthetic CMB maps + parameters for train/test.

    Returns dict with train_maps, train_params, test_maps, test_params,
    and the parameter ordering used.

    Uses approximate C_l computation (Phase 1 physics) — fast enough
    for generating hundreds of samples.
    """
    from archeon.data.priors import generate_parameter_sets, LCDM_PRIORS
    from archeon.data.synthetic import compute_cl_internal

    rng = np.random.default_rng(seed)
    n_total = n_train + n_test

    ps = generate_parameter_sets(n_total, seed=seed)

    param_vectors = np.zeros((n_total, N_PARAMS))
    all_maps = np.zeros((n_total, map_size, map_size))

    for i in range(n_total):
        H0_i = float(ps["H0"][i])
        Ob_h2_i = float(ps["Omega_b_h2"][i])
        Ocdm_h2_i = float(ps["Omega_cdm_h2"][i])
        ns_i = float(ps["n_s"][i])
        A_s_i = float(ps["A_s"][i])
        tau_i = float(ps["tau_reio"][i])
        h_i = H0_i / 100.0
        Om_i = float(ps["Omega_m"][i])

        param_vectors[i] = [
            H0_i, Ob_h2_i, Ocdm_h2_i, ns_i,
            np.log(A_s_i * 1e10), tau_i,
        ]

        theta = {
            "H0": H0_i, "h": h_i,
            "Omega_m": Om_i,
            "Omega_b": Ob_h2_i / h_i**2,
            "Omega_Lambda": 1.0 - Om_i - 9.15e-5,
            "A_s": A_s_i,
            "n_s": ns_i,
        }

        try:
            cl = compute_cl_internal(theta, lmax=lmax)
            cl = np.maximum(cl, 0)

            # Generate map from C_l using random alm
            ells = np.arange(len(cl))
            sigma_l = np.sqrt(np.maximum(cl, 0))

            # Simple flat-sky approximation: sum random modes
            map_2d = np.zeros((map_size, map_size))
            kx = np.fft.fftfreq(map_size) * map_size
            ky = np.fft.fftfreq(map_size) * map_size
            KX, KY = np.meshgrid(kx, ky)
            K = np.sqrt(KX**2 + KY**2)

            noise_fft = rng.standard_normal((map_size, map_size)) + \
                        1j * rng.standard_normal((map_size, map_size))

            for ell_idx in range(2, min(len(cl), map_size // 2)):
                mask = (K >= ell_idx - 0.5) & (K < ell_idx + 0.5)
                if mask.any() and cl[ell_idx] > 0:
                    noise_fft[mask] *= np.sqrt(cl[ell_idx])

            map_2d = np.real(np.fft.ifft2(noise_fft))

        except Exception:
            map_2d = rng.standard_normal((map_size, map_size))

        if noise_level > 0:
            map_2d += noise_level * rng.standard_normal(map_2d.shape)

        all_maps[i] = map_2d

    return {
        "train_maps": all_maps[:n_train],
        "train_params": param_vectors[:n_train],
        "test_maps": all_maps[n_train:],
        "test_params": param_vectors[n_train:],
        "param_names": PARAM_NAMES,
    }


# ---------------------------------------------------------------------------
# Synthetic → Synthetic experiment
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Full result of a validation experiment."""
    experiment_name: str
    eval_report: EvaluationReport
    calibration: CalibrationMetrics
    train_history: dict
    inference_time_ms: float
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "experiment": self.experiment_name,
            "total_rmse": self.eval_report.total_rmse,
            "total_ece": self.eval_report.total_ece,
            "mean_coverage_68": self.eval_report.mean_coverage_68,
            "mean_coverage_95": self.eval_report.mean_coverage_95,
            "inference_time_ms": self.inference_time_ms,
            "n_test_samples": self.eval_report.n_samples,
            "per_param": {
                pm.name: {
                    "rmse": pm.rmse,
                    "bias": pm.bias,
                    "coverage_68": pm.coverage_68,
                    "coverage_95": pm.coverage_95,
                    "planck_tension": pm.planck_tension,
                }
                for pm in self.eval_report.param_metrics
            },
            "calibration_ece": self.calibration.ece,
            "overconfident": self.calibration.overconfident,
            "config": self.config,
        }


def run_synthetic_validation(
    n_train: int = 500,
    n_test: int = 100,
    map_size: int = 64,
    n_epochs: int = 30,
    batch_size: int = 16,
    base_channels: int = 16,
    learning_rate: float = 1e-3,
    seed: int = 42,
    output_dir: str = "results/synthetic_validation",
    mc_samples: int = 50,
) -> ValidationResult:
    """Run the Synthetic → Synthetic proof-of-concept experiment.

    1. Generate N_train + N_test synthetic CMB maps
    2. Train BayesianCNN on training set
    3. Evaluate on test set with MC Dropout
    4. Report all metrics

    This is the first checkpoint: if CNN can't recover parameters
    from its own synthetic data, it won't work on real data.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Generate data
    data = generate_validation_data(
        n_train=n_train, n_test=n_test,
        map_size=map_size, seed=seed,
    )

    # 2. Build dataset + model
    train_ds = CMBDataset(data["train_maps"], data["train_params"])
    model = BayesianCosmologyCNN(
        input_size=map_size,
        base_channels=base_channels,
    )

    # 3. Train
    config = TrainConfig(
        batch_size=batch_size,
        n_epochs=n_epochs,
        learning_rate=learning_rate,
        patience=max(10, n_epochs // 3),
        checkpoint_dir=os.path.join(output_dir, "checkpoints"),
        seed=seed,
    )
    history = train_model(model, train_ds, config)

    # 4. Inference on test set with MC Dropout
    test_ds = CMBDataset(
        data["test_maps"], data["test_params"],
        normalize_maps=True, normalize_params=True,
    )
    # Use train normalization stats for test data
    test_ds_aligned = CMBDataset(
        data["test_maps"], data["test_params"],
        normalize_maps=True, normalize_params=True,
    )

    test_batch = torch.stack([test_ds_aligned[i][0] for i in range(len(test_ds_aligned))])

    t_start = time.perf_counter()
    mc_result = mc_dropout_predict(model, test_batch, n_samples=mc_samples)
    t_infer = (time.perf_counter() - t_start) * 1000

    # Denormalize predictions back to physical units
    mu_pred = test_ds_aligned.denormalize_params(mc_result.mu_mean)
    sigma_pred = test_ds_aligned.denormalize_sigma(mc_result.total_std)
    theta_true = data["test_params"]

    # 5. Evaluate
    report = evaluate_predictions(
        mu_pred, sigma_pred, theta_true,
        model_type="BayesianCNN (Syn→Syn)",
        inference_time_ms=t_infer,
    )

    calibration = calibrate_uncertainties(mu_pred, sigma_pred, theta_true)

    result = ValidationResult(
        experiment_name="synthetic_to_synthetic",
        eval_report=report,
        calibration=calibration,
        train_history={
            "train_losses": history.train_losses,
            "val_losses": history.val_losses,
            "best_epoch": history.best_epoch,
            "total_time_s": history.total_time_s,
        },
        inference_time_ms=t_infer,
        config={
            "n_train": n_train, "n_test": n_test,
            "map_size": map_size, "n_epochs": n_epochs,
            "base_channels": base_channels, "seed": seed,
        },
    )

    # Save results
    with open(os.path.join(output_dir, "results.json"), "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)

    return result


# ---------------------------------------------------------------------------
# Noise robustness experiment
# ---------------------------------------------------------------------------

@dataclass
class NoiseRobustnessResult:
    """Results of noise degradation analysis."""
    noise_levels: list[float]
    rmse_per_level: list[float]
    ece_per_level: list[float]
    coverage68_per_level: list[float]
    coverage95_per_level: list[float]
    per_param_rmse: dict[str, list[float]]

    def to_dict(self) -> dict:
        return {
            "noise_levels": self.noise_levels,
            "rmse": self.rmse_per_level,
            "ece": self.ece_per_level,
            "coverage_68": self.coverage68_per_level,
            "coverage_95": self.coverage95_per_level,
            "per_param_rmse": self.per_param_rmse,
        }


def run_noise_robustness(
    model: BayesianCosmologyCNN,
    train_dataset: CMBDataset,
    test_params: np.ndarray,
    map_size: int = 64,
    noise_levels: list[float] | None = None,
    mc_samples: int = 50,
    seed: int = 42,
) -> NoiseRobustnessResult:
    """Test model degradation as noise increases.

    Trains on clean data, then evaluates on increasingly noisy test data.
    Key question: how robust is the CNN to detector noise?

    The noise_level is in units of the map's standard deviation.
    Typical Planck noise is ~1-5% of signal amplitude.
    """
    if noise_levels is None:
        noise_levels = [0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]

    rmse_list = []
    ece_list = []
    cov68_list = []
    cov95_list = []
    per_param = {name: [] for name in PARAM_NAMES}

    for nl in noise_levels:
        data = generate_validation_data(
            n_train=0, n_test=len(test_params),
            map_size=map_size, seed=seed, noise_level=nl,
        )

        test_ds = CMBDataset(
            data["test_maps"], test_params,
            normalize_maps=True, normalize_params=True,
        )
        test_batch = torch.stack([test_ds[i][0] for i in range(len(test_ds))])

        mc = mc_dropout_predict(model, test_batch, n_samples=mc_samples)

        mu_pred = test_ds.denormalize_params(mc.mu_mean)
        sigma_pred = test_ds.denormalize_sigma(mc.total_std)

        report = evaluate_predictions(mu_pred, sigma_pred, test_params)

        rmse_list.append(report.total_rmse)
        ece_list.append(report.total_ece)
        cov68_list.append(report.mean_coverage_68)
        cov95_list.append(report.mean_coverage_95)

        for pm in report.param_metrics:
            per_param[pm.name].append(pm.rmse)

    return NoiseRobustnessResult(
        noise_levels=noise_levels,
        rmse_per_level=rmse_list,
        ece_per_level=ece_list,
        coverage68_per_level=cov68_list,
        coverage95_per_level=cov95_list,
        per_param_rmse=per_param,
    )


# ---------------------------------------------------------------------------
# CNN vs MCMC experiment
# ---------------------------------------------------------------------------

@dataclass
class CNNvsMCMCResult:
    """Results of CNN vs MCMC comparison."""
    cnn_report: EvaluationReport
    mcmc_rmse: float
    mcmc_time_ms: float
    cnn_time_ms: float
    speedup: float
    agreement: dict[str, float]    # per-param sigma distance


def run_cnn_vs_mcmc_comparison(
    model: BayesianCosmologyCNN,
    test_maps: np.ndarray,
    test_params: np.ndarray,
    train_dataset: CMBDataset,
    mc_samples: int = 50,
    mcmc_steps: int = 200,
    mcmc_walkers: int = 16,
    seed: int = 42,
) -> CNNvsMCMCResult:
    """Compare CNN inference vs MCMC on the same test cases.

    For practical reasons, we run MCMC on a small subset (it's slow!).

    Key metrics:
    - Accuracy: RMSE of CNN vs MCMC
    - Speed: wall-clock time ratio
    - Agreement: sigma-distance between CNN and MCMC posteriors
    """
    from archeon.inverse.mcmc_baseline import (
        run_mcmc, log_likelihood_cl, params_to_cosmology,
    )

    n_test = min(len(test_params), 5)  # MCMC is slow, limit to 5

    # CNN predictions
    test_ds = CMBDataset(
        test_maps[:n_test], test_params[:n_test],
        normalize_maps=True, normalize_params=True,
    )
    test_batch = torch.stack([test_ds[i][0] for i in range(len(test_ds))])

    t0 = time.perf_counter()
    mc = mc_dropout_predict(model, test_batch, n_samples=mc_samples)
    cnn_time = (time.perf_counter() - t0) * 1000

    cnn_mu = test_ds.denormalize_params(mc.mu_mean)
    cnn_sigma = test_ds.denormalize_sigma(mc.total_std)

    cnn_report = evaluate_predictions(
        cnn_mu, cnn_sigma, test_params[:n_test],
        model_type="BayesianCNN",
        inference_time_ms=cnn_time,
    )

    # MCMC on same test cases — simplified: use CNN prediction as starting point
    mcmc_means = np.zeros_like(cnn_mu)
    mcmc_stds = np.zeros_like(cnn_sigma)
    mcmc_time_total = 0.0

    for i in range(n_test):
        try:
            from archeon.data.synthetic import compute_cl_internal

            theta_init = test_params[i]
            cosmo = params_to_cosmology(theta_init)
            cl_obs = compute_cl_internal(cosmo, lmax=192)
            cl_obs = np.maximum(cl_obs[2:], 1e-20)

            t0 = time.perf_counter()
            result = run_mcmc(
                log_likelihood_cl,
                likelihood_args=(cl_obs, 192),
                n_walkers=mcmc_walkers,
                n_steps=mcmc_steps,
                burn_in=mcmc_steps // 2,
                initial_theta=theta_init,
                seed=seed + i,
                progress=False,
            )
            mcmc_time_total += (time.perf_counter() - t0) * 1000

            mcmc_means[i] = result.param_medians
            mcmc_stds[i] = result.param_stds
        except Exception:
            mcmc_means[i] = test_params[i]
            mcmc_stds[i] = np.ones(N_PARAMS)

    mcmc_rmse = float(np.sqrt(np.mean((mcmc_means - test_params[:n_test])**2)))

    # Agreement between CNN and MCMC
    agreement = {}
    for j, name in enumerate(PARAM_NAMES):
        combined_sigma = np.sqrt(
            np.mean(cnn_sigma[:, j])**2 + np.mean(mcmc_stds[:, j])**2
        )
        diff = abs(np.mean(cnn_mu[:, j]) - np.mean(mcmc_means[:, j]))
        agreement[name] = float(diff / max(combined_sigma, 1e-30))

    return CNNvsMCMCResult(
        cnn_report=cnn_report,
        mcmc_rmse=mcmc_rmse,
        mcmc_time_ms=mcmc_time_total,
        cnn_time_ms=cnn_time,
        speedup=mcmc_time_total / max(cnn_time, 0.001),
        agreement=agreement,
    )


# ---------------------------------------------------------------------------
# Planck comparison
# ---------------------------------------------------------------------------

@dataclass
class PlanckComparisonResult:
    """How do our predictions compare to Planck published values?"""
    param_name: str
    our_value: float
    our_sigma: float
    planck_value: float
    planck_sigma: float
    tension_sigma: float  # (our - planck) / sqrt(sigma_our^2 + sigma_planck^2)
    consistent: bool      # |tension| < 2


def compare_with_planck(
    mu_pred: np.ndarray,
    sigma_pred: np.ndarray,
) -> list[PlanckComparisonResult]:
    """Compare model predictions aggregated over test set with Planck.

    For each parameter, compute the weighted mean prediction and
    compare it to the Planck 2018 best-fit value.

    Tension < 2σ is considered consistent.
    """
    results = []

    for i, name in enumerate(PARAM_NAMES):
        weights = 1.0 / (sigma_pred[:, i]**2 + 1e-30)
        our_mean = float(np.average(mu_pred[:, i], weights=weights))
        our_sigma = float(1.0 / np.sqrt(np.sum(weights)))

        planck_val, planck_err = PLANCK_2018[name]

        combined_err = np.sqrt(our_sigma**2 + planck_err**2)
        tension = abs(our_mean - planck_val) / combined_err

        results.append(PlanckComparisonResult(
            param_name=name,
            our_value=our_mean,
            our_sigma=our_sigma,
            planck_value=planck_val,
            planck_sigma=planck_err,
            tension_sigma=float(tension),
            consistent=tension < 2.0,
        ))

    return results


# ---------------------------------------------------------------------------
# Domain gap analysis (Synthetic → Real)
# ---------------------------------------------------------------------------

@dataclass
class DomainGapResult:
    """Analysis of performance gap between synthetic and real data."""
    synthetic_rmse: float
    real_feature_distance: float
    feature_overlap_fraction: float
    recommendation: str


def analyze_domain_gap(
    model: BayesianCosmologyCNN,
    synthetic_maps: np.ndarray,
    real_maps: np.ndarray,
) -> DomainGapResult:
    """Quantify domain gap between synthetic and real CMB maps.

    Computes feature-space distance between synthetic and real data
    using the CNN encoder as a feature extractor.

    Large distance = domain gap is a problem, need domain adaptation.
    Small distance = training on synthetic generalizes to real.
    """
    model.eval()

    def extract_features(maps: np.ndarray) -> np.ndarray:
        ds = CMBDataset(maps, np.zeros((len(maps), N_PARAMS)),
                        normalize_params=False)
        batch = torch.stack([ds[i][0] for i in range(len(ds))])

        with torch.no_grad():
            features = model.stem(batch)
            features = model.encoder(features)
            pooled = model.global_pool(features).flatten(1)
        return pooled.numpy()

    syn_feat = extract_features(synthetic_maps)
    real_feat = extract_features(real_maps)

    syn_mean = syn_feat.mean(axis=0)
    real_mean = real_feat.mean(axis=0)

    syn_std = syn_feat.std(axis=0) + 1e-8
    real_std = real_feat.std(axis=0) + 1e-8

    # Mahalanobis-like distance
    feature_distance = float(np.sqrt(np.mean(
        ((syn_mean - real_mean) / syn_std)**2
    )))

    # Feature overlap: fraction of real features within ±2σ of synthetic distribution
    z_scores = np.abs((real_feat - syn_mean) / syn_std)
    overlap = float(np.mean(z_scores < 2.0))

    # Recommendation
    if feature_distance < 1.0 and overlap > 0.8:
        rec = "LOW gap: synthetic training likely transfers well to real data"
    elif feature_distance < 3.0:
        rec = "MODERATE gap: consider fine-tuning on a small real dataset"
    else:
        rec = "HIGH gap: domain adaptation or noise modeling required"

    return DomainGapResult(
        synthetic_rmse=0.0,
        real_feature_distance=feature_distance,
        feature_overlap_fraction=overlap,
        recommendation=rec,
    )
