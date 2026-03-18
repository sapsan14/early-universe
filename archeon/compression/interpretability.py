"""Physical interpretation of VAE latent space.

The ultimate goal: map each latent dimension to a physical meaning.
If z_3 strongly correlates with H0 and z_7 with Omega_m, the VAE
has independently discovered these as the key degrees of freedom.

More interesting: latent dims that correlate with COMBINATIONS
of parameters may reveal hidden physical relationships not obvious
from the equations alone.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class LatentInterpretation:
    """Physical interpretation of one latent dimension."""
    dim_idx: int
    best_param: str
    correlation: float
    description: str


def interpret_latent_space(
    latent_vectors: np.ndarray,
    parameters: np.ndarray,
    param_names: list[str],
) -> list[LatentInterpretation]:
    """For each latent dimension, find the strongest-correlated parameter.

    Returns a sorted list (by |correlation|, descending) of interpretations.
    """
    n_latent = latent_vectors.shape[1]
    n_params = parameters.shape[1]

    interpretations = []

    for i in range(n_latent):
        best_corr = 0.0
        best_param = "unknown"
        for j in range(n_params):
            c = np.corrcoef(latent_vectors[:, i], parameters[:, j])[0, 1]
            if np.isfinite(c) and abs(c) > abs(best_corr):
                best_corr = c
                best_param = param_names[j]

        if abs(best_corr) > 0.5:
            desc = f"Strongly encodes {best_param} (r={best_corr:.3f})"
        elif abs(best_corr) > 0.3:
            desc = f"Moderately encodes {best_param} (r={best_corr:.3f})"
        else:
            desc = f"Weakly associated with {best_param} (r={best_corr:.3f})"

        interpretations.append(LatentInterpretation(
            dim_idx=i,
            best_param=best_param,
            correlation=float(best_corr),
            description=desc,
        ))

    interpretations.sort(key=lambda x: abs(x.correlation), reverse=True)
    return interpretations


def latent_space_summary(interpretations: list[LatentInterpretation]) -> str:
    """Human-readable summary of latent space interpretation."""
    lines = ["Latent Space Interpretation", "=" * 50]

    strong = [x for x in interpretations if abs(x.correlation) > 0.5]
    moderate = [x for x in interpretations if 0.3 < abs(x.correlation) <= 0.5]
    weak = [x for x in interpretations if abs(x.correlation) <= 0.3]

    if strong:
        lines.append(f"\nStrongly interpretable ({len(strong)} dims):")
        for x in strong:
            lines.append(f"  z_{x.dim_idx} -> {x.best_param} (r={x.correlation:+.3f})")

    if moderate:
        lines.append(f"\nModerately interpretable ({len(moderate)} dims):")
        for x in moderate:
            lines.append(f"  z_{x.dim_idx} -> {x.best_param} (r={x.correlation:+.3f})")

    if weak:
        lines.append(f"\n  + {len(weak)} weakly associated dimensions")

    return "\n".join(lines)


def find_hidden_correlations(
    latent_vectors: np.ndarray,
    parameters: np.ndarray,
    param_names: list[str],
    threshold: float = 0.3,
) -> list[dict]:
    """Find latent dims that encode COMBINATIONS of physical parameters.

    Uses multiple linear regression: for each latent dim, regress
    on all physical params. If R^2 is much higher than the single
    best correlation, the dim encodes a parameter combination.

    These are the scientifically most interesting findings:
    they may reveal hidden relationships in cosmology.
    """
    n_latent = latent_vectors.shape[1]
    n_params = parameters.shape[1]

    results = []

    for i in range(n_latent):
        z_i = latent_vectors[:, i]

        # Single best correlation
        single_corrs = []
        for j in range(n_params):
            c = np.corrcoef(z_i, parameters[:, j])[0, 1]
            single_corrs.append(c if np.isfinite(c) else 0.0)
        best_single_r2 = max(c**2 for c in single_corrs)

        # Multiple regression R^2
        X = parameters - parameters.mean(axis=0)
        X_aug = np.column_stack([X, np.ones(len(X))])
        try:
            beta, _, _, _ = np.linalg.lstsq(X_aug, z_i, rcond=None)
            pred = X_aug @ beta
            ss_res = np.sum((z_i - pred)**2)
            ss_tot = np.sum((z_i - z_i.mean())**2)
            multi_r2 = 1.0 - ss_res / (ss_tot + 1e-30)
        except np.linalg.LinAlgError:
            multi_r2 = best_single_r2

        improvement = multi_r2 - best_single_r2

        if improvement > threshold and multi_r2 > 0.3:
            # Find which params contribute
            contributing = []
            for j in range(n_params):
                if abs(single_corrs[j]) > 0.15:
                    contributing.append(param_names[j])

            results.append({
                "dim_idx": i,
                "single_best_r2": float(best_single_r2),
                "multi_r2": float(multi_r2),
                "improvement": float(improvement),
                "contributing_params": contributing,
                "description": (
                    f"z_{i} encodes combination of "
                    f"{', '.join(contributing)} "
                    f"(R2: {best_single_r2:.3f} -> {multi_r2:.3f})"
                ),
            })

    results.sort(key=lambda x: x["improvement"], reverse=True)
    return results
