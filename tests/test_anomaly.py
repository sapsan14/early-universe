"""Tests for anomaly detection modules (Phase 5)."""

import numpy as np
import pytest
import torch

from archeon.anomaly.autoencoder import (
    CMBAutoencoder, compute_anomaly_scores, train_autoencoder,
)
from archeon.anomaly.latent_analysis import (
    extract_latent_vectors, detect_outliers, analyze_dimensionality,
    reduce_to_2d, latent_parameter_correlation,
)
from archeon.anomaly.statistical_tests import (
    ks_test_pixels, anderson_darling_test, check_non_gaussianity,
    chi_squared_power_spectrum, monte_carlo_significance,
)
from archeon.anomaly.cold_spot import (
    find_cold_spots, compute_radial_profile, cold_spot_mc_significance,
)


class TestAutoencoder:

    @pytest.fixture
    def model(self):
        return CMBAutoencoder(input_size=32, base_channels=8, latent_dim=16)

    def test_forward_shapes(self, model):
        x = torch.randn(2, 1, 32, 32)
        recon, z = model(x)
        assert recon.shape == x.shape
        assert z.shape == (2, 16)

    def test_encode_decode_roundtrip(self, model):
        x = torch.randn(1, 1, 32, 32)
        z = model.encode(x)
        recon = model.decode(z)
        assert recon.shape[0] == 1

    def test_anomaly_scores(self, model):
        maps = np.random.randn(5, 32, 32).astype(np.float32)
        scores = compute_anomaly_scores(model, maps, threshold_sigma=2.0)
        assert len(scores) == 5
        for s in scores:
            assert s.global_score >= 0
            assert s.pixel_scores.shape == (32, 32)
            assert 0 <= s.anomalous_fraction <= 1

    def test_train_loss_decreases(self):
        model = CMBAutoencoder(input_size=32, base_channels=4, latent_dim=8)
        maps = np.random.randn(40, 32, 32).astype(np.float32)
        losses = train_autoencoder(model, maps, n_epochs=5, batch_size=8, lr=1e-3)
        assert len(losses) == 5
        assert losses[-1] < losses[0]


class TestLatentAnalysis:

    @pytest.fixture
    def model_and_data(self):
        model = CMBAutoencoder(input_size=32, base_channels=4, latent_dim=8)
        maps = np.random.randn(20, 32, 32).astype(np.float32)
        return model, maps

    def test_extract_latent(self, model_and_data):
        model, maps = model_and_data
        z = extract_latent_vectors(model, maps)
        assert z.shape == (20, 8)

    def test_outlier_detection(self):
        rng = np.random.default_rng(42)
        train = rng.standard_normal((100, 8))
        test_normal = rng.standard_normal((10, 8))
        test_outlier = rng.standard_normal((5, 8)) + 10.0
        test = np.vstack([test_normal, test_outlier])
        result = detect_outliers(train, test, threshold_sigma=2.5)
        assert result.distances.shape == (15,)
        assert result.n_outliers >= 1

    def test_dimensionality(self):
        rng = np.random.default_rng(42)
        z = rng.standard_normal((50, 16))
        z[:, :3] *= 10  # first 3 dims have most variance
        result = analyze_dimensionality(z)
        assert result.effective_dim <= 16
        assert result.effective_dim >= 1
        assert len(result.explained_variance_ratio) == 16

    def test_reduce_pca(self):
        z = np.random.randn(30, 8)
        proj = reduce_to_2d(z, method="pca")
        assert proj.shape == (30, 2)

    def test_parameter_correlation(self):
        rng = np.random.default_rng(42)
        z = rng.standard_normal((50, 8))
        params = rng.standard_normal((50, 3))
        result = latent_parameter_correlation(z, params)
        assert result["correlation_matrix"].shape == (8, 3)
        assert len(result["max_corr_per_param"]) == 3


class TestStatisticalTests:

    def test_ks_same_distribution(self):
        rng = np.random.default_rng(42)
        a = rng.standard_normal((64, 64))
        b = rng.standard_normal((64, 64))
        result = ks_test_pixels(a, b)
        assert not result.significant  # same distribution

    def test_ks_different_distribution(self):
        rng = np.random.default_rng(42)
        a = rng.standard_normal((64, 64))
        b = rng.standard_normal((64, 64)) + 5.0
        result = ks_test_pixels(a, b)
        assert result.significant

    def test_anderson_darling_gaussian(self):
        rng = np.random.default_rng(42)
        m = rng.standard_normal((100, 100))
        result = anderson_darling_test(m)
        assert result.test_name == "Anderson-Darling (Gaussianity)"

    def test_non_gaussianity_gaussian(self):
        rng = np.random.default_rng(42)
        m = rng.standard_normal((100, 100))
        result = check_non_gaussianity(m)
        assert abs(result.skewness) < 0.5
        assert abs(result.kurtosis) < 0.5

    def test_chi_squared_consistent(self):
        rng = np.random.default_rng(42)
        cl = np.abs(rng.standard_normal(100)) + 0.1
        result = chi_squared_power_spectrum(cl, cl)
        assert result.chi_squared < 1e-10

    def test_monte_carlo_extreme(self):
        sims = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = monte_carlo_significance(100.0, sims)
        assert result.p_value < 0.5

    def test_monte_carlo_typical(self):
        sims = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = monte_carlo_significance(3.0, sims)
        assert result.p_value > 0.3


class TestColdSpot:

    def test_find_cold_spots_with_injected(self):
        """Inject a cold region and verify detection."""
        rng = np.random.default_rng(42)
        m = rng.standard_normal((128, 128))
        # Inject cold spot at (64, 64)
        y, x = np.ogrid[:128, :128]
        r = np.sqrt((x - 64)**2 + (y - 64)**2)
        m[r < 10] -= 5.0

        result = find_cold_spots(m, threshold_sigma=2.5, min_radius=2)
        assert result.n_candidates >= 1
        assert result.coldest_spot is not None
        # Coldest spot should be near (64, 64)
        cs = result.coldest_spot
        assert abs(cs.center_x - 64) < 15
        assert abs(cs.center_y - 64) < 15

    def test_no_cold_spots_in_uniform(self):
        m = np.zeros((64, 64))
        result = find_cold_spots(m, threshold_sigma=3.0)
        assert result.n_candidates == 0

    def test_radial_profile(self):
        rng = np.random.default_rng(42)
        m = rng.standard_normal((64, 64))
        profile = compute_radial_profile(m, center=(32, 32), max_radius=20)
        assert len(profile.radii) == 20
        assert len(profile.temperatures) == 20

    def test_mc_significance(self):
        rng = np.random.default_rng(42)
        sims = rng.standard_normal((20, 32, 32))
        result = cold_spot_mc_significance(-10.0, sims)
        assert "p_value" in result
        assert result["n_simulations"] == 20
        assert 0 < result["p_value"] <= 1
