"""Tests for synthetic CMB data generation."""

import numpy as np
import pytest

from archeon.data.synthetic import (
    compute_cl_internal,
    generate_cmb_map,
    generate_dataset,
    save_dataset,
    load_dataset,
    SyntheticDataset,
)


FIDUCIAL_THETA = {
    "H0": 67.36, "h": 0.6736,
    "Omega_m": 0.3153, "Omega_b": 0.0493,
    "Omega_Lambda": 0.6847, "Omega_r": 9.14e-5,
    "A_s": 2.1e-9, "n_s": 0.9649,
}


class TestComputeCl:
    def test_shape(self):
        """C_l should have lmax+1 elements."""
        cl = compute_cl_internal(FIDUCIAL_THETA, lmax=500)
        assert cl.shape == (501,)

    def test_cl0_cl1_zero(self):
        """C_0 and C_1 should be zero (monopole/dipole not physical)."""
        cl = compute_cl_internal(FIDUCIAL_THETA, lmax=500)
        assert cl[0] == 0.0
        assert cl[1] == 0.0

    def test_cl_positive(self):
        """C_l should be non-negative for l >= 2."""
        cl = compute_cl_internal(FIDUCIAL_THETA, lmax=500)
        assert np.all(cl[2:] >= 0)

    def test_different_params_different_cl(self):
        """Different parameters should give different spectra."""
        theta1 = {**FIDUCIAL_THETA, "Omega_m": 0.25}
        theta2 = {**FIDUCIAL_THETA, "Omega_m": 0.40}
        cl1 = compute_cl_internal(theta1, lmax=200)
        cl2 = compute_cl_internal(theta2, lmax=200)
        # Relative differences should be >1% somewhere
        rel_diff = np.max(np.abs(cl1[2:] - cl2[2:]) / (cl1[2:] + 1e-30))
        assert rel_diff > 0.01, f"Max relative diff = {rel_diff}"


class TestGenerateMap:
    def test_shape(self):
        """Map should have 12*nside^2 pixels."""
        cl = compute_cl_internal(FIDUCIAL_THETA, lmax=192)
        cmb_map = generate_cmb_map(cl, nside=64, seed=42)
        assert cmb_map.shape == (12 * 64**2,)

    def test_reproducible(self):
        """Same seed -> same map."""
        cl = compute_cl_internal(FIDUCIAL_THETA, lmax=192)
        m1 = generate_cmb_map(cl, nside=64, seed=42)
        m2 = generate_cmb_map(cl, nside=64, seed=42)
        np.testing.assert_array_equal(m1, m2)

    def test_zero_mean(self):
        """CMB maps should have approximately zero mean."""
        cl = compute_cl_internal(FIDUCIAL_THETA, lmax=192)
        cmb_map = generate_cmb_map(cl, nside=64, seed=42)
        assert abs(np.mean(cmb_map)) < 0.1 * np.std(cmb_map)

    def test_noise_adds_variance(self):
        """Adding noise should increase total variance."""
        cl = compute_cl_internal(FIDUCIAL_THETA, lmax=192)
        clean = generate_cmb_map(cl, nside=64, seed=42, add_noise=False)
        noisy = generate_cmb_map(cl, nside=64, seed=42, add_noise=True,
                                  noise_level_uK=100.0)
        assert np.var(noisy) > np.var(clean)


class TestDataset:
    def test_small_dataset(self):
        """Generate a tiny dataset end-to-end."""
        ds = generate_dataset(n_samples=5, nside=16, lmax=47,
                              method="uniform", seed=42, verbose=False)
        assert ds.maps.shape == (5, 12 * 16**2)
        assert ds.cl_spectra.shape[0] == 5
        assert len(ds.parameters["H0"]) == 5

    def test_save_load(self, tmp_path):
        """Save and reload should preserve data."""
        ds = generate_dataset(n_samples=3, nside=16, lmax=47,
                              method="lhs", seed=42, verbose=False)
        path = tmp_path / "test_dataset.h5"
        save_dataset(ds, path)
        loaded = load_dataset(path)

        assert loaded.maps.shape == ds.maps.shape
        assert loaded.nside == ds.nside
        np.testing.assert_allclose(loaded.maps, ds.maps, rtol=1e-5)
        np.testing.assert_allclose(
            loaded.parameters["H0"], ds.parameters["H0"])
