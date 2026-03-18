"""Inflationary models: slow-roll dynamics and primordial spectra.

Inflation is a period of exponential expansion in the very early universe
(t ~ 10^{-36} to 10^{-32} seconds) that solves the horizon, flatness,
and monopole problems. Quantum fluctuations during inflation are stretched
to cosmic scales and become the seeds of all structure.

The dynamics are governed by a scalar field (inflaton) phi rolling down
a potential V(phi). The slow-roll approximation gives analytical predictions
for the primordial power spectra of scalar and tensor perturbations.

Implemented models:
1. Quadratic (chaotic): V = m^2 phi^2 / 2
2. Starobinsky R^2: V = Lambda^4 (1 - exp(-sqrt(2/3) phi/M_Pl))^2
3. Natural inflation: V = Lambda^4 (1 + cos(phi/f))
4. Power-law: V = V0 * (phi/M_Pl)^p
"""

from __future__ import annotations

from functools import partial
from typing import NamedTuple

import jax.numpy as jnp
from jax import jit


class SlowRollParams(NamedTuple):
    """Slow-roll parameters at horizon crossing."""
    epsilon: float   # First slow-roll parameter: epsilon = (M_Pl^2/2)(V'/V)^2
    eta: float       # Second slow-roll parameter: eta = M_Pl^2 * V''/V
    n_s: float       # Scalar spectral index: n_s = 1 - 6*epsilon + 2*eta
    r: float         # Tensor-to-scalar ratio: r = 16*epsilon
    n_t: float       # Tensor spectral index: n_t = -2*epsilon (consistency)
    N_efolds: float  # Number of e-folds remaining when mode exits horizon


# ---------------------------------------------------------------------------
# Slow-roll parameters (general)
# ---------------------------------------------------------------------------

@jit
def slow_roll_epsilon(V: float, dV: float, M_Pl: float = 1.0) -> float:
    """First slow-roll parameter: epsilon = (M_Pl^2 / 2) * (V'/V)^2.

    epsilon << 1 means the field rolls slowly (kinetic << potential energy).
    Inflation ends when epsilon ~ 1.
    """
    return 0.5 * M_Pl**2 * (dV / V)**2


@jit
def slow_roll_eta(V: float, d2V: float, M_Pl: float = 1.0) -> float:
    """Second slow-roll parameter: eta = M_Pl^2 * V''/V.

    |eta| << 1 ensures the acceleration of the field is small.
    """
    return M_Pl**2 * d2V / V


@jit
def spectral_index(epsilon: float, eta: float) -> float:
    """Scalar spectral index: n_s = 1 - 6*epsilon + 2*eta.

    Planck 2018: n_s = 0.9649 ± 0.0042 (red tilt, as inflation predicts).
    """
    return 1.0 - 6.0 * epsilon + 2.0 * eta


@jit
def tensor_to_scalar_ratio(epsilon: float) -> float:
    """Tensor-to-scalar ratio: r = 16*epsilon.

    Planck+BICEP2/Keck 2021: r < 0.036 (95% CL).
    """
    return 16.0 * epsilon


# ---------------------------------------------------------------------------
# Model 1: Quadratic (chaotic) inflation V = m^2 phi^2 / 2
# ---------------------------------------------------------------------------

@jit
def quadratic_potential(phi: jnp.ndarray, m: float) -> jnp.ndarray:
    """V(phi) = m^2 * phi^2 / 2."""
    return 0.5 * m**2 * phi**2


@jit
def quadratic_slow_roll(N: float) -> SlowRollParams:
    """Slow-roll parameters for V = m^2 phi^2 / 2 as a function of N e-folds.

    For this model: epsilon = eta = 1/(2N+1), n_s = 1 - 2/N, r = 8/N.
    With N ~ 55-60: n_s ~ 0.964-0.967 (good fit!), r ~ 0.13-0.15 (borderline).
    """
    epsilon = 1.0 / (2.0 * N + 1.0)
    eta = epsilon
    n_s = spectral_index(epsilon, eta)
    r = tensor_to_scalar_ratio(epsilon)
    n_t = -2.0 * epsilon
    return SlowRollParams(epsilon=epsilon, eta=eta, n_s=n_s, r=r, n_t=n_t, N_efolds=N)


# ---------------------------------------------------------------------------
# Model 2: Starobinsky R^2 inflation
# V = (3/4) M_Pl^2 m^2 [1 - exp(-sqrt(2/3) phi/M_Pl)]^2
# ---------------------------------------------------------------------------

@jit
def starobinsky_potential(phi: jnp.ndarray, m: float,
                          M_Pl: float = 1.0) -> jnp.ndarray:
    """Starobinsky R^2 potential in the Einstein frame.

    V(phi) = (3/4) M_Pl^2 m^2 [1 - exp(-sqrt(2/3) phi/M_Pl)]^2

    Originates from f(R) = R + R^2/(6M^2) gravity.
    """
    x = jnp.exp(-jnp.sqrt(2.0 / 3.0) * phi / M_Pl)
    return 0.75 * M_Pl**2 * m**2 * (1.0 - x)**2


@jit
def starobinsky_slow_roll(N: float) -> SlowRollParams:
    """Slow-roll parameters for Starobinsky R^2 model.

    epsilon ~ 3/(4*N^2), eta ~ -1/N.
    n_s ~ 1 - 2/N, r ~ 12/N^2.

    With N ~ 55: n_s ~ 0.964, r ~ 0.004 — excellent fit to Planck data.
    This is currently the "gold standard" model.
    """
    epsilon = 3.0 / (4.0 * N**2)
    eta = -1.0 / N
    n_s = spectral_index(epsilon, eta)
    r = tensor_to_scalar_ratio(epsilon)
    n_t = -2.0 * epsilon
    return SlowRollParams(epsilon=epsilon, eta=eta, n_s=n_s, r=r, n_t=n_t, N_efolds=N)


# ---------------------------------------------------------------------------
# Model 3: Natural inflation V = Lambda^4 [1 + cos(phi/f)]
# ---------------------------------------------------------------------------

@jit
def natural_potential(phi: jnp.ndarray, Lambda4: float,
                      f: float) -> jnp.ndarray:
    """Natural inflation potential: V = Lambda^4 * [1 + cos(phi/f)].

    f is the axion decay constant. Requires f > M_Pl for sufficient inflation.
    """
    return Lambda4 * (1.0 + jnp.cos(phi / f))


@jit
def natural_slow_roll(N: float, f: float, M_Pl: float = 1.0) -> SlowRollParams:
    """Slow-roll for natural inflation (approximate for large f/M_Pl)."""
    x = M_Pl**2 / (2.0 * f**2)
    epsilon = x / (N + 0.5 / x)
    eta = -x * (2.0 * N * x - 1.0) / (N + 0.5 / x)
    n_s = spectral_index(epsilon, eta)
    r = tensor_to_scalar_ratio(epsilon)
    n_t = -2.0 * epsilon
    return SlowRollParams(epsilon=epsilon, eta=eta, n_s=n_s, r=r, n_t=n_t, N_efolds=N)


# ---------------------------------------------------------------------------
# Model 4: Power-law potential V = V0 * (phi/M_Pl)^p
# ---------------------------------------------------------------------------

@jit
def power_law_potential(phi: jnp.ndarray, V0: float,
                        p: float, M_Pl: float = 1.0) -> jnp.ndarray:
    """Power-law potential V = V0 * (phi/M_Pl)^p."""
    return V0 * (phi / M_Pl)**p


@jit
def power_law_slow_roll(N: float, p: float) -> SlowRollParams:
    """Slow-roll for power-law potential V ~ phi^p.

    epsilon = p / (4*N + p), eta = (p-1) / (2*N + p/2).
    """
    epsilon = p / (4.0 * N + p)
    eta = (p - 1.0) / (2.0 * N + p / 2.0)
    n_s = spectral_index(epsilon, eta)
    r = tensor_to_scalar_ratio(epsilon)
    n_t = -2.0 * epsilon
    return SlowRollParams(epsilon=epsilon, eta=eta, n_s=n_s, r=r, n_t=n_t, N_efolds=N)


# ---------------------------------------------------------------------------
# Primordial power spectra
# ---------------------------------------------------------------------------

@jit
def scalar_power_spectrum(k: jnp.ndarray, A_s: float,
                          n_s: float, k_pivot: float) -> jnp.ndarray:
    """Primordial scalar power spectrum P_s(k) = A_s * (k/k_pivot)^{n_s - 1}."""
    return A_s * (k / k_pivot) ** (n_s - 1.0)


@jit
def tensor_power_spectrum(k: jnp.ndarray, A_s: float,
                          r: float, n_t: float,
                          k_pivot: float) -> jnp.ndarray:
    """Primordial tensor (gravitational wave) power spectrum.

    P_t(k) = r * A_s * (k/k_pivot)^{n_t}

    Tensor perturbations produce B-mode polarization in the CMB —
    the "smoking gun" of inflation (not yet detected).
    """
    A_t = r * A_s
    return A_t * (k / k_pivot) ** n_t


# ---------------------------------------------------------------------------
# Number of e-folds from field value
# ---------------------------------------------------------------------------

@jit
def efolds_quadratic(phi_init: float, phi_end: float,
                     M_Pl: float = 1.0) -> float:
    """N e-folds for quadratic potential: N = (phi_i^2 - phi_e^2) / (4 M_Pl^2).

    Inflation ends when epsilon=1, i.e. phi_end = sqrt(2) * M_Pl.
    """
    return (phi_init**2 - phi_end**2) / (4.0 * M_Pl**2)


@jit
def efolds_starobinsky(phi_init: float, M_Pl: float = 1.0) -> float:
    """Approximate N e-folds for Starobinsky model (large phi regime).

    N ~ (3/4) * exp(sqrt(2/3) * phi/M_Pl)
    """
    return 0.75 * jnp.exp(jnp.sqrt(2.0 / 3.0) * phi_init / M_Pl)


# ---------------------------------------------------------------------------
# Convenience: compare models
# ---------------------------------------------------------------------------

def compare_models(N: float = 55.0) -> dict[str, SlowRollParams]:
    """Compare slow-roll predictions of all implemented models at N e-folds.

    Returns a dictionary of model_name -> SlowRollParams.
    """
    return {
        "quadratic": quadratic_slow_roll(N),
        "starobinsky": starobinsky_slow_roll(N),
        "natural_f5": natural_slow_roll(N, f=5.0),
        "natural_f10": natural_slow_roll(N, f=10.0),
        "linear_p1": power_law_slow_roll(N, p=1.0),
        "cubic_p3": power_law_slow_roll(N, p=3.0),
    }
