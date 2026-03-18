"""Friedmann equation solver on JAX.

Solves the first Friedmann equation:

    H^2(a) = H0^2 [ Omega_r/a^4 + Omega_m/a^3 + Omega_k/a^2 + Omega_Lambda ]

Provides: H(a), H(z), cosmic time t(a), conformal time eta(a),
comoving distance chi(z), luminosity distance d_L(z), angular diameter distance d_A(z),
age of the universe.
"""

from __future__ import annotations

from functools import partial
from typing import NamedTuple

import jax
import jax.numpy as jnp
from jax import jit

from archeon.config import get_constants, get_cosmology


class CosmologicalParams(NamedTuple):
    """Minimal set of cosmological parameters for background evolution."""

    H0: float          # Hubble constant [km/s/Mpc]
    Omega_m: float     # Total matter fraction
    Omega_r: float     # Radiation fraction
    Omega_Lambda: float  # Dark energy fraction
    Omega_k: float     # Curvature


def params_from_config(name: str = "planck2018") -> CosmologicalParams:
    """Build CosmologicalParams from a YAML config."""
    c = get_cosmology(name)
    return CosmologicalParams(
        H0=c["H0"],
        Omega_m=c["Omega_m"],
        Omega_r=c["Omega_r"],
        Omega_Lambda=c["Omega_Lambda"],
        Omega_k=c["Omega_k"],
    )


# ---------------------------------------------------------------------------
# Core functions — all JIT-compiled, differentiable, and vmap-compatible
# ---------------------------------------------------------------------------

@jit
def E_squared(a: jnp.ndarray, Omega_m: float, Omega_r: float,
              Omega_Lambda: float, Omega_k: float) -> jnp.ndarray:
    """Dimensionless Hubble function squared: E^2(a) = H^2(a)/H0^2.

    Each term represents a component of the universe's energy budget
    diluting at a different rate as the universe expands:
      - Radiation ~ a^{-4}  (dilution + redshift of wavelength)
      - Matter    ~ a^{-3}  (dilution only)
      - Curvature ~ a^{-2}
      - Lambda    ~ const   (vacuum energy density is constant)
    """
    return Omega_r / a**4 + Omega_m / a**3 + Omega_k / a**2 + Omega_Lambda


@jit
def hubble(a: jnp.ndarray, H0: float, Omega_m: float, Omega_r: float,
           Omega_Lambda: float, Omega_k: float) -> jnp.ndarray:
    """Hubble parameter H(a) in km/s/Mpc."""
    return H0 * jnp.sqrt(E_squared(a, Omega_m, Omega_r, Omega_Lambda, Omega_k))


@jit
def hubble_from_z(z: jnp.ndarray, H0: float, Omega_m: float, Omega_r: float,
                  Omega_Lambda: float, Omega_k: float) -> jnp.ndarray:
    """Hubble parameter H(z) in km/s/Mpc. Relation: a = 1/(1+z)."""
    a = 1.0 / (1.0 + z)
    return hubble(a, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k)


# ---------------------------------------------------------------------------
# Deceleration parameter q(a) = -a*ddot{a}/dot{a}^2
# ---------------------------------------------------------------------------

@jit
def deceleration_parameter(a: jnp.ndarray, Omega_m: float, Omega_r: float,
                           Omega_Lambda: float, Omega_k: float) -> jnp.ndarray:
    """q(a) — positive means decelerating, negative means accelerating."""
    E2 = E_squared(a, Omega_m, Omega_r, Omega_Lambda, Omega_k)
    return (2.0 * Omega_r / a**4 + Omega_m / a**3) / (2.0 * E2) - Omega_Lambda / E2


# ---------------------------------------------------------------------------
# Integrands for distance / time integrals (trapezoidal rule on JAX)
# ---------------------------------------------------------------------------

def _trapz(y: jnp.ndarray, x: jnp.ndarray) -> jnp.ndarray:
    """Trapezoidal integration (pure JAX, no scipy dependency)."""
    dx = jnp.diff(x)
    return jnp.sum(0.5 * (y[:-1] + y[1:]) * dx)


@partial(jit, static_argnames=("n_points",))
def cosmic_time(a_target: float, H0: float, Omega_m: float, Omega_r: float,
                Omega_Lambda: float, Omega_k: float,
                n_points: int = 2000) -> float:
    """Cosmic time t(a) in Gyr from the Big Bang to scale factor a_target.

    t(a) = integral_0^a da' / (a' * H(a'))

    H0 is converted from km/s/Mpc to s^-1 internally.
    """
    Mpc_to_m = 3.0857e22
    Gyr_to_s = 3.1557e16
    H0_si = H0 * 1e3 / Mpc_to_m  # s^-1

    a_min = 1e-12
    a_arr = jnp.linspace(a_min, a_target, n_points)
    E2 = E_squared(a_arr, Omega_m, Omega_r, Omega_Lambda, Omega_k)
    integrand = 1.0 / (a_arr * H0_si * jnp.sqrt(E2))
    return _trapz(integrand, a_arr) / Gyr_to_s


@partial(jit, static_argnames=("n_points",))
def conformal_time(a_target: float, H0: float, Omega_m: float, Omega_r: float,
                   Omega_Lambda: float, Omega_k: float,
                   n_points: int = 2000) -> float:
    """Conformal time eta(a) in Mpc from the Big Bang.

    eta(a) = integral_0^a da' / (a'^2 * H(a'))

    Used for causal structure (light cones, horizons).
    """
    Mpc_to_m = 3.0857e22
    H0_si = H0 * 1e3 / Mpc_to_m
    c_si = 2.99792458e8  # m/s

    a_min = 1e-12
    a_arr = jnp.linspace(a_min, a_target, n_points)
    E2 = E_squared(a_arr, Omega_m, Omega_r, Omega_Lambda, Omega_k)
    integrand = c_si / (a_arr**2 * H0_si * jnp.sqrt(E2))
    return _trapz(integrand, a_arr) / Mpc_to_m


@partial(jit, static_argnames=("n_points",))
def comoving_distance(z_target: float, H0: float, Omega_m: float, Omega_r: float,
                      Omega_Lambda: float, Omega_k: float,
                      n_points: int = 2000) -> float:
    """Comoving distance chi(z) in Mpc.

    chi(z) = c * integral_0^z dz' / H(z')

    The fundamental distance measure: how far away an object is today,
    accounting for expansion.
    """
    c_km_s = 299792.458
    z_arr = jnp.linspace(0.0, z_target, n_points)
    H_arr = hubble_from_z(z_arr, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k)
    integrand = c_km_s / H_arr
    return _trapz(integrand, z_arr)


@partial(jit, static_argnames=("n_points",))
def luminosity_distance(z_target: float, H0: float, Omega_m: float, Omega_r: float,
                        Omega_Lambda: float, Omega_k: float,
                        n_points: int = 2000) -> float:
    """Luminosity distance d_L(z) = (1+z) * chi(z) in Mpc (flat universe)."""
    chi = comoving_distance(z_target, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k, n_points)
    return (1.0 + z_target) * chi


@partial(jit, static_argnames=("n_points",))
def angular_diameter_distance(z_target: float, H0: float, Omega_m: float, Omega_r: float,
                              Omega_Lambda: float, Omega_k: float,
                              n_points: int = 2000) -> float:
    """Angular diameter distance d_A(z) = chi(z) / (1+z) in Mpc."""
    chi = comoving_distance(z_target, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k, n_points)
    return chi / (1.0 + z_target)


@partial(jit, static_argnames=("n_points",))
def age_of_universe(H0: float, Omega_m: float, Omega_r: float,
                    Omega_Lambda: float, Omega_k: float,
                    n_points: int = 5000) -> float:
    """Age of the universe t_0 in Gyr (integral from a=0 to a=1)."""
    return cosmic_time(1.0, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k, n_points)


# ---------------------------------------------------------------------------
# Epoch detection
# ---------------------------------------------------------------------------

@jit
def matter_radiation_equality(Omega_m: float, Omega_r: float) -> float:
    """Scale factor at matter-radiation equality: a_eq = Omega_r / Omega_m."""
    return Omega_r / Omega_m


def redshift_matter_radiation_equality(Omega_m: float, Omega_r: float) -> float:
    """Redshift of matter-radiation equality: z_eq = Omega_m / Omega_r - 1."""
    a_eq = matter_radiation_equality(Omega_m, Omega_r)
    return 1.0 / a_eq - 1.0


# ---------------------------------------------------------------------------
# Scale factor evolution a(t) via ODE integration
# ---------------------------------------------------------------------------

@partial(jit, static_argnames=("n_steps",))
def evolve_scale_factor(H0: float, Omega_m: float, Omega_r: float,
                        Omega_Lambda: float, Omega_k: float,
                        a_start: float = 1e-6, a_end: float = 2.0,
                        n_steps: int = 5000) -> tuple[jnp.ndarray, jnp.ndarray]:
    """Integrate da/dt = a * H(a) to get a(t).

    Returns
    -------
    t_arr : array [Gyr]
    a_arr : array
    """
    Mpc_to_m = 3.0857e22
    Gyr_to_s = 3.1557e16
    H0_si = H0 * 1e3 / Mpc_to_m

    a_arr = jnp.linspace(a_start, a_end, n_steps)
    E2 = E_squared(a_arr, Omega_m, Omega_r, Omega_Lambda, Omega_k)
    da_dt = a_arr * H0_si * jnp.sqrt(E2)

    dt = jnp.diff(a_arr) / ((da_dt[:-1] + da_dt[1:]) / 2.0)
    t_arr = jnp.concatenate([jnp.array([0.0]), jnp.cumsum(dt)])
    t_arr = t_arr / Gyr_to_s

    return t_arr, a_arr


# ---------------------------------------------------------------------------
# Convenience: compute everything from a config
# ---------------------------------------------------------------------------

class BackgroundSolution(NamedTuple):
    """Complete background cosmology solution."""
    params: CosmologicalParams
    age_gyr: float
    z_eq: float
    a_eq: float


def solve_background(config_name: str = "planck2018") -> BackgroundSolution:
    """Compute key background quantities from a named config."""
    p = params_from_config(config_name)

    age = age_of_universe(p.H0, p.Omega_m, p.Omega_r, p.Omega_Lambda, p.Omega_k)
    a_eq = matter_radiation_equality(p.Omega_m, p.Omega_r)
    z_eq = 1.0 / a_eq - 1.0

    return BackgroundSolution(params=p, age_gyr=float(age), z_eq=float(z_eq), a_eq=float(a_eq))
