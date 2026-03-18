"""Prior distributions for cosmological parameters.

When generating synthetic training data for inverse cosmology, we need to
sample cosmological parameters theta from a prior distribution p(theta).

The priors should:
1. Cover the physically plausible range
2. Be broad enough to include alternatives to LCDM
3. Center roughly around Planck 2018 best-fit values
4. Support both uniform and Gaussian sampling strategies

Standard parameter set (6 LCDM parameters):
  - H0:         Hubble constant [km/s/Mpc]
  - Omega_b_h2: Baryon density * h^2
  - Omega_cdm_h2: CDM density * h^2
  - n_s:        Scalar spectral index
  - A_s:        Scalar amplitude (or ln(10^10 A_s))
  - tau_reio:   Optical depth to reionization
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple

import numpy as np


class ParameterRange(NamedTuple):
    """Range for a single cosmological parameter."""
    name: str
    symbol: str
    min: float
    max: float
    fiducial: float    # Planck 2018 best-fit
    unit: str = ""


# ---------------------------------------------------------------------------
# Standard 6-parameter LCDM prior ranges
# ---------------------------------------------------------------------------

LCDM_PRIORS = {
    "H0": ParameterRange(
        name="Hubble constant",
        symbol="H_0",
        min=55.0, max=85.0, fiducial=67.36,
        unit="km/s/Mpc",
    ),
    "Omega_b_h2": ParameterRange(
        name="Baryon density",
        symbol="Omega_b h^2",
        min=0.019, max=0.026, fiducial=0.02237,
    ),
    "Omega_cdm_h2": ParameterRange(
        name="CDM density",
        symbol="Omega_cdm h^2",
        min=0.095, max=0.145, fiducial=0.1200,
    ),
    "n_s": ParameterRange(
        name="Scalar spectral index",
        symbol="n_s",
        min=0.90, max=1.05, fiducial=0.9649,
    ),
    "ln10As": ParameterRange(
        name="Log scalar amplitude",
        symbol="ln(10^{10} A_s)",
        min=2.5, max=3.7, fiducial=3.044,
    ),
    "tau_reio": ParameterRange(
        name="Reionization optical depth",
        symbol="tau_{reio}",
        min=0.01, max=0.12, fiducial=0.0544,
    ),
}

# Derived Omega parameters (computed from the 6 base parameters)
DERIVED_PARAMS = {
    "Omega_m": ParameterRange("Matter fraction", "Omega_m", 0.1, 0.6, 0.3153),
    "Omega_Lambda": ParameterRange("Dark energy fraction", "Omega_Lambda", 0.4, 0.9, 0.6847),
    "sigma_8": ParameterRange("Clustering amplitude", "sigma_8", 0.6, 1.0, 0.8111),
}


# ---------------------------------------------------------------------------
# Sampling strategies
# ---------------------------------------------------------------------------

def sample_uniform(n_samples: int,
                   params: dict[str, ParameterRange] | None = None,
                   seed: int | None = None) -> dict[str, np.ndarray]:
    """Sample parameters uniformly within prior ranges.

    Simple and unbiased — good for initial exploration, but inefficient
    for high-dimensional spaces (most samples land in low-likelihood regions).

    Parameters
    ----------
    n_samples : int
        Number of parameter sets to generate.
    params : dict, optional
        Parameter ranges. Default: LCDM_PRIORS.
    seed : int, optional
        Random seed.

    Returns
    -------
    dict mapping parameter name -> array of shape (n_samples,)
    """
    if params is None:
        params = LCDM_PRIORS
    rng = np.random.default_rng(seed)

    samples = {}
    for name, pr in params.items():
        samples[name] = rng.uniform(pr.min, pr.max, size=n_samples)
    return samples


def sample_gaussian(n_samples: int,
                    params: dict[str, ParameterRange] | None = None,
                    sigma_factor: float = 5.0,
                    seed: int | None = None) -> dict[str, np.ndarray]:
    """Sample parameters from Gaussian centered on fiducial values.

    Sigma is set so that the prior range covers ~sigma_factor sigmas.
    Samples outside [min, max] are clipped. Concentrates samples near
    the physically interesting region.

    Parameters
    ----------
    n_samples : int
    params : dict, optional
    sigma_factor : float
        Number of sigmas spanning the prior range.
    seed : int, optional

    Returns
    -------
    dict mapping parameter name -> array of shape (n_samples,)
    """
    if params is None:
        params = LCDM_PRIORS
    rng = np.random.default_rng(seed)

    samples = {}
    for name, pr in params.items():
        sigma = (pr.max - pr.min) / (2.0 * sigma_factor)
        raw = rng.normal(loc=pr.fiducial, scale=sigma, size=n_samples)
        samples[name] = np.clip(raw, pr.min, pr.max)
    return samples


def latin_hypercube_sample(n_samples: int,
                           params: dict[str, ParameterRange] | None = None,
                           seed: int | None = None) -> dict[str, np.ndarray]:
    """Latin Hypercube Sampling (LHS) for space-filling coverage.

    Divides each parameter range into n_samples equal strata and places
    exactly one sample in each stratum. Guarantees uniform marginal
    distributions and much better coverage than random sampling.

    This is the recommended strategy for generating training data
    for emulators and neural surrogates (used by cosmopower, CAMB, etc.).

    Parameters
    ----------
    n_samples : int
    params : dict, optional
    seed : int, optional

    Returns
    -------
    dict mapping parameter name -> array of shape (n_samples,)
    """
    if params is None:
        params = LCDM_PRIORS
    rng = np.random.default_rng(seed)
    n_params = len(params)

    # Generate LHS in [0, 1]^d
    result = np.zeros((n_samples, n_params))
    for j in range(n_params):
        perm = rng.permutation(n_samples)
        for i in range(n_samples):
            result[perm[i], j] = (i + rng.random()) / n_samples

    # Scale to parameter ranges
    samples = {}
    for j, (name, pr) in enumerate(params.items()):
        samples[name] = pr.min + result[:, j] * (pr.max - pr.min)
    return samples


# ---------------------------------------------------------------------------
# Derived parameter computation
# ---------------------------------------------------------------------------

def compute_derived(theta: dict[str, np.ndarray | float]) -> dict[str, np.ndarray | float]:
    """Compute derived cosmological parameters from base parameters.

    Converts from the 6 base LCDM parameters to the physically
    intuitive Omega parameters used in the Friedmann solver.
    """
    h = np.asarray(theta["H0"]) / 100.0
    h2 = h**2

    Omega_b = np.asarray(theta["Omega_b_h2"]) / h2
    Omega_cdm = np.asarray(theta["Omega_cdm_h2"]) / h2
    Omega_m = Omega_b + Omega_cdm

    ln10As = np.asarray(theta["ln10As"])
    A_s = np.exp(ln10As) * 1e-10

    # Radiation density (photons + 3 massless neutrinos)
    T_cmb = 2.7255
    Omega_gamma = 2.469e-5 / h2  # photon density
    N_eff = 3.046
    Omega_nu = N_eff * 7.0 / 8.0 * (4.0 / 11.0) ** (4.0 / 3.0) * Omega_gamma
    Omega_r = Omega_gamma + Omega_nu

    Omega_Lambda = 1.0 - Omega_m - Omega_r  # flat universe assumption

    return {
        "h": h,
        "Omega_b": Omega_b,
        "Omega_cdm": Omega_cdm,
        "Omega_m": Omega_m,
        "Omega_Lambda": Omega_Lambda,
        "Omega_r": Omega_r,
        "A_s": A_s,
        "n_s": np.asarray(theta["n_s"]),
        "tau_reio": np.asarray(theta["tau_reio"]),
        "H0": np.asarray(theta["H0"]),
    }


# ---------------------------------------------------------------------------
# Convenience: generate a complete parameter set
# ---------------------------------------------------------------------------

def generate_parameter_sets(n_samples: int,
                            method: str = "lhs",
                            seed: int | None = None) -> dict[str, np.ndarray]:
    """Generate n_samples parameter sets with derived quantities.

    Parameters
    ----------
    n_samples : int
    method : str
        "uniform", "gaussian", or "lhs" (Latin Hypercube).
    seed : int, optional

    Returns
    -------
    dict with both base and derived parameters.
    """
    samplers = {
        "uniform": sample_uniform,
        "gaussian": sample_gaussian,
        "lhs": latin_hypercube_sample,
    }
    if method not in samplers:
        raise ValueError(f"Unknown method '{method}'. Use: {list(samplers.keys())}")

    base = samplers[method](n_samples, seed=seed)
    derived = compute_derived(base)
    return {**base, **derived}
