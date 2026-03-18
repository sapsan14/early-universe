"""Tests for MCMC baseline module."""

import numpy as np
import pytest

from archeon.inverse.mcmc_baseline import (
    log_prior,
    params_to_cosmology,
    PARAM_NAMES,
    PARAM_RANGES,
    N_PARAMS,
)


class TestLogPrior:

    def test_inside_bounds(self):
        theta = np.array([67.36, 0.02237, 0.120, 0.965, 3.044, 0.054])
        assert log_prior(theta) == 0.0

    def test_outside_bounds_H0(self):
        theta = np.array([50.0, 0.02237, 0.120, 0.965, 3.044, 0.054])
        assert log_prior(theta) == -np.inf

    def test_outside_bounds_tau(self):
        theta = np.array([67.36, 0.02237, 0.120, 0.965, 3.044, 0.5])
        assert log_prior(theta) == -np.inf

    def test_boundary_values(self):
        theta = np.array([60.0, 0.019, 0.10, 0.92, 2.5, 0.01])
        assert np.isfinite(log_prior(theta))


class TestParamsToCosmology:

    def test_returns_dict(self):
        theta = np.array([67.36, 0.02237, 0.120, 0.965, 3.044, 0.054])
        cosmo = params_to_cosmology(theta)
        assert isinstance(cosmo, dict)

    def test_H0_preserved(self):
        theta = np.array([67.36, 0.02237, 0.120, 0.965, 3.044, 0.054])
        cosmo = params_to_cosmology(theta)
        assert cosmo["H0"] == 67.36

    def test_omega_m_consistent(self):
        theta = np.array([67.36, 0.02237, 0.120, 0.965, 3.044, 0.054])
        cosmo = params_to_cosmology(theta)
        h2 = (67.36 / 100) ** 2
        expected = (0.02237 + 0.120) / h2
        assert abs(cosmo["Omega_m"] - expected) < 1e-10

    def test_flatness(self):
        """Omega_m + Omega_r + Omega_Lambda should be ~1."""
        theta = np.array([67.36, 0.02237, 0.120, 0.965, 3.044, 0.054])
        cosmo = params_to_cosmology(theta)
        total = cosmo["Omega_m"] + cosmo["Omega_r"] + cosmo["Omega_Lambda"]
        assert abs(total - 1.0) < 0.01

    def test_A_s_conversion(self):
        theta = np.array([67.36, 0.02237, 0.120, 0.965, 3.044, 0.054])
        cosmo = params_to_cosmology(theta)
        expected = np.exp(3.044) * 1e-10
        assert abs(cosmo["A_s"] - expected) / expected < 1e-10


class TestParamRanges:

    def test_all_params_have_ranges(self):
        for name in PARAM_NAMES:
            assert name in PARAM_RANGES

    def test_ranges_ordered(self):
        for name, (lo, hi) in PARAM_RANGES.items():
            assert lo < hi, f"{name}: {lo} >= {hi}"
