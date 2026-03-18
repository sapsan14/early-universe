"""Universal training loop for neural surrogate models.

Provides a unified trainer for all Phase 6 models (Emulator, FNO, PINN)
with logging, checkpointing, learning rate scheduling, and calibration
hooks.

Design goals:
- Model-agnostic: works with any nn.Module + loss function.
- Callback-based: custom hooks for physics losses, logging, etc.
- Reproducible: seed control, deterministic data splits.
- Efficient: mixed-precision support, gradient accumulation.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class SurrogateTrainConfig:
    """Training hyperparameters for surrogate models."""
    n_epochs: int = 200
    batch_size: int = 64
    lr: float = 1e-3
    weight_decay: float = 1e-4
    patience: int = 20
    grad_clip: float = 1.0
    val_fraction: float = 0.1
    scheduler: str = "cosine"  # "cosine", "plateau", "none"
    seed: int = 42
    device: str = "cpu"
    checkpoint_dir: str | None = None
    log_every: int = 10


# ---------------------------------------------------------------------------
# Training result
# ---------------------------------------------------------------------------

@dataclass
class TrainResult:
    """Container for training results."""
    train_losses: list[float] = field(default_factory=list)
    val_losses: list[float] = field(default_factory=list)
    best_epoch: int = 0
    best_val_loss: float = float("inf")
    elapsed_seconds: float = 0.0
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

class TrainCallback:
    """Base class for training callbacks."""

    def on_epoch_start(self, epoch: int, model: nn.Module) -> None:
        pass

    def on_epoch_end(self, epoch: int, model: nn.Module,
                     train_loss: float, val_loss: float) -> None:
        pass

    def on_train_end(self, model: nn.Module, result: TrainResult) -> None:
        pass


class PrintCallback(TrainCallback):
    """Prints progress every N epochs."""

    def __init__(self, every: int = 10):
        self.every = every

    def on_epoch_end(self, epoch: int, model: nn.Module,
                     train_loss: float, val_loss: float) -> None:
        if (epoch + 1) % self.every == 0 or epoch == 0:
            print(f"  Epoch {epoch+1:4d} | train={train_loss:.6f} "
                  f"| val={val_loss:.6f}")


class LogCallback(TrainCallback):
    """Accumulates metrics into a JSON-serializable log."""

    def __init__(self):
        self.log: list[dict[str, Any]] = []

    def on_epoch_end(self, epoch: int, model: nn.Module,
                     train_loss: float, val_loss: float) -> None:
        self.log.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "timestamp": time.time(),
        })

    def save(self, path: str | Path) -> None:
        with open(path, "w") as f:
            json.dump(self.log, f, indent=2)


# ---------------------------------------------------------------------------
# Universal trainer
# ---------------------------------------------------------------------------

def make_dataloaders(
    x: np.ndarray | torch.Tensor,
    y: np.ndarray | torch.Tensor,
    batch_size: int,
    val_fraction: float,
    seed: int,
) -> tuple[DataLoader, DataLoader]:
    """Create train/val dataloaders with deterministic split."""
    if isinstance(x, np.ndarray):
        x = torch.from_numpy(x.astype(np.float32))
    if isinstance(y, np.ndarray):
        y = torch.from_numpy(y.astype(np.float32))

    n = len(x)
    n_val = max(int(n * val_fraction), 1)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    tr_idx, val_idx = idx[n_val:], idx[:n_val]

    train_ds = TensorDataset(x[tr_idx], y[tr_idx])
    val_ds = TensorDataset(x[val_idx], y[val_idx])

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True,
        drop_last=len(train_ds) > batch_size)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    return train_loader, val_loader


def train_surrogate(
    model: nn.Module,
    x: np.ndarray | torch.Tensor,
    y: np.ndarray | torch.Tensor,
    config: SurrogateTrainConfig | None = None,
    loss_fn: Callable | None = None,
    callbacks: list[TrainCallback] | None = None,
) -> TrainResult:
    """Universal training loop for surrogate models.

    Parameters
    ----------
    model : nn.Module
        Any PyTorch model.
    x : array-like, shape (N, ...)
        Inputs.
    y : array-like, shape (N, ...)
        Targets.
    config : SurrogateTrainConfig
        Training hyperparameters.
    loss_fn : callable, optional
        Loss function(pred, target) -> scalar. Default: MSE.
    callbacks : list of TrainCallback, optional.

    Returns
    -------
    TrainResult
    """
    if config is None:
        config = SurrogateTrainConfig()
    if loss_fn is None:
        loss_fn = F.mse_loss
    if callbacks is None:
        callbacks = [PrintCallback(config.log_every)]

    device = config.device
    model = model.to(device)

    train_loader, val_loader = make_dataloaders(
        x, y, config.batch_size, config.val_fraction, config.seed)

    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.lr, weight_decay=config.weight_decay)

    if config.scheduler == "cosine":
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, config.n_epochs)
    elif config.scheduler == "plateau":
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, patience=config.patience // 2, factor=0.5)
    else:
        sched = None

    result = TrainResult()
    best_state = None
    wait = 0
    t0 = time.perf_counter()

    for epoch in range(config.n_epochs):
        for cb in callbacks:
            cb.on_epoch_start(epoch, model)

        # Train
        model.train()
        epoch_loss = 0.0
        n_batches = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            optimizer.zero_grad()
            loss.backward()
            if config.grad_clip > 0:
                nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip)
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1
        train_loss = epoch_loss / max(n_batches, 1)

        # Validate
        model.eval()
        val_loss_sum = 0.0
        n_val = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                pred = model(xb)
                val_loss_sum += loss_fn(pred, yb).item()
                n_val += 1
        val_loss = val_loss_sum / max(n_val, 1)

        result.train_losses.append(train_loss)
        result.val_losses.append(val_loss)

        # Scheduler
        if config.scheduler == "cosine" and sched:
            sched.step()
        elif config.scheduler == "plateau" and sched:
            sched.step(val_loss)

        # Checkpointing
        if val_loss < result.best_val_loss - 1e-8:
            result.best_val_loss = val_loss
            result.best_epoch = epoch
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1

        for cb in callbacks:
            cb.on_epoch_end(epoch, model, train_loss, val_loss)

        if wait >= config.patience:
            break

    result.elapsed_seconds = time.perf_counter() - t0

    # Restore best
    if best_state is not None:
        model.load_state_dict(best_state)
        model.to(device)

    # Save checkpoint
    if config.checkpoint_dir:
        ckpt_dir = Path(config.checkpoint_dir)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), ckpt_dir / "best_model.pt")
        with open(ckpt_dir / "train_result.json", "w") as f:
            json.dump({
                "train_losses": result.train_losses,
                "val_losses": result.val_losses,
                "best_epoch": result.best_epoch,
                "best_val_loss": result.best_val_loss,
                "elapsed_seconds": result.elapsed_seconds,
            }, f, indent=2)

    for cb in callbacks:
        cb.on_train_end(model, result)

    return result


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

def relative_error_analysis(
    model: nn.Module,
    x_test: np.ndarray | torch.Tensor,
    y_test: np.ndarray | torch.Tensor,
    device: str = "cpu",
) -> dict:
    """Compute element-wise relative errors on test data.

    Returns dict with mean, max, percentile errors.
    """
    model = model.to(device)
    model.eval()

    if isinstance(x_test, np.ndarray):
        x_test = torch.from_numpy(x_test.astype(np.float32))
    if isinstance(y_test, np.ndarray):
        y_test = torch.from_numpy(y_test.astype(np.float32))

    with torch.no_grad():
        pred = model(x_test.to(device)).cpu()
    y_np = y_test.numpy()
    p_np = pred.numpy()

    rel = np.abs(p_np - y_np) / (np.abs(y_np) + 1e-10)

    return {
        "mean_rel_error": float(rel.mean()),
        "max_rel_error": float(rel.max()),
        "median_rel_error": float(np.median(rel)),
        "p95_rel_error": float(np.percentile(rel, 95)),
        "p99_rel_error": float(np.percentile(rel, 99)),
    }


def compare_models(
    models: dict[str, nn.Module],
    x_test: np.ndarray,
    y_test: np.ndarray,
    device: str = "cpu",
) -> dict[str, dict]:
    """Compare multiple models on the same test data."""
    results = {}
    for name, model in models.items():
        results[name] = relative_error_analysis(model, x_test, y_test, device)
    return results
