"""Latent space disentanglement analysis.

A disentangled representation is one where each latent dimension
captures a single independent factor of variation. For cosmology:
  - z_0 might encode H0
  - z_1 might encode Omega_m
  - z_2 might encode n_s, etc.

Disentanglement is valuable because it makes the latent space
physically interpretable and enables controlled generation.

Metrics:
- Mutual Information Gap (MIG): how much more informative is
  the best latent dim vs the second-best for each parameter
- Factor-latent correlation matrix
- Traversal analysis: what happens when we move along one axis
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch


@dataclass
class DisentanglementMetrics:
    """Summary metrics for latent space disentanglement."""
    mutual_info_gap: float
    per_factor_scores: dict[str, float]


def compute_mutual_info_gap(
    latent_vectors: np.ndarray,
    parameters: np.ndarray,
    param_names: list[str] | None = None,
) -> DisentanglementMetrics:
    """Compute Mutual Information Gap (MIG).

    For each physical parameter, find the two latent dimensions
    with the highest absolute correlation. MIG = difference between
    the top two. High MIG = good disentanglement (one dim dominates).

    Uses |Pearson correlation| as a proxy for mutual information
    (exact for Gaussian variables, reasonable approximation otherwise).
    """
    n_latent = latent_vectors.shape[1]
    n_params = parameters.shape[1]

    if param_names is None:
        param_names = [f"param_{i}" for i in range(n_params)]

    per_factor = {}
    gaps = []

    for j in range(n_params):
        correlations = []
        for k in range(n_latent):
            c = np.corrcoef(latent_vectors[:, k], parameters[:, j])[0, 1]
            correlations.append(abs(c) if np.isfinite(c) else 0.0)
        sorted_corr = sorted(correlations, reverse=True)
        gap = sorted_corr[0] - sorted_corr[1] if len(sorted_corr) > 1 else sorted_corr[0]
        per_factor[param_names[j]] = gap
        gaps.append(gap)

    return DisentanglementMetrics(
        mutual_info_gap=float(np.mean(gaps)),
        per_factor_scores=per_factor,
    )


def traversal_analysis(
    model,
    base_latent: np.ndarray,
    dim_idx: int,
    n_steps: int = 10,
    range_sigma: float = 3.0,
    device: str = "cpu",
) -> np.ndarray:
    """Traverse one latent dimension while keeping others fixed.

    Generates a sequence of decoded outputs as dim_idx varies
    from -range_sigma to +range_sigma. This visualizes what
    physical change that latent dimension encodes.

    Returns array of shape (n_steps, C, H, W).
    """
    model.eval()
    model = model.to(device)

    z_base = torch.from_numpy(base_latent).float().to(device)
    if z_base.dim() == 1:
        z_base = z_base.unsqueeze(0)

    values = np.linspace(-range_sigma, range_sigma, n_steps)
    outputs = []

    with torch.no_grad():
        for val in values:
            z = z_base.clone()
            z[0, dim_idx] = val
            decoded = model.decode(z)
            outputs.append(decoded.cpu().numpy()[0])

    return np.stack(outputs)


def factor_correlation_matrix(
    latent_vectors: np.ndarray,
    parameters: np.ndarray,
    param_names: list[str] | None = None,
) -> dict:
    """Compute full correlation matrix between latent dims and parameters.

    Returns dict with:
    - correlation_matrix: (n_latent, n_params) Pearson correlations
    - max_corr_per_param: strongest |correlation| for each param
    - best_latent_dim: which latent dim correlates most per param
    """
    n_latent = latent_vectors.shape[1]
    n_params = parameters.shape[1]
    if param_names is None:
        param_names = [f"param_{i}" for i in range(n_params)]

    corr = np.zeros((n_latent, n_params))
    for i in range(n_latent):
        for j in range(n_params):
            c = np.corrcoef(latent_vectors[:, i], parameters[:, j])[0, 1]
            corr[i, j] = c if np.isfinite(c) else 0.0

    return {
        "correlation_matrix": corr,
        "max_corr_per_param": np.max(np.abs(corr), axis=0),
        "best_latent_dim": np.argmax(np.abs(corr), axis=0),
        "param_names": param_names,
    }
