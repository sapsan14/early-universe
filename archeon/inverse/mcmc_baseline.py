"""MCMC baseline for cosmological parameter inference.

Classical approach: sample the posterior p(theta | data) using
Markov Chain Monte Carlo. This serves as the gold standard
to validate the Bayesian CNN against.

Uses emcee (Foreman-Mackey et al. 2013), an affine-invariant
ensemble sampler — the de facto standard in astrophysics.

The key idea: instead of training a neural network to approximate
the posterior, we directly explore it by evaluating the likelihood
at many parameter points. Accurate but slow (~hours vs milliseconds
for the CNN).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

try:
    import emcee
    HAS_EMCEE = True
except ImportError:
    HAS_EMCEE = False

from archeon.config import get_cosmology, get_constants
from archeon.physics.perturbations import compute_matter_pk


# ---------------------------------------------------------------------------
# Parameter priors (uniform box)
# ---------------------------------------------------------------------------

PARAM_RANGES = {
    "H0":          (60.0, 80.0),
    "Omega_b_h2":  (0.019, 0.025),
    "Omega_cdm_h2": (0.10, 0.14),
    "n_s":         (0.92, 1.02),
    "ln10As":      (2.5, 3.5),
    "tau_reio":    (0.01, 0.12),
}
PARAM_NAMES = list(PARAM_RANGES.keys())
N_PARAMS = len(PARAM_NAMES)


def log_prior(theta: np.ndarray) -> float:
    """Flat (uniform) prior within parameter box. Returns -inf outside."""
    for val, name in zip(theta, PARAM_NAMES):
        lo, hi = PARAM_RANGES[name]
        if val < lo or val > hi:
            return -np.inf
    return 0.0


# ---------------------------------------------------------------------------
# Likelihood: simplified power spectrum comparison
# ---------------------------------------------------------------------------

def params_to_cosmology(theta: np.ndarray) -> dict:
    """Convert parameter vector to cosmology dict."""
    H0, Omega_b_h2, Omega_cdm_h2, n_s, ln10As, tau_reio = theta
    h = H0 / 100.0
    h2 = h**2
    return {
        "H0": H0, "h": h,
        "Omega_b_h2": Omega_b_h2,
        "Omega_cdm_h2": Omega_cdm_h2,
        "Omega_b": Omega_b_h2 / h2,
        "Omega_cdm": Omega_cdm_h2 / h2,
        "Omega_m": (Omega_b_h2 + Omega_cdm_h2) / h2,
        "Omega_r": 9.15e-5,
        "Omega_Lambda": 1.0 - (Omega_b_h2 + Omega_cdm_h2) / h2 - 9.15e-5,
        "n_s": n_s,
        "A_s": np.exp(ln10As) * 1e-10,
        "tau_reio": tau_reio,
    }


def log_likelihood_pk(theta: np.ndarray, k_obs: np.ndarray,
                       pk_obs: np.ndarray, pk_err: np.ndarray) -> float:
    """Gaussian log-likelihood comparing predicted vs observed P(k).

    L = -0.5 * sum [ (P_pred(k) - P_obs(k))^2 / sigma_obs^2 ]
    """
    try:
        cosmo = params_to_cosmology(theta)
        result = compute_matter_pk(cosmo, k_obs)
        pk_pred = result["P_k"]

        residuals = (pk_pred - pk_obs) / pk_err
        return -0.5 * np.sum(residuals**2)
    except Exception:
        return -np.inf


def log_likelihood_cl(theta: np.ndarray, cl_obs: np.ndarray,
                       l_max: int, noise_cl: np.ndarray | None = None) -> float:
    """Gaussian log-likelihood comparing predicted vs observed C_l.

    For CMB power spectrum fitting. Uses simplified C_l computation.
    """
    try:
        from archeon.data.synthetic import compute_cl_internal
        cosmo = params_to_cosmology(theta)
        cl_pred = compute_cl_internal(cosmo, l_max=l_max)

        ells = np.arange(2, len(cl_obs) + 2)
        var = 2.0 / (2.0 * ells + 1.0) * cl_obs**2  # cosmic variance
        if noise_cl is not None:
            var += noise_cl**2

        n = min(len(cl_pred) - 2, len(cl_obs))
        cl_pred_cut = cl_pred[2:2 + n]
        cl_obs_cut = cl_obs[:n]
        var_cut = var[:n]

        mask = var_cut > 0
        residuals = (cl_pred_cut[mask] - cl_obs_cut[mask])**2 / var_cut[mask]
        return -0.5 * np.sum(residuals)
    except Exception:
        return -np.inf


# ---------------------------------------------------------------------------
# Posterior = Prior + Likelihood
# ---------------------------------------------------------------------------

def log_posterior(theta: np.ndarray, log_likelihood_fn: Callable,
                  *likelihood_args) -> float:
    lp = log_prior(theta)
    if not np.isfinite(lp):
        return -np.inf
    ll = log_likelihood_fn(theta, *likelihood_args)
    if not np.isfinite(ll):
        return -np.inf
    return lp + ll


# ---------------------------------------------------------------------------
# MCMC runner
# ---------------------------------------------------------------------------

@dataclass
class MCMCResult:
    """Container for MCMC results."""
    samples: np.ndarray          # (n_steps, n_walkers, n_params)
    flat_samples: np.ndarray     # (n_effective, n_params)
    log_prob: np.ndarray         # (n_steps, n_walkers)
    acceptance_fraction: np.ndarray
    param_names: list[str]
    param_means: np.ndarray
    param_stds: np.ndarray
    param_medians: np.ndarray
    quantiles_16: np.ndarray
    quantiles_84: np.ndarray

    def summary(self) -> str:
        lines = ["MCMC Parameter Estimates:", "=" * 50]
        for i, name in enumerate(self.param_names):
            lines.append(
                f"  {name:>15s}: {self.param_medians[i]:.6f}  "
                f"(+{self.quantiles_84[i] - self.param_medians[i]:.6f}  "
                f"-{self.param_medians[i] - self.quantiles_16[i]:.6f})"
            )
        lines.append(f"  Mean acceptance: {self.acceptance_fraction.mean():.3f}")
        return "\n".join(lines)


def run_mcmc(
    log_likelihood_fn: Callable,
    likelihood_args: tuple = (),
    n_walkers: int = 32,
    n_steps: int = 2000,
    burn_in: int = 500,
    initial_theta: np.ndarray | None = None,
    initial_spread: float = 0.01,
    seed: int | None = None,
    progress: bool = True,
) -> MCMCResult:
    """Run MCMC sampling using emcee.

    Parameters
    ----------
    log_likelihood_fn : callable
        Log-likelihood function: log_likelihood_fn(theta, *likelihood_args).
    likelihood_args : tuple
        Extra arguments passed to the likelihood function.
    n_walkers : int
        Number of ensemble walkers (must be >= 2*n_params).
    n_steps : int
        Total number of MCMC steps.
    burn_in : int
        Number of initial steps to discard (transient before convergence).
    initial_theta : array
        Starting parameter values. If None, uses Planck best-fit.
    initial_spread : float
        Scale of random perturbation around initial_theta for walkers.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    MCMCResult with posterior samples and summary statistics.
    """
    if not HAS_EMCEE:
        raise ImportError("emcee is required: pip install emcee")

    rng = np.random.default_rng(seed)

    if initial_theta is None:
        cosmo = get_cosmology()
        initial_theta = np.array([
            cosmo["H0"],
            cosmo["Omega_b_h2"],
            cosmo["Omega_cdm_h2"],
            cosmo["n_s"],
            np.log(cosmo["A_s"] * 1e10),
            cosmo["tau_reio"],
        ])

    n_dim = len(initial_theta)
    n_walkers = max(n_walkers, 2 * n_dim + 2)

    # Initialize walkers in a small ball around the initial point
    pos = initial_theta + initial_spread * rng.standard_normal((n_walkers, n_dim))

    # Clamp to prior bounds
    for i, name in enumerate(PARAM_NAMES):
        lo, hi = PARAM_RANGES[name]
        pos[:, i] = np.clip(pos[:, i], lo + 1e-6, hi - 1e-6)

    sampler = emcee.EnsembleSampler(
        n_walkers, n_dim, log_posterior,
        args=(log_likelihood_fn, *likelihood_args),
    )

    sampler.run_mcmc(pos, n_steps, progress=progress)

    chain = sampler.get_chain()                  # (n_steps, n_walkers, n_dim)
    log_prob = sampler.get_log_prob()             # (n_steps, n_walkers)
    flat = sampler.get_chain(discard=burn_in, flat=True)  # (n_effective, n_dim)

    return MCMCResult(
        samples=chain,
        flat_samples=flat,
        log_prob=log_prob,
        acceptance_fraction=sampler.acceptance_fraction,
        param_names=PARAM_NAMES,
        param_means=flat.mean(axis=0),
        param_stds=flat.std(axis=0),
        param_medians=np.median(flat, axis=0),
        quantiles_16=np.percentile(flat, 16, axis=0),
        quantiles_84=np.percentile(flat, 84, axis=0),
    )


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def plot_corner(result: MCMCResult, truths: np.ndarray | None = None,
                filename: str | None = None):
    """Corner plot of posterior samples (requires corner package)."""
    try:
        import corner
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("corner and matplotlib required for plotting")

    fig = corner.corner(
        result.flat_samples,
        labels=result.param_names,
        truths=truths,
        quantiles=[0.16, 0.5, 0.84],
        show_titles=True,
        title_kwargs={"fontsize": 10},
    )
    if filename:
        fig.savefig(filename, dpi=150, bbox_inches="tight")
    return fig


def plot_chains(result: MCMCResult, filename: str | None = None):
    """Trace plots for all parameters (convergence diagnostic)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required for plotting")

    fig, axes = plt.subplots(N_PARAMS, 1, figsize=(10, 2 * N_PARAMS), sharex=True)
    for i, (ax, name) in enumerate(zip(axes, result.param_names)):
        ax.plot(result.samples[:, :, i], alpha=0.3, lw=0.5)
        ax.set_ylabel(name)
    axes[-1].set_xlabel("Step")
    fig.tight_layout()
    if filename:
        fig.savefig(filename, dpi=150, bbox_inches="tight")
    return fig
