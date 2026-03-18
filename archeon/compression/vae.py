"""Variational Autoencoder for cosmological field compression.

A VAE learns a probabilistic latent representation of CMB maps.
Unlike a regular autoencoder, it maps to a distribution in latent
space, enabling:
- Generation of new plausible CMB maps
- Smooth interpolation between cosmologies
- Discovery of which latent dimensions encode which physics

The KL divergence term regularizes the latent space to be Gaussian,
making it interpretable and navigable.

Loss = Reconstruction (MSE) + beta * KL divergence
  beta > 1: stronger regularization, more disentangled (beta-VAE)
  beta = 1: standard VAE
  beta < 1: better reconstruction, less structure in latent space
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class CosmologyVAE(nn.Module):
    """Variational Autoencoder for CMB maps.

    Parameters
    ----------
    input_size : int
        Spatial dimension of input maps.
    base_channels : int
        Channels in first conv layer.
    latent_dim : int
        Dimensionality of latent space.
    """

    def __init__(self, input_size: int = 64, base_channels: int = 32,
                 latent_dim: int = 32):
        super().__init__()
        self.input_size = input_size
        self.latent_dim = latent_dim
        c = base_channels

        # Encoder
        self.encoder = nn.Sequential(
            nn.Conv2d(1, c, 4, stride=2, padding=1),
            nn.BatchNorm2d(c), nn.ReLU(),
            nn.Conv2d(c, c * 2, 4, stride=2, padding=1),
            nn.BatchNorm2d(c * 2), nn.ReLU(),
            nn.Conv2d(c * 2, c * 4, 4, stride=2, padding=1),
            nn.BatchNorm2d(c * 4), nn.ReLU(),
            nn.Conv2d(c * 4, c * 8, 4, stride=2, padding=1),
            nn.BatchNorm2d(c * 8), nn.ReLU(),
        )

        spatial = input_size // 16
        self._spatial = spatial
        self._dec_channels = c * 8
        flat_dim = c * 8 * spatial * spatial

        self.fc_mu = nn.Linear(flat_dim, latent_dim)
        self.fc_logvar = nn.Linear(flat_dim, latent_dim)

        # Decoder
        self.fc_decode = nn.Linear(latent_dim, flat_dim)

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(c * 8, c * 4, 4, stride=2, padding=1),
            nn.BatchNorm2d(c * 4), nn.ReLU(),
            nn.ConvTranspose2d(c * 4, c * 2, 4, stride=2, padding=1),
            nn.BatchNorm2d(c * 2), nn.ReLU(),
            nn.ConvTranspose2d(c * 2, c, 4, stride=2, padding=1),
            nn.BatchNorm2d(c), nn.ReLU(),
            nn.ConvTranspose2d(c, 1, 4, stride=2, padding=1),
        )

    def encode(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.encoder(x).flatten(1)
        return self.fc_mu(h), self.fc_logvar(h)

    def reparameterize(self, mu: torch.Tensor,
                       logvar: torch.Tensor) -> torch.Tensor:
        """Reparameterization trick: z = mu + std * epsilon."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + std * eps

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        h = self.fc_decode(z)
        h = h.view(-1, self._dec_channels, self._spatial, self._spatial)
        recon = self.decoder(h)
        return recon

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor,
                                                  torch.Tensor]:
        """Returns (reconstruction, mu, logvar)."""
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        if recon.shape[2:] != x.shape[2:]:
            recon = F.interpolate(recon, size=x.shape[2:], mode="bilinear",
                                  align_corners=False)
        return recon, mu, logvar

    def generate(self, n_samples: int = 1,
                 device: str = "cpu") -> torch.Tensor:
        """Sample from prior and decode."""
        z = torch.randn(n_samples, self.latent_dim).to(device)
        return self.decode(z)


def vae_loss(recon: torch.Tensor, target: torch.Tensor,
             mu: torch.Tensor, logvar: torch.Tensor,
             beta: float = 1.0) -> tuple[torch.Tensor, torch.Tensor,
                                          torch.Tensor]:
    """VAE loss = reconstruction + beta * KL divergence.

    Returns (total_loss, recon_loss, kl_loss).
    """
    recon_loss = F.mse_loss(recon, target, reduction="mean")
    kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    total = recon_loss + beta * kl_loss
    return total, recon_loss, kl_loss


def train_vae(model: CosmologyVAE, maps: np.ndarray,
              n_epochs: int = 50, batch_size: int = 32,
              lr: float = 1e-3, beta: float = 1.0,
              device: str = "cpu") -> list[float]:
    """Train VAE on CMB maps. Returns per-epoch total losses."""
    model = model.to(device)
    model.train()

    if maps.ndim == 3:
        data = torch.from_numpy(maps[:, np.newaxis]).float()
    else:
        data = torch.from_numpy(maps).float()

    dataset = torch.utils.data.TensorDataset(data)
    loader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    losses = []

    for epoch in range(n_epochs):
        epoch_loss = 0.0
        n_batches = 0
        for (batch,) in loader:
            batch = batch.to(device)
            recon, mu, logvar = model(batch)
            loss, _, _ = vae_loss(recon, batch, mu, logvar, beta=beta)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            n_batches += 1
        losses.append(epoch_loss / max(n_batches, 1))

    return losses
