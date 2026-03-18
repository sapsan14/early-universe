"""Tests for evaluation metrics module."""

import numpy as np
import pytest
import torch

from archeon.inverse.evaluation import (
    evaluate_predictions,
    compare_cnn_vs_mcmc,
    benchmark_inference,
    PLANCK_2018,
    N_PARAMS,
    PARAM_NAMES,
)
from archeon.inverse.bayesian_cnn import BayesianCosmologyCNN


class TestEvaluatePredictions:

    def test_perfect_predictions(self):
        """Perfect predictions should have near-zero RMSE."""
        rng = np.random.default_rng(42)
        n = 100
        theta = rng.normal(0, 1, (n, N_PARAMS))
        sigma = np.ones_like(theta) * 0.01

        report = evaluate_predictions(theta, sigma, theta)
        assert report.total_rmse < 1e-10
        for pm in report.param_metrics:
            assert pm.rmse < 1e-10
            assert abs(pm.bias) < 1e-10

    def test_noisy_predictions(self):
        rng = np.random.default_rng(42)
        n = 200
        theta = rng.normal(0, 1, (n, N_PARAMS))
        mu = theta + rng.normal(0, 0.1, (n, N_PARAMS))
        sigma = np.ones_like(theta) * 0.1

        report = evaluate_predictions(mu, sigma, theta)
        assert report.total_rmse > 0
        assert report.total_rmse < 1.0

    def test_report_summary(self):
        rng = np.random.default_rng(42)
        n = 50
        theta = rng.normal(0, 1, (n, N_PARAMS))
        sigma = np.ones_like(theta)

        report = evaluate_predictions(theta, sigma, theta)
        summary = report.summary()
        assert "Evaluation Report" in summary
        for name in PARAM_NAMES:
            assert name in summary

    def test_coverage_perfect_uncertainty(self):
        """Well-calibrated uncertainty should give ~expected coverage."""
        rng = np.random.default_rng(42)
        n = 5000
        theta = rng.normal(0, 1, (n, N_PARAMS))
        noise = rng.normal(0, 1, (n, N_PARAMS))
        mu = theta + noise
        sigma = np.ones_like(theta)

        report = evaluate_predictions(mu, sigma, theta)
        assert report.mean_coverage_68 > 0.55
        assert report.mean_coverage_68 < 0.80
        assert report.mean_coverage_95 > 0.85


class TestPlanckValues:

    def test_all_params_present(self):
        for name in PARAM_NAMES:
            assert name in PLANCK_2018

    def test_uncertainties_positive(self):
        for name, (val, err) in PLANCK_2018.items():
            assert err > 0


class TestBenchmark:

    def test_benchmark_returns_positive(self):
        model = BayesianCosmologyCNN(input_size=32, base_channels=4)
        x = torch.randn(4, 1, 32, 32)
        ms = benchmark_inference(model, x, n_repeats=5)
        assert ms > 0


class TestComparisonReport:

    def test_speedup_positive(self):
        rng = np.random.default_rng(42)
        n = 50
        theta = rng.normal(0, 1, (n, N_PARAMS))
        mu = theta + rng.normal(0, 0.1, (n, N_PARAMS))
        sigma = np.ones_like(theta) * 0.1

        report = compare_cnn_vs_mcmc(
            cnn_mu=mu, cnn_sigma=sigma,
            mcmc_means=mu, mcmc_stds=sigma,
            theta_true=theta,
            cnn_time_ms=5.0,
            mcmc_time_ms=50000.0,
        )
        assert report.speedup > 1000
        assert report.cnn_report is not None
        assert report.mcmc_report is not None
