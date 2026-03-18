"""Tests for uncertainty calibration module."""

import numpy as np
import pytest
import torch

from archeon.inverse.bayesian_cnn import BayesianCosmologyCNN, N_PARAMS
from archeon.inverse.uncertainty import (
    mc_dropout_predict,
    DeepEnsemble,
    expected_calibration_error,
    coverage_probability,
    calibrate_uncertainties,
    temperature_scale,
)


class TestMCDropout:

    @pytest.fixture
    def model(self):
        return BayesianCosmologyCNN(input_size=32, base_channels=8)

    def test_output_shapes(self, model):
        x = torch.randn(2, 1, 32, 32)
        result = mc_dropout_predict(model, x, n_samples=10)
        assert result.mu_mean.shape == (2, N_PARAMS)
        assert result.mu_std.shape == (2, N_PARAMS)
        assert result.total_std.shape == (2, N_PARAMS)
        assert result.all_mus.shape == (10, 2, N_PARAMS)

    def test_epistemic_nonzero(self, model):
        x = torch.randn(2, 1, 32, 32)
        result = mc_dropout_predict(model, x, n_samples=30)
        assert result.epistemic.sum() > 0

    def test_total_geq_components(self, model):
        """Total variance should be >= each component."""
        x = torch.randn(1, 1, 32, 32)
        result = mc_dropout_predict(model, x, n_samples=20)
        total = result.epistemic + result.aleatoric
        assert np.allclose(result.total_std**2, total, atol=1e-5)


class TestDeepEnsemble:

    def test_predict_shape(self):
        ensemble = DeepEnsemble(n_members=3, input_size=32, base_channels=4)
        x = torch.randn(2, 1, 32, 32)
        result = ensemble.predict(x)
        assert result.mu_mean.shape == (2, N_PARAMS)
        assert result.member_mus.shape == (3, 2, N_PARAMS)

    def test_members_differ(self):
        """Different random init should produce different predictions."""
        ensemble = DeepEnsemble(n_members=3, input_size=32, base_channels=4)
        x = torch.randn(1, 1, 32, 32)
        result = ensemble.predict(x)
        assert result.epistemic.sum() > 0


class TestCalibrationMetrics:

    def test_perfect_calibration(self):
        """If sigma perfectly describes noise, ECE should be small."""
        rng = np.random.default_rng(42)
        n = 5000
        mu = rng.normal(0, 1, (n, 3))
        sigma = np.ones((n, 3))
        theta_true = mu + rng.normal(0, 1, (n, 3))

        ece = expected_calibration_error(mu, sigma, theta_true)
        assert ece < 0.05

    def test_overconfident_high_ece(self):
        """Too-small sigma should give high ECE."""
        rng = np.random.default_rng(42)
        n = 2000
        mu = rng.normal(0, 1, (n, 3))
        sigma = np.ones((n, 3)) * 0.01
        theta_true = mu + rng.normal(0, 1, (n, 3))

        ece = expected_calibration_error(mu, sigma, theta_true)
        assert ece > 0.3

    def test_coverage_probability_shape(self):
        rng = np.random.default_rng(42)
        n = 500
        mu = rng.normal(0, 1, (n, 2))
        sigma = np.ones((n, 2))
        theta = mu + rng.normal(0, 1, (n, 2))

        cov = coverage_probability(mu, sigma, theta, levels=[0.5, 0.95])
        assert 0.5 in cov
        assert 0.95 in cov
        assert 0 <= cov[0.5] <= 1
        assert 0 <= cov[0.95] <= 1

    def test_coverage_monotonic(self):
        """Higher confidence should give higher coverage."""
        rng = np.random.default_rng(42)
        n = 2000
        mu = rng.normal(0, 1, (n, 2))
        sigma = np.ones((n, 2))
        theta = mu + rng.normal(0, 1, (n, 2))

        cov = coverage_probability(mu, sigma, theta, levels=[0.5, 0.68, 0.95])
        assert cov[0.5] <= cov[0.68] + 0.05
        assert cov[0.68] <= cov[0.95] + 0.05


class TestTemperatureScaling:

    def test_overconfident_T_gt_1(self):
        """Overconfident model should need T > 1."""
        rng = np.random.default_rng(42)
        n = 1000
        mu = rng.normal(0, 1, (n, 3))
        sigma = np.ones((n, 3)) * 0.1
        theta = mu + rng.normal(0, 1, (n, 3))

        T = temperature_scale(mu, sigma, theta)
        assert T > 1.0

    def test_well_calibrated_T_near_1(self):
        rng = np.random.default_rng(42)
        n = 3000
        mu = rng.normal(0, 1, (n, 3))
        sigma = np.ones((n, 3))
        theta = mu + rng.normal(0, 1, (n, 3))

        T = temperature_scale(mu, sigma, theta)
        assert 0.8 < T < 1.2


class TestCalibrationReport:

    def test_calibrate_returns_metrics(self):
        rng = np.random.default_rng(42)
        n = 500
        mu = rng.normal(0, 1, (n, 3))
        sigma = np.ones((n, 3))
        theta = mu + rng.normal(0, 1, (n, 3))

        result = calibrate_uncertainties(mu, sigma, theta)
        assert result.ece >= 0
        assert isinstance(result.coverage, dict)
        assert len(result.sharpness) == 3
        assert isinstance(result.details, str)
