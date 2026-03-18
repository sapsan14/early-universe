"""Tests for the training module."""

import numpy as np
import pytest
import torch
import tempfile
import os

from archeon.inverse.bayesian_cnn import BayesianCosmologyCNN, N_PARAMS
from archeon.inverse.training import (
    CMBDataset,
    TrainConfig,
    train_model,
    load_best_model,
)


class TestCMBDataset:

    def test_length(self):
        maps = np.random.randn(20, 32, 32).astype(np.float32)
        params = np.random.randn(20, N_PARAMS).astype(np.float32)
        ds = CMBDataset(maps, params)
        assert len(ds) == 20

    def test_getitem_shapes(self):
        maps = np.random.randn(10, 32, 32).astype(np.float32)
        params = np.random.randn(10, N_PARAMS).astype(np.float32)
        ds = CMBDataset(maps, params)
        x, y = ds[0]
        assert x.shape == (1, 32, 32)
        assert y.shape == (N_PARAMS,)

    def test_normalization(self):
        maps = np.random.randn(50, 16, 16).astype(np.float32) * 100 + 50
        params = np.random.randn(50, N_PARAMS).astype(np.float32) * 10 + 5
        ds = CMBDataset(maps, params, normalize_maps=True, normalize_params=True)
        assert abs(ds.maps.mean()) < 0.5
        assert abs(ds.params.mean()) < 0.5

    def test_denormalize_roundtrip(self):
        params_orig = np.random.randn(20, N_PARAMS).astype(np.float32)
        maps = np.random.randn(20, 16, 16).astype(np.float32)
        ds = CMBDataset(maps, params_orig.copy())
        recovered = ds.denormalize_params(ds.params)
        np.testing.assert_allclose(recovered, params_orig, rtol=1e-4)

    def test_1d_map_reshaped(self):
        maps = np.random.randn(5, 1024).astype(np.float32)
        params = np.random.randn(5, N_PARAMS).astype(np.float32)
        ds = CMBDataset(maps, params)
        x, _ = ds[0]
        assert x.shape == (1, 32, 32)


class TestTraining:

    def test_short_training_runs(self):
        """Verify training loop completes without errors."""
        maps = np.random.randn(40, 32, 32).astype(np.float32)
        params = np.random.randn(40, N_PARAMS).astype(np.float32)
        ds = CMBDataset(maps, params)

        model = BayesianCosmologyCNN(input_size=32, base_channels=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainConfig(
                batch_size=8,
                n_epochs=3,
                patience=100,
                checkpoint_dir=tmpdir,
            )
            history = train_model(model, ds, config)

            assert len(history.train_losses) == 3
            assert len(history.val_losses) == 3
            assert history.total_time_s > 0

    def test_loss_decreases(self):
        """Loss should generally decrease over training."""
        np.random.seed(42)
        n = 100
        params = np.random.randn(n, N_PARAMS).astype(np.float32)
        maps = np.random.randn(n, 32, 32).astype(np.float32)
        ds = CMBDataset(maps, params)

        model = BayesianCosmologyCNN(input_size=32, base_channels=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainConfig(
                batch_size=16,
                n_epochs=10,
                patience=100,
                learning_rate=1e-3,
                checkpoint_dir=tmpdir,
            )
            history = train_model(model, ds, config)
            assert history.train_losses[-1] < history.train_losses[0]

    def test_checkpoint_saved(self):
        maps = np.random.randn(30, 32, 32).astype(np.float32)
        params = np.random.randn(30, N_PARAMS).astype(np.float32)
        ds = CMBDataset(maps, params)

        model = BayesianCosmologyCNN(input_size=32, base_channels=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainConfig(
                batch_size=8,
                n_epochs=2,
                patience=100,
                checkpoint_dir=tmpdir,
            )
            train_model(model, ds, config)
            assert os.path.exists(os.path.join(tmpdir, "best_model.pt"))
            assert os.path.exists(os.path.join(tmpdir, "history.json"))

    def test_load_best_model(self):
        maps = np.random.randn(30, 32, 32).astype(np.float32)
        params = np.random.randn(30, N_PARAMS).astype(np.float32)
        ds = CMBDataset(maps, params)

        model = BayesianCosmologyCNN(input_size=32, base_channels=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            config = TrainConfig(
                batch_size=8,
                n_epochs=2,
                patience=100,
                checkpoint_dir=tmpdir,
            )
            train_model(model, ds, config)
            loaded = load_best_model(tmpdir, input_size=32, base_channels=4)
            assert loaded is not None

            x = torch.randn(1, 1, 32, 32)
            mu, log_sigma = loaded(x)
            assert mu.shape == (1, N_PARAMS)
