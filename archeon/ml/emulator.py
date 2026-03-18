"""Neural emulator for CMB power spectrum C_l.

Replaces CLASS/CAMB (~30s per evaluation) with a neural network (~1ms).
Trained on Latin Hypercube-sampled parameter sets, the emulator learns
the mapping: theta (6 LCDM params) -> C_l (angular power spectrum).

Architecture: MLP with residual connections. Residuals help the network
learn small corrections to a baseline, improving accuracy in the regime
where C_l varies smoothly with parameters.

Target accuracy: < 0.1% relative error vs CLASS.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Residual MLP
# ---------------------------------------------------------------------------

class ResidualMLPBlock(nn.Module):
    """MLP block with skip connection: y = ReLU(BN(Linear(x))) + x."""

    def __init__(self, dim: int, dropout: float = 0.0):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.relu(self.net(x) + x)


class ClEmulator(nn.Module):
    """Neural emulator: 6 cosmological parameters -> C_l spectrum.

    Parameters
    ----------
    n_params : int
        Number of input cosmological parameters.
    n_ell : int
        Number of output multipoles (l=2..l_max).
    hidden_dim : int
        Width of hidden layers.
    n_blocks : int
        Number of residual blocks.
    dropout : float
        Dropout rate.
    """

    def __init__(self, n_params: int = 6, n_ell: int = 2499,
                 hidden_dim: int = 512, n_blocks: int = 4,
                 dropout: float = 0.05):
        super().__init__()
        self.n_params = n_params
        self.n_ell = n_ell

        self.input_proj = nn.Sequential(
            nn.Linear(n_params, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
        )

        self.blocks = nn.Sequential(
            *[ResidualMLPBlock(hidden_dim, dropout) for _ in range(n_blocks)]
        )

        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_ell),
        )

    def forward(self, theta: torch.Tensor) -> torch.Tensor:
        """Predict C_l from cosmological parameters.

        Parameters
        ----------
        theta : tensor of shape (batch, n_params)

        Returns
        -------
        cl : tensor of shape (batch, n_ell) — log10(C_l) values.
        """
        h = self.input_proj(theta)
        h = self.blocks(h)
        return self.output_proj(h)

    def predict_cl(self, theta: np.ndarray, device: str = "cpu") -> np.ndarray:
        """Convenience: numpy in, numpy out. Returns C_l (not log)."""
        self.eval()
        self.to(device)
        with torch.no_grad():
            t = torch.from_numpy(theta.astype(np.float32)).to(device)
            if t.dim() == 1:
                t = t.unsqueeze(0)
            log_cl = self(t)
        return 10.0 ** log_cl.cpu().numpy()


# ---------------------------------------------------------------------------
# Data normalization
# ---------------------------------------------------------------------------

@dataclass
class EmulatorNormalization:
    """Stores normalization statistics for inputs and outputs."""
    theta_mean: np.ndarray
    theta_std: np.ndarray
    cl_mean: np.ndarray
    cl_std: np.ndarray

    def normalize_theta(self, theta: np.ndarray) -> np.ndarray:
        return (theta - self.theta_mean) / (self.theta_std + 1e-10)

    def normalize_cl(self, cl: np.ndarray) -> np.ndarray:
        return (cl - self.cl_mean) / (self.cl_std + 1e-10)

    def denormalize_cl(self, cl_norm: np.ndarray) -> np.ndarray:
        return cl_norm * (self.cl_std + 1e-10) + self.cl_mean


def compute_normalization(theta: np.ndarray,
                          cl: np.ndarray) -> EmulatorNormalization:
    """Compute normalization stats from training data."""
    return EmulatorNormalization(
        theta_mean=theta.mean(axis=0),
        theta_std=theta.std(axis=0),
        cl_mean=cl.mean(axis=0),
        cl_std=cl.std(axis=0),
    )


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def generate_training_data(
    n_samples: int = 1000,
    l_max: int = 2500,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate training pairs (theta, C_l) using internal physics.

    Uses our approximate C_l computation as a stand-in for CLASS.
    For production, replace with CLASS wrapper.

    Returns (theta_array, cl_array) both of shape (n_samples, ...).
    """
    from archeon.data.priors import generate_parameter_sets

    ps = generate_parameter_sets(n_samples, seed=seed)

    theta_list = np.column_stack([
        ps["H0"], ps["Omega_b_h2"], ps["Omega_cdm_h2"],
        ps["n_s"], np.log(ps["A_s"] * 1e10), ps["tau_reio"],
    ])

    from archeon.data.synthetic import compute_cl_internal

    cl_list = []
    for i in range(n_samples):
        cosmo = {
            "H0": float(ps["H0"][i]),
            "h": float(ps["h"][i]),
            "Omega_m": float(ps["Omega_m"][i]),
            "Omega_b": float(ps["Omega_b"][i]),
            "Omega_Lambda": float(ps["Omega_Lambda"][i]),
            "A_s": float(ps["A_s"][i]),
            "n_s": float(ps["n_s"][i]),
        }
        cl = compute_cl_internal(cosmo, lmax=l_max)
        cl_list.append(cl[2:])  # skip l=0,1

    # Pad to same length
    max_len = max(len(c) for c in cl_list)
    cl_array = np.zeros((n_samples, max_len))
    for i, c in enumerate(cl_list):
        cl_array[i, :len(c)] = c

    return theta_list, cl_array


def train_emulator(
    model: ClEmulator,
    theta: np.ndarray,
    cl: np.ndarray,
    n_epochs: int = 100,
    batch_size: int = 64,
    lr: float = 1e-3,
    val_fraction: float = 0.1,
    device: str = "cpu",
    patience: int = 15,
) -> dict:
    """Train the C_l emulator.

    Works in log10(C_l) space for numerical stability.

    Returns dict with train_losses, val_losses, best_epoch.
    """
    model = model.to(device)

    # Work in log10 space (C_l spans many orders of magnitude)
    cl_safe = np.maximum(cl, 1e-30)
    log_cl = np.log10(cl_safe)

    # Normalize inputs
    norm = compute_normalization(theta, log_cl)
    theta_n = norm.normalize_theta(theta).astype(np.float32)
    cl_n = log_cl.astype(np.float32)  # output is raw log10(C_l)

    # Split
    n = len(theta)
    n_val = max(int(n * val_fraction), 1)
    idx = np.random.default_rng(42).permutation(n)
    train_idx, val_idx = idx[n_val:], idx[:n_val]

    train_ds = torch.utils.data.TensorDataset(
        torch.from_numpy(theta_n[train_idx]),
        torch.from_numpy(cl_n[train_idx]),
    )
    val_ds = torch.utils.data.TensorDataset(
        torch.from_numpy(theta_n[val_idx]),
        torch.from_numpy(cl_n[val_idx]),
    )
    train_loader = torch.utils.data.DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = torch.utils.data.DataLoader(
        val_ds, batch_size=batch_size)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, patience=patience // 2, factor=0.5)

    train_losses, val_losses = [], []
    best_val = float("inf")
    best_epoch = 0
    wait = 0

    for epoch in range(n_epochs):
        model.train()
        tloss = 0.0
        nb = 0
        for t_batch, c_batch in train_loader:
            t_batch, c_batch = t_batch.to(device), c_batch.to(device)
            pred = model(t_batch)
            n_ell = min(pred.shape[1], c_batch.shape[1])
            loss = F.mse_loss(pred[:, :n_ell], c_batch[:, :n_ell])
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            tloss += loss.item()
            nb += 1
        train_losses.append(tloss / max(nb, 1))

        model.eval()
        vloss = 0.0
        nvb = 0
        with torch.no_grad():
            for t_batch, c_batch in val_loader:
                t_batch, c_batch = t_batch.to(device), c_batch.to(device)
                pred = model(t_batch)
                n_ell = min(pred.shape[1], c_batch.shape[1])
                vloss += F.mse_loss(pred[:, :n_ell], c_batch[:, :n_ell]).item()
                nvb += 1
        val_losses.append(vloss / max(nvb, 1))

        scheduler.step(val_losses[-1])

        if val_losses[-1] < best_val - 1e-6:
            best_val = val_losses[-1]
            best_epoch = epoch
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break

    return {
        "train_losses": train_losses,
        "val_losses": val_losses,
        "best_epoch": best_epoch,
        "normalization": norm,
    }


def benchmark_emulator(model: ClEmulator, n_params: int = 6,
                       batch_size: int = 100, n_repeats: int = 100,
                       device: str = "cpu") -> float:
    """Measure emulator inference time in ms per sample."""
    model = model.to(device)
    model.eval()
    x = torch.randn(batch_size, n_params).to(device)

    with torch.no_grad():
        for _ in range(10):
            model(x)

    t0 = perf_counter()
    with torch.no_grad():
        for _ in range(n_repeats):
            model(x)
    elapsed = perf_counter() - t0

    return (elapsed / n_repeats / batch_size) * 1000
