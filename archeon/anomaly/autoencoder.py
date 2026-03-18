"""Convolutional Autoencoder for CMB anomaly detection.

Core idea: train an autoencoder to reconstruct "normal" CMB maps
(generated from standard LCDM). When applied to real data,
regions with high reconstruction error are anomalous — they
don't look like standard cosmology predicts.

Architecture:
  Encoder: input (1, H, W) -> latent vector (latent_dim,)
  Decoder: latent vector -> reconstructed map (1, H, W)

Anomaly score = reconstruction error per pixel or per region.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Encoder / Decoder blocks
# ---------------------------------------------------------------------------

class EncoderBlock(nn.Module):
    """Conv → BN → ReLU → Conv → BN → ReLU → MaxPool."""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
        self.pool = nn.MaxPool2d(2)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.block(x)
        pooled = self.pool(features)
        return pooled, features  # return pre-pool for skip connections


class DecoderBlock(nn.Module):
    """Upsample → Conv → BN → ReLU → Conv → BN → ReLU."""

    def __init__(self, in_ch: int, out_ch: int, use_skip: bool = False):
        super().__init__()
        self.use_skip = use_skip
        cat_ch = in_ch + out_ch if use_skip else in_ch
        self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False)
        self.block = nn.Sequential(
            nn.Conv2d(cat_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor,
                skip: torch.Tensor | None = None) -> torch.Tensor:
        x = self.up(x)
        if self.use_skip and skip is not None:
            if x.shape != skip.shape:
                x = F.interpolate(x, size=skip.shape[2:], mode="bilinear",
                                  align_corners=False)
            x = torch.cat([x, skip], dim=1)
        return self.block(x)


# ---------------------------------------------------------------------------
# Main autoencoder
# ---------------------------------------------------------------------------

class CMBAutoencoder(nn.Module):
    """Convolutional autoencoder for CMB map reconstruction.

    Encoder compresses to a latent vector. Decoder reconstructs.
    High reconstruction error = anomaly.

    Parameters
    ----------
    input_size : int
        Spatial dimension (input_size x input_size).
    base_channels : int
        Channels in first encoder layer (doubles each block).
    latent_dim : int
        Dimensionality of latent representation.
    use_skip : bool
        Whether to use U-Net-style skip connections.
    """

    def __init__(self, input_size: int = 64, base_channels: int = 32,
                 latent_dim: int = 64, use_skip: bool = False):
        super().__init__()
        self.input_size = input_size
        self.latent_dim = latent_dim
        self.use_skip = use_skip

        c = base_channels
        self.enc1 = EncoderBlock(1, c)
        self.enc2 = EncoderBlock(c, c * 2)
        self.enc3 = EncoderBlock(c * 2, c * 4)
        self.enc4 = EncoderBlock(c * 4, c * 8)

        spatial = input_size // 16
        self.flatten_dim = c * 8 * spatial * spatial

        self.fc_encode = nn.Sequential(
            nn.Linear(self.flatten_dim, 256),
            nn.ReLU(),
            nn.Linear(256, latent_dim),
        )

        self.fc_decode = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.ReLU(),
            nn.Linear(256, self.flatten_dim),
            nn.ReLU(),
        )

        self.dec4 = DecoderBlock(c * 8, c * 4, use_skip=use_skip)
        self.dec3 = DecoderBlock(c * 4, c * 2, use_skip=use_skip)
        self.dec2 = DecoderBlock(c * 2, c, use_skip=use_skip)
        self.dec1 = DecoderBlock(c, c, use_skip=False)

        self.final = nn.Conv2d(c, 1, 1)

        self._spatial = spatial
        self._enc_channels = c * 8

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        x, s1 = self.enc1(x)
        x, s2 = self.enc2(x)
        x, s3 = self.enc3(x)
        x, s4 = self.enc4(x)
        x = x.flatten(1)
        z = self.fc_encode(x)
        return z

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        x = self.fc_decode(z)
        x = x.view(-1, self._enc_channels, self._spatial, self._spatial)
        x = self.dec4(x)
        x = self.dec3(x)
        x = self.dec2(x)
        x = self.dec1(x)
        return self.final(x)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Returns (reconstruction, latent_vector)."""
        z = self.encode(x)
        recon = self.decode(z)
        if recon.shape[2:] != x.shape[2:]:
            recon = F.interpolate(recon, size=x.shape[2:], mode="bilinear",
                                  align_corners=False)
        return recon, z


# ---------------------------------------------------------------------------
# Anomaly scoring
# ---------------------------------------------------------------------------

@dataclass
class AnomalyMap:
    """Per-pixel anomaly scores for a CMB map."""
    pixel_scores: np.ndarray       # (H, W) reconstruction error
    global_score: float            # mean anomaly score
    threshold: float               # anomaly threshold
    anomalous_fraction: float      # fraction of pixels above threshold
    anomalous_mask: np.ndarray     # (H, W) bool mask of anomalous pixels


def compute_anomaly_scores(
    model: CMBAutoencoder,
    maps: np.ndarray,
    threshold_sigma: float = 3.0,
    device: str = "cpu",
) -> list[AnomalyMap]:
    """Compute per-pixel anomaly scores for a batch of maps.

    Anomaly score = (pixel - reconstruction)^2, normalized.
    Pixels above threshold_sigma * std are flagged as anomalous.
    """
    model = model.to(device)
    model.eval()

    if maps.ndim == 3:
        maps_t = torch.from_numpy(maps[:, np.newaxis]).float().to(device)
    else:
        maps_t = torch.from_numpy(maps).float().to(device)

    with torch.no_grad():
        recon, _ = model(maps_t)

    error = (maps_t - recon).cpu().numpy() ** 2

    results = []
    for i in range(len(maps)):
        err = error[i, 0]
        global_score = float(err.mean())
        std = float(err.std()) + 1e-10
        threshold = float(err.mean() + threshold_sigma * std)
        mask = err > threshold
        results.append(AnomalyMap(
            pixel_scores=err,
            global_score=global_score,
            threshold=threshold,
            anomalous_fraction=float(mask.mean()),
            anomalous_mask=mask,
        ))

    return results


def train_autoencoder(
    model: CMBAutoencoder,
    maps: np.ndarray,
    n_epochs: int = 50,
    batch_size: int = 32,
    lr: float = 1e-3,
    device: str = "cpu",
) -> list[float]:
    """Train autoencoder on normal (LCDM) CMB maps.

    Returns list of per-epoch losses.
    """
    model = model.to(device)
    model.train()

    if maps.ndim == 3:
        data = torch.from_numpy(maps[:, np.newaxis]).float()
    else:
        data = torch.from_numpy(maps).float()

    dataset = torch.utils.data.TensorDataset(data)
    loader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True, drop_last=True,
    )

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    losses = []

    for epoch in range(n_epochs):
        epoch_loss = 0.0
        n_batches = 0
        for (batch,) in loader:
            batch = batch.to(device)
            recon, z = model(batch)
            loss = F.mse_loss(recon, batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1
        losses.append(epoch_loss / max(n_batches, 1))

    return losses
