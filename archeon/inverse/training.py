"""Training loop for Bayesian CNN and Deep Ensembles.

Handles:
- Data loading from synthetic HDF5 datasets
- Normalization (crucial: CMB maps span ~[-300, 300] μK, params vary wildly)
- Training with heteroscedastic loss
- Validation and early stopping
- Checkpoint saving/loading
- Logging training metrics
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

from archeon.inverse.bayesian_cnn import (
    BayesianCosmologyCNN,
    CosmologyMLP,
    HeteroscedasticGaussianNLL,
    N_PARAMS,
    PARAM_NAMES,
)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class CMBDataset(Dataset):
    """PyTorch dataset for CMB maps and cosmological parameters.

    Loads from the HDF5 format produced by archeon.data.synthetic.
    Applies normalization to both maps and parameters.
    """

    def __init__(self, maps: np.ndarray, params: np.ndarray,
                 normalize_maps: bool = True, normalize_params: bool = True):
        """
        Parameters
        ----------
        maps : array of shape (N, H, W) or (N, npix)
            CMB map patches.
        params : array of shape (N, n_params)
            Cosmological parameters.
        """
        self.maps = maps.astype(np.float32)
        self.params = params.astype(np.float32)

        self.map_mean = 0.0
        self.map_std = 1.0
        self.param_means = np.zeros(params.shape[1], dtype=np.float32)
        self.param_stds = np.ones(params.shape[1], dtype=np.float32)

        if normalize_maps:
            self.map_mean = float(self.maps.mean())
            self.map_std = float(self.maps.std()) + 1e-8
            self.maps = (self.maps - self.map_mean) / self.map_std

        if normalize_params:
            self.param_means = self.params.mean(axis=0)
            self.param_stds = self.params.std(axis=0) + 1e-8
            self.params = (self.params - self.param_means) / self.param_stds

    def __len__(self) -> int:
        return len(self.maps)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        cmb_map = self.maps[idx]
        if cmb_map.ndim == 1:
            side = int(np.sqrt(len(cmb_map)))
            cmb_map = cmb_map[:side * side].reshape(side, side)
        if cmb_map.ndim == 2:
            cmb_map = cmb_map[np.newaxis, ...]  # add channel dim

        return torch.from_numpy(cmb_map), torch.from_numpy(self.params[idx])

    def denormalize_params(self, params_normed: np.ndarray) -> np.ndarray:
        """Convert normalized parameter values back to physical units."""
        return params_normed * self.param_stds + self.param_means

    def denormalize_sigma(self, sigma_normed: np.ndarray) -> np.ndarray:
        """Convert normalized uncertainties back to physical units."""
        return sigma_normed * self.param_stds


# ---------------------------------------------------------------------------
# Training configuration
# ---------------------------------------------------------------------------

@dataclass
class TrainConfig:
    """Training hyperparameters."""
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    n_epochs: int = 100
    patience: int = 15         # early stopping patience
    min_delta: float = 1e-4    # minimum improvement for early stopping
    val_fraction: float = 0.15
    scheduler_factor: float = 0.5
    scheduler_patience: int = 7
    grad_clip: float = 1.0
    device: str = "cpu"
    checkpoint_dir: str = "checkpoints"
    log_interval: int = 10     # log every N batches
    seed: int = 42


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

@dataclass
class TrainHistory:
    """Training history for plotting and analysis."""
    train_losses: list[float] = field(default_factory=list)
    val_losses: list[float] = field(default_factory=list)
    learning_rates: list[float] = field(default_factory=list)
    best_val_loss: float = float("inf")
    best_epoch: int = 0
    total_time_s: float = 0.0


def train_model(
    model: nn.Module,
    dataset: CMBDataset,
    config: TrainConfig | None = None,
) -> TrainHistory:
    """Train a Bayesian CNN with heteroscedastic loss.

    Features:
    - AdamW optimizer with weight decay
    - ReduceLROnPlateau scheduler
    - Gradient clipping
    - Early stopping
    - Checkpoint saving
    """
    if config is None:
        config = TrainConfig()

    torch.manual_seed(config.seed)
    device = torch.device(config.device)
    model = model.to(device)

    # Split into train/val
    n_val = int(len(dataset) * config.val_fraction)
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(
        dataset, [n_train, n_val],
        generator=torch.Generator().manual_seed(config.seed),
    )

    train_loader = DataLoader(train_ds, batch_size=config.batch_size,
                               shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=config.batch_size)

    criterion = HeteroscedasticGaussianNLL()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min",
        factor=config.scheduler_factor,
        patience=config.scheduler_patience,
    )

    os.makedirs(config.checkpoint_dir, exist_ok=True)
    history = TrainHistory()
    patience_counter = 0
    start_time = time.time()

    for epoch in range(config.n_epochs):
        # --- Train ---
        model.train()
        epoch_loss = 0.0
        n_batches = 0

        for batch_idx, (maps, params) in enumerate(train_loader):
            maps, params = maps.to(device), params.to(device)

            mu, log_sigma = model(maps)
            loss = criterion(mu, log_sigma, params)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip)
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        train_loss = epoch_loss / max(n_batches, 1)

        # --- Validate ---
        model.eval()
        val_loss = 0.0
        n_val_batches = 0

        with torch.no_grad():
            for maps, params in val_loader:
                maps, params = maps.to(device), params.to(device)
                mu, log_sigma = model(maps)
                loss = criterion(mu, log_sigma, params)
                val_loss += loss.item()
                n_val_batches += 1

        val_loss = val_loss / max(n_val_batches, 1)

        # --- Scheduler ---
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        # --- Logging ---
        history.train_losses.append(train_loss)
        history.val_losses.append(val_loss)
        history.learning_rates.append(current_lr)

        # --- Early stopping & checkpointing ---
        if val_loss < history.best_val_loss - config.min_delta:
            history.best_val_loss = val_loss
            history.best_epoch = epoch
            patience_counter = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss,
                "train_loss": train_loss,
            }, os.path.join(config.checkpoint_dir, "best_model.pt"))
        else:
            patience_counter += 1
            if patience_counter >= config.patience:
                break

    history.total_time_s = time.time() - start_time

    # Save training history
    with open(os.path.join(config.checkpoint_dir, "history.json"), "w") as f:
        json.dump({
            "train_losses": history.train_losses,
            "val_losses": history.val_losses,
            "learning_rates": history.learning_rates,
            "best_val_loss": history.best_val_loss,
            "best_epoch": history.best_epoch,
            "total_time_s": history.total_time_s,
        }, f, indent=2)

    return history


# ---------------------------------------------------------------------------
# Ensemble training
# ---------------------------------------------------------------------------

def train_ensemble(
    n_members: int,
    dataset: CMBDataset,
    config: TrainConfig | None = None,
    **model_kwargs,
) -> list[TrainHistory]:
    """Train a Deep Ensemble: N independent models with different seeds.

    Each member gets a unique random seed for initialization and
    data shuffling, ensuring diversity in the ensemble.
    """
    if config is None:
        config = TrainConfig()

    histories = []

    for i in range(n_members):
        member_config = TrainConfig(
            **{k: getattr(config, k) for k in config.__dataclass_fields__}
        )
        member_config.seed = config.seed + i * 100
        member_config.checkpoint_dir = os.path.join(
            config.checkpoint_dir, f"member_{i}"
        )

        model = BayesianCosmologyCNN(**model_kwargs)
        history = train_model(model, dataset, member_config)
        histories.append(history)

    return histories


# ---------------------------------------------------------------------------
# Loading best model
# ---------------------------------------------------------------------------

def load_best_model(checkpoint_dir: str, device: str = "cpu",
                     **model_kwargs) -> BayesianCosmologyCNN:
    """Load the best model from a training run."""
    model = BayesianCosmologyCNN(**model_kwargs)
    checkpoint = torch.load(
        os.path.join(checkpoint_dir, "best_model.pt"),
        map_location=device,
        weights_only=True,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    return model
