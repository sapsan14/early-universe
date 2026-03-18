"""Tests for the Bayesian CNN architecture."""

import numpy as np
import pytest
import torch

from archeon.inverse.bayesian_cnn import (
    BayesianCosmologyCNN,
    CosmologyMLP,
    HeteroscedasticGaussianNLL,
    N_PARAMS,
    ResidualBlock,
    DownBlock,
)


class TestResidualBlock:

    def test_output_shape_preserved(self):
        block = ResidualBlock(channels=16)
        x = torch.randn(2, 16, 32, 32)
        out = block(x)
        assert out.shape == x.shape

    def test_nonzero_output(self):
        block = ResidualBlock(channels=8)
        x = torch.randn(1, 8, 16, 16)
        out = block(x)
        assert out.abs().sum() > 0


class TestDownBlock:

    def test_spatial_halving(self):
        block = DownBlock(in_ch=8, out_ch=16)
        x = torch.randn(2, 8, 64, 64)
        out = block(x)
        assert out.shape == (2, 16, 32, 32)


class TestBayesianCNN:

    @pytest.fixture
    def model(self):
        return BayesianCosmologyCNN(input_size=64, base_channels=8)

    def test_output_shapes(self, model):
        x = torch.randn(4, 1, 64, 64)
        mu, log_sigma = model(x)
        assert mu.shape == (4, N_PARAMS)
        assert log_sigma.shape == (4, N_PARAMS)

    def test_different_inputs_different_outputs(self, model):
        model.eval()
        x1 = torch.randn(1, 1, 64, 64)
        x2 = torch.randn(1, 1, 64, 64) * 10
        mu1, _ = model(x1)
        mu2, _ = model(x2)
        assert not torch.allclose(mu1, mu2, atol=1e-4)

    def test_log_sigma_clamped(self, model):
        x = torch.randn(2, 1, 64, 64)
        _, log_sigma = model(x)
        assert (log_sigma >= -10.0).all()
        assert (log_sigma <= 5.0).all()

    def test_mc_dropout_varies(self, model):
        """MC Dropout should produce varying predictions."""
        x = torch.randn(1, 1, 64, 64)
        result = model.predict_with_uncertainty(x, n_samples=20)
        assert result["epistemic_var"].sum() > 0

    def test_mc_dropout_keys(self, model):
        x = torch.randn(1, 1, 64, 64)
        result = model.predict_with_uncertainty(x, n_samples=5)
        expected_keys = {"mu", "epistemic_var", "aleatoric_var", "total_var", "sigma"}
        assert set(result.keys()) == expected_keys

    def test_batch_independence(self, model):
        """Predictions should not depend on batch composition."""
        model.eval()
        x = torch.randn(3, 1, 64, 64)
        mu_batch, _ = model(x)
        mu_single, _ = model(x[1:2])
        assert torch.allclose(mu_batch[1], mu_single[0], atol=1e-5)

    def test_input_size_128(self):
        model = BayesianCosmologyCNN(input_size=128, base_channels=8)
        x = torch.randn(1, 1, 128, 128)
        mu, log_sigma = model(x)
        assert mu.shape == (1, N_PARAMS)


class TestHeteroscedasticLoss:

    def test_loss_positive(self):
        criterion = HeteroscedasticGaussianNLL()
        mu = torch.randn(8, N_PARAMS)
        log_sigma = torch.zeros(8, N_PARAMS)
        target = torch.randn(8, N_PARAMS)
        loss = criterion(mu, log_sigma, target)
        assert loss.item() > 0

    def test_loss_decreases_with_accuracy(self):
        """Loss should be lower when predictions are closer to truth."""
        criterion = HeteroscedasticGaussianNLL()
        target = torch.randn(16, N_PARAMS)
        log_sigma = torch.zeros(16, N_PARAMS)

        loss_good = criterion(target + 0.01 * torch.randn_like(target), log_sigma, target)
        loss_bad = criterion(target + 5.0 * torch.randn_like(target), log_sigma, target)
        assert loss_good < loss_bad

    def test_loss_penalizes_overconfidence(self):
        """High confidence (small sigma) on wrong prediction is heavily penalized."""
        criterion = HeteroscedasticGaussianNLL()
        target = torch.zeros(8, N_PARAMS)
        mu = torch.ones(8, N_PARAMS)  # wrong

        loss_uncertain = criterion(mu, torch.ones(8, N_PARAMS), target)   # large sigma
        loss_confident = criterion(mu, -3 * torch.ones(8, N_PARAMS), target)  # small sigma
        assert loss_confident > loss_uncertain

    def test_gradient_flows(self):
        criterion = HeteroscedasticGaussianNLL()
        mu = torch.randn(4, N_PARAMS, requires_grad=True)
        log_sigma = torch.randn(4, N_PARAMS, requires_grad=True)
        target = torch.randn(4, N_PARAMS)
        loss = criterion(mu, log_sigma, target)
        loss.backward()
        assert mu.grad is not None
        assert log_sigma.grad is not None


class TestCosmologyMLP:

    def test_output_shape(self):
        model = CosmologyMLP(input_dim=100)
        x = torch.randn(8, 100)
        mu, log_sigma = model(x)
        assert mu.shape == (8, N_PARAMS)
        assert log_sigma.shape == (8, N_PARAMS)
