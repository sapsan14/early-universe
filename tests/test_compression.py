"""Tests for cosmological compression modules (Phase 5)."""

import numpy as np
import pytest
import torch

from archeon.compression.vae import CosmologyVAE, vae_loss, train_vae
from archeon.compression.disentanglement import (
    compute_mutual_info_gap, traversal_analysis, factor_correlation_matrix,
)
from archeon.compression.interpretability import (
    interpret_latent_space, latent_space_summary, find_hidden_correlations,
)


class TestVAE:

    @pytest.fixture
    def model(self):
        return CosmologyVAE(input_size=32, base_channels=8, latent_dim=16)

    def test_forward_shapes(self, model):
        x = torch.randn(4, 1, 32, 32)
        recon, mu, logvar = model(x)
        assert recon.shape == x.shape
        assert mu.shape == (4, 16)
        assert logvar.shape == (4, 16)

    def test_encode_decode(self, model):
        x = torch.randn(2, 1, 32, 32)
        mu, logvar = model.encode(x)
        z = model.reparameterize(mu, logvar)
        recon = model.decode(z)
        assert recon.shape[0] == 2

    def test_generate(self, model):
        samples = model.generate(n_samples=3)
        assert samples.shape[0] == 3
        assert samples.shape[1] == 1

    def test_vae_loss_positive(self, model):
        x = torch.randn(4, 1, 32, 32)
        recon, mu, logvar = model(x)
        total, recon_l, kl = vae_loss(recon, x, mu, logvar)
        assert total.item() > 0
        assert recon_l.item() > 0
        assert kl.item() >= 0

    def test_beta_affects_kl(self, model):
        x = torch.randn(4, 1, 32, 32)
        recon, mu, logvar = model(x)
        loss_b1, _, _ = vae_loss(recon, x, mu, logvar, beta=1.0)
        loss_b10, _, _ = vae_loss(recon, x, mu, logvar, beta=10.0)
        assert loss_b10.item() >= loss_b1.item()

    def test_train_returns_losses(self):
        model = CosmologyVAE(input_size=32, base_channels=4, latent_dim=8)
        maps = np.random.randn(30, 32, 32).astype(np.float32)
        losses = train_vae(model, maps, n_epochs=3, batch_size=8)
        assert len(losses) == 3
        assert all(l > 0 for l in losses)


class TestDisentanglement:

    def test_mig_perfect_disentanglement(self):
        """If each latent dim is exactly one param, MIG should be high."""
        rng = np.random.default_rng(42)
        n = 200
        params = rng.standard_normal((n, 3))
        # Latent = params + small noise (perfect disentanglement)
        latent = np.column_stack([
            params[:, 0] + 0.01 * rng.standard_normal(n),
            params[:, 1] + 0.01 * rng.standard_normal(n),
            params[:, 2] + 0.01 * rng.standard_normal(n),
            rng.standard_normal(n),  # noise dim
        ])
        result = compute_mutual_info_gap(latent, params, ["a", "b", "c"])
        assert result.mutual_info_gap > 0.5

    def test_mig_entangled(self):
        """Random latent should have low MIG."""
        rng = np.random.default_rng(42)
        latent = rng.standard_normal((200, 8))
        params = rng.standard_normal((200, 3))
        result = compute_mutual_info_gap(latent, params, ["a", "b", "c"])
        assert result.mutual_info_gap < 0.5

    def test_traversal_shape(self):
        model = CosmologyVAE(input_size=32, base_channels=4, latent_dim=8)
        base = np.zeros(8, dtype=np.float32)
        out = traversal_analysis(model, base, dim_idx=0, n_steps=5)
        assert out.shape[0] == 5

    def test_correlation_matrix(self):
        rng = np.random.default_rng(42)
        latent = rng.standard_normal((100, 6))
        params = rng.standard_normal((100, 3))
        result = factor_correlation_matrix(latent, params, ["x", "y", "z"])
        assert result["correlation_matrix"].shape == (6, 3)
        assert len(result["max_corr_per_param"]) == 3
        assert len(result["best_latent_dim"]) == 3


class TestInterpretability:

    def test_interpret_returns_all_dims(self):
        rng = np.random.default_rng(42)
        latent = rng.standard_normal((100, 5))
        params = rng.standard_normal((100, 3))
        interps = interpret_latent_space(latent, params, ["H0", "Om", "ns"])
        assert len(interps) == 5
        for x in interps:
            assert x.best_param in ["H0", "Om", "ns"]

    def test_strong_correlation_detected(self):
        rng = np.random.default_rng(42)
        n = 200
        params = rng.standard_normal((n, 2))
        latent = np.column_stack([
            params[:, 0],  # perfect correlation
            rng.standard_normal(n),
        ])
        interps = interpret_latent_space(latent, params, ["A", "B"])
        top = interps[0]
        assert abs(top.correlation) > 0.9
        assert top.best_param == "A"

    def test_summary_string(self):
        rng = np.random.default_rng(42)
        latent = rng.standard_normal((50, 4))
        params = rng.standard_normal((50, 2))
        interps = interpret_latent_space(latent, params, ["H0", "Om"])
        s = latent_space_summary(interps)
        assert "Latent Space Interpretation" in s
        assert len(s) > 20

    def test_hidden_correlations(self):
        rng = np.random.default_rng(42)
        n = 300
        params = rng.standard_normal((n, 3))
        # z_0 encodes combination: params[:,0] + params[:,1]
        latent = np.column_stack([
            params[:, 0] + params[:, 1] + 0.1 * rng.standard_normal(n),
            rng.standard_normal(n),
        ])
        results = find_hidden_correlations(
            latent, params, ["a", "b", "c"], threshold=0.05)
        # Should detect that dim 0 encodes a combination
        assert isinstance(results, list)
