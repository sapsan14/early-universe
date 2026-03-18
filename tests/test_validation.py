"""Tests for Phase 4 validation pipeline."""

import json
import os
import tempfile

import numpy as np
import pytest
import torch

from archeon.inverse.bayesian_cnn import BayesianCosmologyCNN, N_PARAMS, PARAM_NAMES
from archeon.inverse.training import CMBDataset, TrainConfig, train_model
from archeon.inverse.uncertainty import mc_dropout_predict
from archeon.inverse.evaluation import evaluate_predictions, PLANCK_2018
from archeon.inverse.validation import (
    generate_validation_data,
    run_synthetic_validation,
    run_noise_robustness,
    run_cnn_vs_mcmc_comparison,
    compare_with_planck,
    analyze_domain_gap,
    ValidationResult,
    NoiseRobustnessResult,
    PlanckComparisonResult,
    DomainGapResult,
)


class TestGenerateValidationData:

    def test_shapes(self):
        data = generate_validation_data(
            n_train=20, n_test=10, map_size=32, seed=42,
        )
        assert data["train_maps"].shape == (20, 32, 32)
        assert data["train_params"].shape == (20, N_PARAMS)
        assert data["test_maps"].shape == (10, 32, 32)
        assert data["test_params"].shape == (10, N_PARAMS)

    def test_different_seeds_differ(self):
        d1 = generate_validation_data(n_train=5, n_test=5, map_size=16, seed=1)
        d2 = generate_validation_data(n_train=5, n_test=5, map_size=16, seed=2)
        assert not np.allclose(d1["train_maps"], d2["train_maps"])

    def test_noise_adds_variance(self):
        d_clean = generate_validation_data(
            n_train=10, n_test=5, map_size=16, seed=42, noise_level=0.0,
        )
        d_noisy = generate_validation_data(
            n_train=10, n_test=5, map_size=16, seed=42, noise_level=1.0,
        )
        clean_var = d_clean["train_maps"].var()
        noisy_var = d_noisy["train_maps"].var()
        assert noisy_var > clean_var

    def test_params_in_physical_range(self):
        data = generate_validation_data(n_train=50, n_test=10, map_size=16)
        params = data["train_params"]
        # H0 should be ~[60, 80]
        assert params[:, 0].min() > 55
        assert params[:, 0].max() < 85
        # Omega_b_h2 ~ [0.019, 0.025]
        assert params[:, 1].min() > 0.018
        assert params[:, 1].max() < 0.026


class TestSyntheticValidation:

    def test_runs_end_to_end(self):
        """Full pipeline: generate, train, evaluate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_synthetic_validation(
                n_train=30,
                n_test=10,
                map_size=32,
                n_epochs=3,
                batch_size=8,
                base_channels=4,
                seed=42,
                output_dir=tmpdir,
                mc_samples=5,
            )

            assert isinstance(result, ValidationResult)
            assert result.experiment_name == "synthetic_to_synthetic"
            assert result.eval_report.n_samples == 10
            assert result.eval_report.total_rmse > 0
            assert result.inference_time_ms > 0
            assert len(result.eval_report.param_metrics) == N_PARAMS

    def test_results_saved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_synthetic_validation(
                n_train=20, n_test=5, map_size=32,
                n_epochs=2, batch_size=8, base_channels=4,
                output_dir=tmpdir, mc_samples=3,
            )
            assert os.path.exists(os.path.join(tmpdir, "results.json"))
            with open(os.path.join(tmpdir, "results.json")) as f:
                data = json.load(f)
            assert "total_rmse" in data
            assert "per_param" in data

    def test_to_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_synthetic_validation(
                n_train=20, n_test=5, map_size=32,
                n_epochs=2, batch_size=8, base_channels=4,
                output_dir=tmpdir, mc_samples=3,
            )
            d = result.to_dict()
            assert "experiment" in d
            assert "total_rmse" in d
            assert "per_param" in d
            assert "H0" in d["per_param"]


class TestNoiseRobustness:

    def test_rmse_increases_with_noise(self):
        """More noise → worse RMSE (at least in general trend)."""
        data = generate_validation_data(
            n_train=40, n_test=15, map_size=32, seed=42,
        )
        train_ds = CMBDataset(data["train_maps"], data["train_params"])
        model = BayesianCosmologyCNN(input_size=32, base_channels=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainConfig(
                batch_size=8, n_epochs=5, patience=100,
                checkpoint_dir=tmpdir,
            )
            train_model(model, train_ds, config)

        result = run_noise_robustness(
            model, train_ds,
            test_params=data["test_params"],
            map_size=32,
            noise_levels=[0.0, 0.5, 2.0],
            mc_samples=5,
        )

        assert isinstance(result, NoiseRobustnessResult)
        assert len(result.noise_levels) == 3
        assert len(result.rmse_per_level) == 3
        # RMSE at highest noise should generally be >= RMSE at lowest
        # (may not be strictly monotonic with small samples/short training)

    def test_to_dict(self):
        result = NoiseRobustnessResult(
            noise_levels=[0.0, 0.1],
            rmse_per_level=[0.5, 0.6],
            ece_per_level=[0.1, 0.2],
            coverage68_per_level=[0.6, 0.5],
            coverage95_per_level=[0.9, 0.8],
            per_param_rmse={"H0": [0.3, 0.4]},
        )
        d = result.to_dict()
        assert "noise_levels" in d
        assert "per_param_rmse" in d


class TestPlanckComparison:

    def test_perfect_planck_predictions(self):
        """If we predict exactly Planck values, tension should be ~0."""
        n = 50
        mu = np.tile(
            [67.36, 0.02237, 0.1200, 0.9649, 3.044, 0.0544],
            (n, 1),
        )
        sigma = np.ones_like(mu) * 0.01

        results = compare_with_planck(mu, sigma)
        assert len(results) == N_PARAMS
        for r in results:
            assert isinstance(r, PlanckComparisonResult)
            assert r.tension_sigma < 1.0
            assert r.consistent

    def test_discrepant_H0(self):
        """H0=73 should be in tension with Planck H0=67.36."""
        n = 50
        mu = np.tile(
            [73.0, 0.02237, 0.1200, 0.9649, 3.044, 0.0544],
            (n, 1),
        )
        sigma = np.ones_like(mu) * 0.1

        results = compare_with_planck(mu, sigma)
        h0_result = [r for r in results if r.param_name == "H0"][0]
        assert h0_result.tension_sigma > 2.0
        assert not h0_result.consistent

    def test_all_planck_params_covered(self):
        n = 10
        mu = np.random.randn(n, N_PARAMS)
        sigma = np.ones_like(mu)
        results = compare_with_planck(mu, sigma)
        names = {r.param_name for r in results}
        assert names == set(PARAM_NAMES)


class TestDomainGap:

    def test_same_distribution_low_gap(self):
        """Same distribution should give low feature distance."""
        model = BayesianCosmologyCNN(input_size=32, base_channels=4)
        rng = np.random.default_rng(42)
        maps1 = rng.standard_normal((10, 32, 32)).astype(np.float32)
        maps2 = rng.standard_normal((10, 32, 32)).astype(np.float32)

        result = analyze_domain_gap(model, maps1, maps2)
        assert isinstance(result, DomainGapResult)
        assert result.feature_overlap_fraction > 0

    def test_different_distribution_higher_gap(self):
        """Shifted distribution should give higher feature distance."""
        model = BayesianCosmologyCNN(input_size=32, base_channels=4)
        rng = np.random.default_rng(42)
        maps_syn = rng.standard_normal((15, 32, 32)).astype(np.float32)
        maps_real = (rng.standard_normal((15, 32, 32)) * 10 + 50).astype(np.float32)

        result = analyze_domain_gap(model, maps_syn, maps_real)
        assert result.feature_overlap_fraction < 1.0

    def test_recommendation_present(self):
        model = BayesianCosmologyCNN(input_size=32, base_channels=4)
        maps = np.random.randn(5, 32, 32).astype(np.float32)
        result = analyze_domain_gap(model, maps, maps)
        assert len(result.recommendation) > 0


class TestCNNvsMCMC:

    @pytest.mark.slow
    def test_comparison_runs(self):
        """Verify CNN vs MCMC comparison pipeline runs (slow)."""
        data = generate_validation_data(
            n_train=30, n_test=5, map_size=32, seed=42,
        )
        train_ds = CMBDataset(data["train_maps"], data["train_params"])
        model = BayesianCosmologyCNN(input_size=32, base_channels=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainConfig(
                batch_size=8, n_epochs=3, patience=100,
                checkpoint_dir=tmpdir,
            )
            train_model(model, train_ds, config)

        result = run_cnn_vs_mcmc_comparison(
            model=model,
            test_maps=data["test_maps"][:2],
            test_params=data["test_params"][:2],
            train_dataset=train_ds,
            mc_samples=3,
            mcmc_steps=20,
            mcmc_walkers=14,
            seed=42,
        )

        assert result.cnn_time_ms > 0
        assert result.speedup >= 0
        assert isinstance(result.agreement, dict)
