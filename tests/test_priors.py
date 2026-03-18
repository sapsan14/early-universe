"""Tests for prior distributions."""

import numpy as np
import pytest

from archeon.data.priors import (
    LCDM_PRIORS,
    compute_derived,
    generate_parameter_sets,
    latin_hypercube_sample,
    sample_gaussian,
    sample_uniform,
)


class TestUniformSampling:
    def test_within_bounds(self):
        """All samples must be within prior ranges."""
        samples = sample_uniform(1000, seed=42)
        for name, pr in LCDM_PRIORS.items():
            assert np.all(samples[name] >= pr.min)
            assert np.all(samples[name] <= pr.max)

    def test_shape(self):
        """Should return n_samples values per parameter."""
        samples = sample_uniform(500, seed=42)
        for name in LCDM_PRIORS:
            assert samples[name].shape == (500,)

    def test_reproducible(self):
        """Same seed -> same samples."""
        s1 = sample_uniform(100, seed=99)
        s2 = sample_uniform(100, seed=99)
        for name in LCDM_PRIORS:
            np.testing.assert_array_equal(s1[name], s2[name])


class TestGaussianSampling:
    def test_within_bounds(self):
        """All samples must be clipped to prior ranges."""
        samples = sample_gaussian(1000, seed=42)
        for name, pr in LCDM_PRIORS.items():
            assert np.all(samples[name] >= pr.min)
            assert np.all(samples[name] <= pr.max)

    def test_centered_near_fiducial(self):
        """Mean should be near fiducial value."""
        samples = sample_gaussian(5000, seed=42)
        for name, pr in LCDM_PRIORS.items():
            mean = np.mean(samples[name])
            span = pr.max - pr.min
            assert abs(mean - pr.fiducial) < 0.2 * span, \
                f"{name}: mean={mean}, fiducial={pr.fiducial}"


class TestLatinHypercube:
    def test_within_bounds(self):
        samples = latin_hypercube_sample(200, seed=42)
        for name, pr in LCDM_PRIORS.items():
            assert np.all(samples[name] >= pr.min)
            assert np.all(samples[name] <= pr.max)

    def test_better_coverage(self):
        """LHS should have lower discrepancy than random sampling."""
        n = 100
        lhs = latin_hypercube_sample(n, seed=42)
        uniform = sample_uniform(n, seed=42)

        for name, pr in LCDM_PRIORS.items():
            lhs_norm = (lhs[name] - pr.min) / (pr.max - pr.min)
            uni_norm = (uniform[name] - pr.min) / (pr.max - pr.min)

            # LHS marginals should be closer to uniform
            lhs_sorted = np.sort(lhs_norm)
            expected = np.linspace(0, 1, n)
            lhs_max_gap = np.max(np.abs(lhs_sorted - expected))
            assert lhs_max_gap < 0.15, f"{name}: LHS max gap = {lhs_max_gap}"


class TestDerivedParams:
    def test_flat_universe(self):
        """Omega_m + Omega_Lambda + Omega_r ~ 1 (flat universe)."""
        base = sample_uniform(100, seed=42)
        derived = compute_derived(base)
        total = derived["Omega_m"] + derived["Omega_Lambda"] + derived["Omega_r"]
        np.testing.assert_allclose(total, 1.0, atol=1e-4)

    def test_A_s_from_ln10As(self):
        """A_s should be derived correctly from ln(10^10 A_s)."""
        base = {"H0": np.array([67.36]), "Omega_b_h2": np.array([0.02237]),
                "Omega_cdm_h2": np.array([0.12]), "n_s": np.array([0.9649]),
                "ln10As": np.array([3.044]), "tau_reio": np.array([0.0544])}
        derived = compute_derived(base)
        expected = np.exp(3.044) * 1e-10
        np.testing.assert_allclose(derived["A_s"], expected, rtol=1e-10)


class TestGenerateParameterSets:
    def test_all_methods(self):
        for method in ["uniform", "gaussian", "lhs"]:
            params = generate_parameter_sets(50, method=method, seed=42)
            assert "H0" in params
            assert "Omega_m" in params
            assert "A_s" in params
