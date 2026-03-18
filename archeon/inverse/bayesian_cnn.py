"""Bayesian CNN for cosmological parameter inference from CMB maps.

The core of inverse cosmology: given a CMB temperature map,
predict the cosmological parameters that generated it, WITH
calibrated uncertainty estimates.

Architecture:
  Input: 2D flat-sky CMB patch (128x128 or 64x64 pixels)
  Encoder: ResNet-style convolutional backbone
  Output heads:
    - mu_head: predicted parameter means (6 values)
    - log_sigma_head: predicted log-uncertainties (6 values)

Loss function (heteroscedastic Gaussian NLL):
  L = sum_i [ (theta_true_i - mu_i)^2 / sigma_i^2 + log(sigma_i^2) ]

The model learns BOTH the prediction AND how uncertain it is about
each prediction — a crucial property for scientific applications.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Parameter names (output ordering)
# ---------------------------------------------------------------------------

PARAM_NAMES = ["H0", "Omega_b_h2", "Omega_cdm_h2", "n_s", "ln10As", "tau_reio"]
N_PARAMS = len(PARAM_NAMES)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class ResidualBlock(nn.Module):
    """Residual block with two conv layers and skip connection.

    Skip connections allow training deeper networks by providing
    gradient highways — essential for the subtle patterns in CMB maps.
    """

    def __init__(self, channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return F.relu(out + residual)


class DownBlock(nn.Module):
    """Downsampling block: increase channels, reduce spatial dims by 2."""

    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, 3, stride=2, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(out_ch)
        self.res = ResidualBlock(out_ch)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.bn(self.conv(x)))
        return self.res(x)


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------

class BayesianCosmologyCNN(nn.Module):
    """Bayesian CNN for cosmological parameter inference.

    Takes a 1-channel 2D CMB map patch and outputs:
      - mu: predicted parameter means (N_PARAMS,)
      - log_sigma: log predicted uncertainties (N_PARAMS,)

    The log_sigma output enables heteroscedastic uncertainty:
    the model can be MORE uncertain about some parameters than others,
    and MORE uncertain for some inputs than others.

    Parameters
    ----------
    input_size : int
        Spatial size of input (input_size x input_size).
    base_channels : int
        Number of channels in first conv layer (doubles each block).
    n_params : int
        Number of output parameters.
    dropout_rate : float
        Dropout rate (used for MC Dropout uncertainty estimation).
    """

    def __init__(self, input_size: int = 128, base_channels: int = 32,
                 n_params: int = N_PARAMS, dropout_rate: float = 0.1):
        super().__init__()
        self.n_params = n_params
        self.dropout_rate = dropout_rate

        c = base_channels
        self.stem = nn.Sequential(
            nn.Conv2d(1, c, 5, stride=1, padding=2, bias=False),
            nn.BatchNorm2d(c),
            nn.ReLU(),
        )

        self.encoder = nn.Sequential(
            DownBlock(c, c * 2),       # /2
            DownBlock(c * 2, c * 4),   # /4
            DownBlock(c * 4, c * 8),   # /8
            DownBlock(c * 8, c * 16),  # /16
        )

        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(dropout_rate)

        feat_dim = c * 16

        self.shared_fc = nn.Sequential(
            nn.Linear(feat_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
        )

        self.mu_head = nn.Linear(128, n_params)
        self.log_sigma_head = nn.Linear(128, n_params)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

        # Initialize log_sigma bias to moderate uncertainty
        nn.init.constant_(self.log_sigma_head.bias, -1.0)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Parameters
        ----------
        x : tensor of shape (batch, 1, H, W)
            CMB map patches.

        Returns
        -------
        mu : tensor of shape (batch, n_params)
            Predicted parameter means.
        log_sigma : tensor of shape (batch, n_params)
            Predicted log-uncertainties. sigma = exp(log_sigma).
        """
        features = self.stem(x)
        features = self.encoder(features)
        pooled = self.global_pool(features).flatten(1)
        pooled = self.dropout(pooled)

        shared = self.shared_fc(pooled)
        mu = self.mu_head(shared)
        log_sigma = self.log_sigma_head(shared)

        # Clamp log_sigma to prevent numerical instability
        log_sigma = torch.clamp(log_sigma, min=-10.0, max=5.0)

        return mu, log_sigma

    def predict_with_uncertainty(self, x: torch.Tensor,
                                 n_samples: int = 50) -> dict[str, torch.Tensor]:
        """MC Dropout prediction: run N forward passes with dropout enabled.

        Returns the mean prediction and both aleatoric and epistemic uncertainty.

        Aleatoric uncertainty: inherent data noise (from log_sigma output)
        Epistemic uncertainty: model uncertainty (from dropout variation)
        """
        self.train()  # keep dropout active

        mus = []
        log_sigmas = []

        with torch.no_grad():
            for _ in range(n_samples):
                mu, log_sigma = self(x)
                mus.append(mu)
                log_sigmas.append(log_sigma)

        mus = torch.stack(mus)             # (n_samples, batch, n_params)
        log_sigmas = torch.stack(log_sigmas)

        mu_mean = mus.mean(dim=0)
        epistemic = mus.var(dim=0)
        aleatoric = torch.exp(2 * log_sigmas).mean(dim=0)
        total_uncertainty = epistemic + aleatoric

        return {
            "mu": mu_mean,
            "epistemic_var": epistemic,
            "aleatoric_var": aleatoric,
            "total_var": total_uncertainty,
            "sigma": torch.sqrt(total_uncertainty),
        }


# ---------------------------------------------------------------------------
# Loss function
# ---------------------------------------------------------------------------

class HeteroscedasticGaussianNLL(nn.Module):
    """Heteroscedastic Gaussian negative log-likelihood loss.

    L = sum_i [ (y_i - mu_i)^2 / (2*sigma_i^2) + 0.5*log(sigma_i^2) ]

    This loss naturally balances accuracy vs. overconfidence:
    - The first term penalizes wrong predictions (weighted by certainty)
    - The second term penalizes excessive uncertainty (can't just say "I don't know")

    The model learns to output larger sigma for harder examples.
    """

    def forward(self, mu: torch.Tensor, log_sigma: torch.Tensor,
                target: torch.Tensor) -> torch.Tensor:
        sigma_sq = torch.exp(2 * log_sigma)
        nll = 0.5 * ((target - mu)**2 / sigma_sq + 2 * log_sigma)
        return nll.mean()


# ---------------------------------------------------------------------------
# Lightweight model for quick experiments
# ---------------------------------------------------------------------------

class CosmologyMLP(nn.Module):
    """Simple MLP baseline for parameter inference from power spectrum.

    Input: C_l vector (instead of map) — much simpler, faster to train.
    Useful as a sanity check before the full CNN.
    """

    def __init__(self, input_dim: int = 191, n_params: int = N_PARAMS,
                 hidden: int = 256, dropout: float = 0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.mu_head = nn.Linear(hidden // 2, n_params)
        self.log_sigma_head = nn.Linear(hidden // 2, n_params)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.net(x)
        return self.mu_head(h), torch.clamp(self.log_sigma_head(h), -10, 5)
