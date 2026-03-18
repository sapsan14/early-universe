"""Latent space analysis for CMB anomaly detection.

After training an autoencoder, the latent space encodes a compressed
representation of CMB maps. Analysis of this space reveals:

1. Clustering — do different cosmologies form distinct clusters?
2. Outliers — which real maps are far from the LCDM training manifold?
3. Dimensionality — how many effective degrees of freedom describe CMB?
4. Trajectories — how does the latent representation change with parameters?
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from archeon.anomaly.autoencoder import CMBAutoencoder


# ---------------------------------------------------------------------------
# Latent extraction
# ---------------------------------------------------------------------------

def extract_latent_vectors(
    model: CMBAutoencoder,
    maps: np.ndarray,
    device: str = "cpu",
) -> np.ndarray:
    """Encode a batch of CMB maps into latent vectors.

    Parameters
    ----------
    model : trained CMBAutoencoder
    maps : array of shape (N, H, W) or (N, 1, H, W)

    Returns
    -------
    latent : array of shape (N, latent_dim)
    """
    model = model.to(device)
    model.eval()

    if maps.ndim == 3:
        maps_t = torch.from_numpy(maps[:, np.newaxis]).float().to(device)
    else:
        maps_t = torch.from_numpy(maps).float().to(device)

    with torch.no_grad():
        z = model.encode(maps_t)

    return z.cpu().numpy()


# ---------------------------------------------------------------------------
# Outlier detection
# ---------------------------------------------------------------------------

@dataclass
class OutlierResult:
    """Results from outlier detection in latent space."""
    distances: np.ndarray          # (N,) distance from training centroid
    is_outlier: np.ndarray         # (N,) bool mask
    threshold: float
    n_outliers: int
    centroid: np.ndarray           # (latent_dim,) training distribution center
    covariance_inv: np.ndarray     # (latent_dim, latent_dim) inverse covariance


def detect_outliers(
    latent_train: np.ndarray,
    latent_test: np.ndarray,
    threshold_sigma: float = 3.0,
) -> OutlierResult:
    """Detect outliers using Mahalanobis distance in latent space.

    Points farther than threshold_sigma from the training centroid
    (in Mahalanobis metric) are flagged as anomalous.

    Mahalanobis distance accounts for correlations between latent
    dimensions — more principled than simple Euclidean distance.
    """
    centroid = latent_train.mean(axis=0)
    centered = latent_train - centroid
    cov = np.cov(centered, rowvar=False)

    # Regularize covariance for numerical stability
    cov += np.eye(cov.shape[0]) * 1e-6
    cov_inv = np.linalg.inv(cov)

    # Mahalanobis distance for test points
    diff = latent_test - centroid
    mahal = np.sqrt(np.sum(diff @ cov_inv * diff, axis=1))

    # Threshold from training distribution
    train_diff = latent_train - centroid
    train_mahal = np.sqrt(np.sum(train_diff @ cov_inv * train_diff, axis=1))
    threshold = float(train_mahal.mean() + threshold_sigma * train_mahal.std())

    is_outlier = mahal > threshold

    return OutlierResult(
        distances=mahal,
        is_outlier=is_outlier,
        threshold=threshold,
        n_outliers=int(is_outlier.sum()),
        centroid=centroid,
        covariance_inv=cov_inv,
    )


# ---------------------------------------------------------------------------
# Dimensionality analysis (PCA of latent space)
# ---------------------------------------------------------------------------

@dataclass
class DimensionalityResult:
    """PCA analysis of latent space."""
    explained_variance_ratio: np.ndarray   # per component
    cumulative_variance: np.ndarray
    effective_dim: int                      # 95% variance threshold
    principal_components: np.ndarray        # (n_components, latent_dim)


def analyze_dimensionality(
    latent_vectors: np.ndarray,
    variance_threshold: float = 0.95,
) -> DimensionalityResult:
    """PCA analysis of latent space.

    How many effective dimensions encode CMB information?
    Low effective_dim means the autoencoder found a compact representation.
    """
    centered = latent_vectors - latent_vectors.mean(axis=0)
    cov = np.cov(centered, rowvar=False)

    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Sort descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    total_var = eigenvalues.sum()
    explained_ratio = eigenvalues / total_var
    cumulative = np.cumsum(explained_ratio)

    effective_dim = int(np.searchsorted(cumulative, variance_threshold) + 1)

    return DimensionalityResult(
        explained_variance_ratio=explained_ratio,
        cumulative_variance=cumulative,
        effective_dim=effective_dim,
        principal_components=eigenvectors.T,
    )


# ---------------------------------------------------------------------------
# t-SNE / UMAP dimensionality reduction for visualization
# ---------------------------------------------------------------------------

def reduce_to_2d(
    latent_vectors: np.ndarray,
    method: str = "pca",
    **kwargs,
) -> np.ndarray:
    """Reduce latent vectors to 2D for visualization.

    Methods:
    - "pca": fast, linear (always available)
    - "tsne": nonlinear, captures local structure (requires sklearn)
    - "umap": nonlinear, preserves global+local structure (requires umap-learn)

    Returns array of shape (N, 2).
    """
    if method == "pca":
        centered = latent_vectors - latent_vectors.mean(axis=0)
        cov = np.cov(centered, rowvar=False)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        idx = np.argsort(eigenvalues)[::-1][:2]
        return centered @ eigenvectors[:, idx]

    elif method == "tsne":
        from sklearn.manifold import TSNE
        perplexity = kwargs.get("perplexity", min(30, len(latent_vectors) - 1))
        tsne = TSNE(n_components=2, perplexity=perplexity,
                     random_state=kwargs.get("seed", 42))
        return tsne.fit_transform(latent_vectors)

    elif method == "umap":
        import umap
        reducer = umap.UMAP(
            n_components=2,
            n_neighbors=kwargs.get("n_neighbors", 15),
            min_dist=kwargs.get("min_dist", 0.1),
            random_state=kwargs.get("seed", 42),
        )
        return reducer.fit_transform(latent_vectors)

    else:
        raise ValueError(f"Unknown method '{method}'. Use 'pca', 'tsne', or 'umap'.")


# ---------------------------------------------------------------------------
# Parameter-latent correlation
# ---------------------------------------------------------------------------

def latent_parameter_correlation(
    latent_vectors: np.ndarray,
    parameters: np.ndarray,
    param_names: list[str] | None = None,
) -> dict[str, np.ndarray]:
    """Compute correlation between latent dimensions and physical parameters.

    High correlation means the autoencoder has learned to encode
    physical information in specific latent dimensions.

    Returns dict with:
    - "correlation_matrix": (latent_dim, n_params) Pearson correlation
    - "max_corr_per_param": (n_params,) strongest correlation for each param
    - "best_latent_dim": (n_params,) which latent dim correlates most
    """
    n_latent = latent_vectors.shape[1]
    n_params = parameters.shape[1]

    corr_matrix = np.zeros((n_latent, n_params))
    for i in range(n_latent):
        for j in range(n_params):
            corr = np.corrcoef(latent_vectors[:, i], parameters[:, j])[0, 1]
            corr_matrix[i, j] = corr if np.isfinite(corr) else 0.0

    max_corr = np.max(np.abs(corr_matrix), axis=0)
    best_dim = np.argmax(np.abs(corr_matrix), axis=0)

    return {
        "correlation_matrix": corr_matrix,
        "max_corr_per_param": max_corr,
        "best_latent_dim": best_dim,
    }
