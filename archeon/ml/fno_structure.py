"""Fourier Neural Operator for cosmological structure formation.

Predicts the evolution of density fields from initial conditions (z=1100)
to the present day (z=0), achieving ~1000x speedup over N-body simulations.

FNO operates in Fourier space: it learns integral kernel operators via
spectral convolutions. In each Fourier layer, the signal is transformed
with FFT, the low-frequency modes are multiplied by learnable complex
weights, and the result is combined with a local (pointwise) linear
transformation back in physical space.

Reference: Li et al., "Fourier Neural Operator for Parametric Partial
Differential Equations", ICLR 2021.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.fft import rfft2, irfft2


# ---------------------------------------------------------------------------
# Spectral convolution layer (2D)
# ---------------------------------------------------------------------------

class SpectralConv2d(nn.Module):
    """2D spectral convolution: learnable Fourier-space filter.

    Retains only the first `modes` Fourier modes in each spatial dimension,
    multiplies them by complex weight matrices R, then transforms back.
    """

    def __init__(self, in_channels: int, out_channels: int,
                 modes1: int, modes2: int):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = modes1
        self.modes2 = modes2

        scale = 1.0 / (in_channels * out_channels)
        self.weights1 = nn.Parameter(
            scale * torch.randn(in_channels, out_channels,
                                modes1, modes2, dtype=torch.cfloat))
        self.weights2 = nn.Parameter(
            scale * torch.randn(in_channels, out_channels,
                                modes1, modes2, dtype=torch.cfloat))

    def _compl_mul(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """Complex-valued einsum: (batch, in, x, y) x (in, out, x, y) -> (batch, out, x, y)."""
        return torch.einsum("bixy,ioxy->boxy", a, b)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch = x.shape[0]
        x_ft = rfft2(x, norm="ortho")

        m1, m2 = self.modes1, self.modes2
        out_ft = torch.zeros(
            batch, self.out_channels, x.size(-2), x.size(-1) // 2 + 1,
            dtype=torch.cfloat, device=x.device)

        out_ft[:, :, :m1, :m2] = self._compl_mul(x_ft[:, :, :m1, :m2], self.weights1)
        out_ft[:, :, -m1:, :m2] = self._compl_mul(x_ft[:, :, -m1:, :m2], self.weights2)

        return irfft2(out_ft, s=(x.size(-2), x.size(-1)), norm="ortho")


class FourierBlock(nn.Module):
    """One FNO layer = spectral conv + pointwise conv + activation."""

    def __init__(self, width: int, modes1: int, modes2: int):
        super().__init__()
        self.spectral = SpectralConv2d(width, width, modes1, modes2)
        self.pointwise = nn.Conv2d(width, width, kernel_size=1)
        self.norm = nn.InstanceNorm2d(width)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.gelu(self.norm(self.spectral(x) + self.pointwise(x)))


# ---------------------------------------------------------------------------
# Full FNO model
# ---------------------------------------------------------------------------

class FNOStructureFormation(nn.Module):
    """Fourier Neural Operator for density field evolution.

    Parameters
    ----------
    in_channels : int
        Input channels (1 for scalar density field).
    out_channels : int
        Output channels.
    width : int
        Internal channel width of Fourier layers.
    modes : int
        Number of Fourier modes to retain per dimension.
    n_layers : int
        Number of FNO layers.
    """

    def __init__(self, in_channels: int = 1, out_channels: int = 1,
                 width: int = 32, modes: int = 12, n_layers: int = 4):
        super().__init__()
        self.width = width

        self.lift = nn.Conv2d(in_channels, width, kernel_size=1)

        self.layers = nn.ModuleList([
            FourierBlock(width, modes, modes) for _ in range(n_layers)
        ])

        self.proj = nn.Sequential(
            nn.Conv2d(width, width, kernel_size=1),
            nn.GELU(),
            nn.Conv2d(width, out_channels, kernel_size=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Parameters
        ----------
        x : tensor (batch, C_in, H, W)
            Initial density field at high redshift.

        Returns
        -------
        tensor (batch, C_out, H, W)
            Predicted density field at z=0.
        """
        h = self.lift(x)
        for layer in self.layers:
            h = layer(h)
        return self.proj(h)


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_density_pair(
    size: int = 64,
    n_samples: int = 100,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic density field pairs for FNO training.

    Generates Gaussian random fields (initial) and applies a simplified
    Zel'dovich-like nonlinear evolution as the "target".

    Returns (initial, evolved) arrays of shape (n_samples, 1, size, size).
    """
    rng = np.random.default_rng(seed)

    kx = np.fft.fftfreq(size, d=1.0 / size)
    ky = np.fft.fftfreq(size, d=1.0 / size)
    KX, KY = np.meshgrid(kx, ky)
    k2 = KX**2 + KY**2
    k2[0, 0] = 1.0  # avoid division by zero

    initial = np.zeros((n_samples, 1, size, size), dtype=np.float32)
    evolved = np.zeros_like(initial)

    for i in range(n_samples):
        n_s = rng.uniform(0.92, 1.02)
        k_abs = np.sqrt(k2)
        k_abs[0, 0] = 1.0
        # Power-law P(k) ∝ k^(n_s - 1)
        pk = k_abs ** (n_s - 1.0)
        pk[0, 0] = 0.0

        noise = rng.standard_normal((size, size)) + 1j * rng.standard_normal((size, size))
        delta_k = noise * np.sqrt(pk)
        delta_init = np.real(np.fft.ifft2(delta_k)).astype(np.float32)

        sigma = delta_init.std() + 1e-10
        delta_init /= sigma

        # Simplified nonlinear evolution: lognormal approximation
        growth_factor = rng.uniform(5.0, 15.0)
        delta_evolved = np.exp(growth_factor * delta_init - 0.5 * growth_factor**2) - 1.0
        delta_evolved = delta_evolved.astype(np.float32)

        e_std = delta_evolved.std() + 1e-10
        delta_evolved /= e_std

        initial[i, 0] = delta_init
        evolved[i, 0] = delta_evolved

    return initial, evolved


def train_fno(
    model: FNOStructureFormation,
    initial: np.ndarray,
    evolved: np.ndarray,
    n_epochs: int = 50,
    batch_size: int = 16,
    lr: float = 1e-3,
    val_fraction: float = 0.1,
    device: str = "cpu",
    patience: int = 10,
) -> dict:
    """Train FNO on density field pairs."""
    model = model.to(device)

    n = len(initial)
    n_val = max(int(n * val_fraction), 1)
    idx = np.random.default_rng(42).permutation(n)
    tr_idx, val_idx = idx[n_val:], idx[:n_val]

    x_train = torch.from_numpy(initial[tr_idx]).to(device)
    y_train = torch.from_numpy(evolved[tr_idx]).to(device)
    x_val = torch.from_numpy(initial[val_idx]).to(device)
    y_val = torch.from_numpy(evolved[val_idx]).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, n_epochs)

    train_losses, val_losses = [], []
    best_val = float("inf")
    best_epoch = 0
    wait = 0

    for epoch in range(n_epochs):
        model.train()
        perm = torch.randperm(len(x_train))
        epoch_loss = 0.0
        nb = 0
        for start in range(0, len(x_train), batch_size):
            batch_idx = perm[start:start + batch_size]
            if len(batch_idx) < 2:
                continue
            xb, yb = x_train[batch_idx], y_train[batch_idx]
            pred = model(xb)
            loss = F.mse_loss(pred, yb)
            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item()
            nb += 1
        train_losses.append(epoch_loss / max(nb, 1))
        scheduler.step()

        model.eval()
        with torch.no_grad():
            pred_v = model(x_val)
            vl = F.mse_loss(pred_v, y_val).item()
        val_losses.append(vl)

        if vl < best_val - 1e-6:
            best_val = vl
            best_epoch = epoch
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break

    return {"train_losses": train_losses, "val_losses": val_losses,
            "best_epoch": best_epoch}


def compute_power_spectrum_2d(field: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute radially averaged 2D power spectrum.

    Parameters
    ----------
    field : 2D array (H, W).

    Returns
    -------
    k_bins, pk : 1D arrays.
    """
    fk = np.fft.fft2(field)
    pk2d = np.abs(fk) ** 2 / field.size

    h, w = field.shape
    kx = np.fft.fftfreq(w, d=1.0 / w)
    ky = np.fft.fftfreq(h, d=1.0 / h)
    KX, KY = np.meshgrid(kx, ky)
    k_mag = np.sqrt(KX**2 + KY**2).ravel()
    pk_flat = pk2d.ravel()

    k_max = int(min(h, w) // 2)
    k_bins = np.arange(1, k_max + 1, dtype=float)
    pk_avg = np.zeros(k_max)
    for i, kb in enumerate(k_bins):
        mask = (k_mag >= kb - 0.5) & (k_mag < kb + 0.5)
        if mask.any():
            pk_avg[i] = pk_flat[mask].mean()

    return k_bins, pk_avg
