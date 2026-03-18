"""Tests for Phase 6: Neural Surrogate Models.

Covers emulator, FNO, PINN, and universal training loop.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
import torch.nn.functional as F


# ===================================================================
# Emulator tests
# ===================================================================

class TestClEmulator:
    """Tests for the CMB spectrum emulator."""

    def test_output_shape(self):
        from archeon.ml.emulator import ClEmulator
        model = ClEmulator(n_params=6, n_ell=100, hidden_dim=32, n_blocks=2)
        x = torch.randn(4, 6)
        out = model(x)
        assert out.shape == (4, 100)

    def test_residual_block_preserves_shape(self):
        from archeon.ml.emulator import ResidualMLPBlock
        block = ResidualMLPBlock(64)
        x = torch.randn(8, 64)
        out = block(x)
        assert out.shape == x.shape

    def test_predict_cl_numpy(self):
        from archeon.ml.emulator import ClEmulator
        model = ClEmulator(n_params=6, n_ell=50, hidden_dim=16, n_blocks=1)
        theta = np.random.randn(3, 6)
        cl = model.predict_cl(theta)
        assert cl.shape == (3, 50)
        assert np.all(cl > 0), "C_l should be positive (10^x is always > 0)"

    def test_predict_cl_single_sample(self):
        from archeon.ml.emulator import ClEmulator
        model = ClEmulator(n_params=6, n_ell=30, hidden_dim=16, n_blocks=1)
        theta = np.random.randn(6)
        cl = model.predict_cl(theta)
        assert cl.shape == (1, 30)

    def test_normalization(self):
        from archeon.ml.emulator import compute_normalization
        theta = np.random.randn(100, 6)
        cl = np.random.randn(100, 50)
        norm = compute_normalization(theta, cl)
        theta_n = norm.normalize_theta(theta)
        assert np.abs(theta_n.mean(axis=0)).max() < 0.2
        cl_n = norm.normalize_cl(cl)
        cl_back = norm.denormalize_cl(cl_n)
        np.testing.assert_allclose(cl_back, cl, atol=1e-5)

    def test_train_emulator_runs(self):
        from archeon.ml.emulator import ClEmulator, train_emulator
        model = ClEmulator(n_params=6, n_ell=20, hidden_dim=16, n_blocks=1)
        theta = np.random.randn(80, 6).astype(np.float32)
        cl = np.abs(np.random.randn(80, 20).astype(np.float32)) + 1e-5
        result = train_emulator(model, theta, cl, n_epochs=5, batch_size=16)
        assert len(result["train_losses"]) > 0
        assert result["best_epoch"] >= 0

    def test_benchmark_emulator(self):
        from archeon.ml.emulator import ClEmulator, benchmark_emulator
        model = ClEmulator(n_params=6, n_ell=50, hidden_dim=16, n_blocks=1)
        ms = benchmark_emulator(model, batch_size=10, n_repeats=10)
        assert ms > 0
        assert ms < 100  # should be well under 100ms per sample


class TestGenerateTrainingData:
    """Tests for emulator training data generation."""

    def test_generate_training_data_shapes(self):
        from archeon.ml.emulator import generate_training_data
        theta, cl = generate_training_data(n_samples=10, l_max=100)
        assert theta.shape[0] == 10
        assert theta.shape[1] == 6
        assert cl.shape[0] == 10
        assert cl.shape[1] > 0

    def test_generate_training_data_reproducible(self):
        from archeon.ml.emulator import generate_training_data
        t1, c1 = generate_training_data(n_samples=5, l_max=50, seed=123)
        t2, c2 = generate_training_data(n_samples=5, l_max=50, seed=123)
        np.testing.assert_array_equal(t1, t2)
        np.testing.assert_array_equal(c1, c2)


# ===================================================================
# FNO tests
# ===================================================================

class TestFNO:
    """Tests for the Fourier Neural Operator."""

    def test_spectral_conv_shape(self):
        from archeon.ml.fno_structure import SpectralConv2d
        sc = SpectralConv2d(8, 16, modes1=4, modes2=4)
        x = torch.randn(2, 8, 32, 32)
        out = sc(x)
        assert out.shape == (2, 16, 32, 32)

    def test_fourier_block_shape(self):
        from archeon.ml.fno_structure import FourierBlock
        fb = FourierBlock(width=16, modes1=4, modes2=4)
        x = torch.randn(2, 16, 32, 32)
        out = fb(x)
        assert out.shape == x.shape

    def test_fno_full_forward(self):
        from archeon.ml.fno_structure import FNOStructureFormation
        model = FNOStructureFormation(
            in_channels=1, out_channels=1, width=8, modes=4, n_layers=2)
        x = torch.randn(2, 1, 32, 32)
        out = model(x)
        assert out.shape == (2, 1, 32, 32)

    def test_fno_different_sizes(self):
        from archeon.ml.fno_structure import FNOStructureFormation
        model = FNOStructureFormation(width=8, modes=4, n_layers=2)
        for size in [16, 32, 64]:
            x = torch.randn(1, 1, size, size)
            out = model(x)
            assert out.shape == (1, 1, size, size)

    def test_generate_density_pair(self):
        from archeon.ml.fno_structure import generate_density_pair
        init, evol = generate_density_pair(size=32, n_samples=5, seed=0)
        assert init.shape == (5, 1, 32, 32)
        assert evol.shape == (5, 1, 32, 32)

    def test_density_pairs_normalized(self):
        from archeon.ml.fno_structure import generate_density_pair
        init, evol = generate_density_pair(size=32, n_samples=20, seed=0)
        for i in range(20):
            std_i = init[i, 0].std()
            assert 0.5 < std_i < 2.0, f"Initial field std out of range: {std_i}"

    def test_train_fno_runs(self):
        from archeon.ml.fno_structure import (
            FNOStructureFormation, generate_density_pair, train_fno)
        init, evol = generate_density_pair(size=16, n_samples=20, seed=42)
        model = FNOStructureFormation(width=8, modes=4, n_layers=2)
        result = train_fno(model, init, evol, n_epochs=3, batch_size=8)
        assert len(result["train_losses"]) > 0

    def test_power_spectrum_2d(self):
        from archeon.ml.fno_structure import compute_power_spectrum_2d
        field = np.random.randn(64, 64)
        k, pk = compute_power_spectrum_2d(field)
        assert len(k) == len(pk)
        assert len(k) > 0
        assert np.all(pk >= 0)

    def test_power_spectrum_white_noise(self):
        from archeon.ml.fno_structure import compute_power_spectrum_2d
        rng = np.random.default_rng(42)
        field = rng.standard_normal((128, 128))
        k, pk = compute_power_spectrum_2d(field)
        pk_nonzero = pk[pk > 0]
        if len(pk_nonzero) > 3:
            ratio = pk_nonzero.max() / pk_nonzero.min()
            assert ratio < 20, "White noise P(k) should be roughly flat"


# ===================================================================
# PINN tests
# ===================================================================

class TestPINN:
    """Tests for the Physics-Informed Neural Network."""

    def test_pinn_output_shape(self):
        from archeon.ml.pinn_friedmann import FriedmannPINN
        model = FriedmannPINN(hidden_dim=32, n_layers=2)
        a = torch.rand(10, 1)
        H = model(a)
        assert H.shape == (10, 1)

    def test_pinn_positive_output(self):
        from archeon.ml.pinn_friedmann import FriedmannPINN
        model = FriedmannPINN(hidden_dim=32, n_layers=2)
        a = torch.rand(100, 1)
        H = model(a)
        assert (H > 0).all(), "H(a) should always be positive (softplus)"

    def test_friedmann_h_squared(self):
        from archeon.ml.pinn_friedmann import CosmologyParams, friedmann_H_squared
        params = CosmologyParams()
        a = torch.tensor([[1.0]])
        h2 = friedmann_H_squared(a, params)
        expected = params.H0**2 * (params.Omega_r + params.Omega_m + params.Omega_Lambda)
        assert abs(h2.item() - expected) < 1.0

    def test_friedmann_h_increases_at_early_times(self):
        from archeon.ml.pinn_friedmann import CosmologyParams, friedmann_H_squared
        params = CosmologyParams()
        a_early = torch.tensor([[0.01]])
        a_late = torch.tensor([[1.0]])
        h2_early = friedmann_H_squared(a_early, params)
        h2_late = friedmann_H_squared(a_late, params)
        assert h2_early.item() > h2_late.item()

    def test_physics_residual_runs(self):
        from archeon.ml.pinn_friedmann import (
            FriedmannPINN, CosmologyParams, compute_physics_residual)
        model = FriedmannPINN(hidden_dim=16, n_layers=2)
        params = CosmologyParams()
        a = torch.rand(5, 1)
        residual = compute_physics_residual(model, a, params)
        assert residual.shape == (5, 1)

    def test_derivative_residual_runs(self):
        from archeon.ml.pinn_friedmann import (
            FriedmannPINN, CosmologyParams, compute_derivative_residual)
        model = FriedmannPINN(hidden_dim=16, n_layers=2)
        params = CosmologyParams()
        a = torch.rand(5, 1)
        residual = compute_derivative_residual(model, a, params)
        assert residual.shape == (5, 1)

    def test_pinn_loss_components(self):
        from archeon.ml.pinn_friedmann import (
            FriedmannPINN, CosmologyParams, pinn_loss)
        model = FriedmannPINN(hidden_dim=16, n_layers=2)
        params = CosmologyParams()
        a_data = torch.rand(10, 1)
        h_data = torch.rand(10, 1) * 100
        a_phys = torch.rand(20, 1)
        total, components = pinn_loss(model, a_data, h_data, a_phys, params)
        assert total.item() > 0
        assert "data" in components
        assert "physics" in components
        assert "derivative" in components

    def test_generate_friedmann_data(self):
        from archeon.ml.pinn_friedmann import generate_friedmann_data, CosmologyParams
        params = CosmologyParams()
        a_data, H_data, a_coll = generate_friedmann_data(
            params, n_data=50, n_collocation=100)
        assert a_data.shape == (50, 1)
        assert H_data.shape == (50, 1)
        assert a_coll.shape == (100, 1)
        assert np.all(a_data > 0)
        assert np.all(H_data > 0)

    def test_train_pinn_runs(self):
        from archeon.ml.pinn_friedmann import FriedmannPINN, train_pinn
        model = FriedmannPINN(hidden_dim=16, n_layers=2)
        result = train_pinn(model, n_epochs=20, n_data=30, n_collocation=50)
        assert len(result["history"]) == 20
        assert result["final_mean_rel_error"] >= 0

    def test_evaluate_pinn(self):
        from archeon.ml.pinn_friedmann import FriedmannPINN, evaluate_pinn
        model = FriedmannPINN(hidden_dim=16, n_layers=2)
        result = evaluate_pinn(model, n_test=50)
        assert len(result["a"]) == 50
        assert len(result["H_true"]) == 50
        assert len(result["H_pred"]) == 50
        assert result["mean_rel_error"] >= 0

    def test_predict_numpy(self):
        from archeon.ml.pinn_friedmann import FriedmannPINN
        model = FriedmannPINN(hidden_dim=16, n_layers=2)
        a = np.linspace(0.01, 1.0, 20).astype(np.float32)
        H = model.predict(a)
        assert H.shape == (20,)
        assert np.all(H > 0)


# ===================================================================
# Universal training loop tests
# ===================================================================

class TestUniversalTraining:
    """Tests for the universal training loop."""

    def _make_data(self, n=100, d_in=6, d_out=10):
        rng = np.random.default_rng(42)
        x = rng.standard_normal((n, d_in)).astype(np.float32)
        y = rng.standard_normal((n, d_out)).astype(np.float32)
        return x, y

    def test_make_dataloaders(self):
        from archeon.ml.training import make_dataloaders
        x, y = self._make_data()
        train_dl, val_dl = make_dataloaders(x, y, batch_size=16,
                                            val_fraction=0.2, seed=42)
        n_train = sum(len(b[0]) for b in train_dl)
        n_val = sum(len(b[0]) for b in val_dl)
        assert n_train > 0
        assert n_val > 0
        assert n_train + n_val <= 100

    def test_train_surrogate_basic(self):
        from archeon.ml.training import train_surrogate, SurrogateTrainConfig
        x, y = self._make_data()
        model = torch.nn.Sequential(
            torch.nn.Linear(6, 32),
            torch.nn.ReLU(),
            torch.nn.Linear(32, 10),
        )
        config = SurrogateTrainConfig(n_epochs=5, batch_size=16)
        result = train_surrogate(model, x, y, config)
        assert len(result.train_losses) > 0
        assert result.best_epoch >= 0

    def test_train_surrogate_with_plateau(self):
        from archeon.ml.training import train_surrogate, SurrogateTrainConfig
        x, y = self._make_data()
        model = torch.nn.Linear(6, 10)
        config = SurrogateTrainConfig(n_epochs=5, scheduler="plateau")
        result = train_surrogate(model, x, y, config)
        assert len(result.val_losses) > 0

    def test_train_surrogate_no_scheduler(self):
        from archeon.ml.training import train_surrogate, SurrogateTrainConfig
        x, y = self._make_data()
        model = torch.nn.Linear(6, 10)
        config = SurrogateTrainConfig(n_epochs=3, scheduler="none")
        result = train_surrogate(model, x, y, config)
        assert len(result.train_losses) == 3

    def test_callbacks(self):
        from archeon.ml.training import (
            train_surrogate, SurrogateTrainConfig, LogCallback)
        x, y = self._make_data()
        model = torch.nn.Linear(6, 10)
        log_cb = LogCallback()
        config = SurrogateTrainConfig(n_epochs=3)
        train_surrogate(model, x, y, config, callbacks=[log_cb])
        assert len(log_cb.log) == 3
        assert "epoch" in log_cb.log[0]
        assert "train_loss" in log_cb.log[0]

    def test_custom_loss(self):
        from archeon.ml.training import train_surrogate, SurrogateTrainConfig
        x, y = self._make_data()
        model = torch.nn.Linear(6, 10)
        config = SurrogateTrainConfig(n_epochs=3)
        result = train_surrogate(
            model, x, y, config,
            loss_fn=lambda pred, tgt: F.l1_loss(pred, tgt))
        assert len(result.train_losses) > 0

    def test_relative_error_analysis(self):
        from archeon.ml.training import relative_error_analysis
        model = torch.nn.Linear(6, 10)
        x = np.random.randn(20, 6).astype(np.float32)
        y = np.random.randn(20, 10).astype(np.float32)
        metrics = relative_error_analysis(model, x, y)
        assert "mean_rel_error" in metrics
        assert "max_rel_error" in metrics
        assert "p95_rel_error" in metrics
        assert metrics["mean_rel_error"] >= 0

    def test_compare_models(self):
        from archeon.ml.training import compare_models
        m1 = torch.nn.Linear(6, 10)
        m2 = torch.nn.Linear(6, 10)
        x = np.random.randn(20, 6).astype(np.float32)
        y = np.random.randn(20, 10).astype(np.float32)
        results = compare_models({"m1": m1, "m2": m2}, x, y)
        assert "m1" in results
        assert "m2" in results

    def test_early_stopping(self):
        from archeon.ml.training import train_surrogate, SurrogateTrainConfig
        x, y = self._make_data(n=50)
        model = torch.nn.Linear(6, 10)
        config = SurrogateTrainConfig(
            n_epochs=200, patience=3, scheduler="none", lr=0.0)
        result = train_surrogate(model, x, y, config)
        assert len(result.train_losses) <= 4, (
            "With lr=0 val loss is constant, early stopping should fire at patience+1")

    def test_checkpoint_saving(self, tmp_path):
        from archeon.ml.training import train_surrogate, SurrogateTrainConfig
        x, y = self._make_data(n=50)
        model = torch.nn.Linear(6, 10)
        config = SurrogateTrainConfig(
            n_epochs=3, checkpoint_dir=str(tmp_path / "ckpt"))
        train_surrogate(model, x, y, config)
        assert (tmp_path / "ckpt" / "best_model.pt").exists()
        assert (tmp_path / "ckpt" / "train_result.json").exists()
