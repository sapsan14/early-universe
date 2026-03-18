"""Cosmological perturbation theory: transfer functions, P(k), and C_l.

The universe started nearly uniform, with tiny perturbations seeded by
inflation. These perturbations grew under gravity to form all observed
structure (galaxies, clusters, CMB anisotropies).

Key quantities:
- Transfer function T(k): how each Fourier mode evolves from initial conditions
  to today, encoding BAO, Silk damping, etc.
- Matter power spectrum P(k): the statistical description of density fluctuations
- Angular power spectrum C_l: the CMB temperature anisotropy spectrum, the
  "fingerprint" of cosmology observable through CMB maps

This module provides:
1. Eisenstein-Hu fitting formula for T(k) (analytical, fast)
2. P(k) from T(k) + primordial spectrum
3. C_l via line-of-sight integration (simplified)
"""

from __future__ import annotations

from functools import partial

import jax.numpy as jnp
from jax import jit

from archeon.config import get_constants, get_cosmology


# ---------------------------------------------------------------------------
# Eisenstein-Hu transfer function (no baryon oscillations, zero-baryon approx)
# Eisenstein & Hu 1998 (ApJ 496, 605), Eq. 29-31
# ---------------------------------------------------------------------------

@jit
def transfer_function_eh98(k: jnp.ndarray, h: float,
                           Omega_m: float, Omega_b: float,
                           T_cmb: float = 2.7255) -> jnp.ndarray:
    """Eisenstein-Hu transfer function (with baryon features).

    A fast analytical approximation accurate to ~5% that captures the
    main physics: horizon crossing, matter-radiation equality, Silk damping,
    and baryon acoustic oscillations (BAO).

    Parameters
    ----------
    k : array
        Wavenumber in h/Mpc.
    h : float
        Dimensionless Hubble parameter H0/100.
    Omega_m : float
        Total matter density parameter.
    Omega_b : float
        Baryon density parameter.
    T_cmb : float
        CMB temperature [K].

    Returns
    -------
    T(k) : array
        Transfer function values.
    """
    Omega_m_h2 = Omega_m * h**2
    Omega_b_h2 = Omega_b * h**2
    theta = T_cmb / 2.7

    # Sound horizon at drag epoch
    z_eq = 2.5e4 * Omega_m_h2 * theta**(-4)
    k_eq = 7.46e-2 * Omega_m_h2 * theta**(-2)  # Mpc^-1

    b1 = 0.313 * Omega_m_h2**(-0.419) * (1.0 + 0.607 * Omega_m_h2**0.674)
    b2 = 0.238 * Omega_m_h2**0.223
    z_drag = (1291.0 * Omega_m_h2**0.251 / (1.0 + 0.659 * Omega_m_h2**0.828)
              * (1.0 + b1 * Omega_b_h2**b2))

    R_drag = 31.5e3 * Omega_b_h2 * theta**(-4) / z_drag  # baryon-to-photon ratio at drag
    R_eq = 31.5e3 * Omega_b_h2 * theta**(-4) / z_eq

    s = (2.0 / (3.0 * k_eq) * jnp.sqrt(6.0 / R_eq)
         * jnp.log((jnp.sqrt(1.0 + R_drag) + jnp.sqrt(R_drag + R_eq))
                    / (1.0 + jnp.sqrt(R_eq))))

    # Silk damping scale
    k_silk = (1.6 * Omega_b_h2**0.52 * Omega_m_h2**0.73
              * (1.0 + (10.4 * Omega_m_h2)**(-0.95)))

    # CDM transfer (zero-baryon piece)
    f_b = Omega_b / Omega_m
    f_c = 1.0 - f_b

    a1 = (46.9 * Omega_m_h2)**0.670 * (1.0 + (32.1 * Omega_m_h2)**(-0.532))
    a2 = (12.0 * Omega_m_h2)**0.424 * (1.0 + (45.0 * Omega_m_h2)**(-0.582))
    alpha_c = a1**(-f_b) * a2**(-f_b**3)

    b1_c = 0.944 / (1.0 + (458.0 * Omega_m_h2)**(-0.708))
    b2_c = (0.395 * Omega_m_h2)**(-0.0266)
    beta_c = 1.0 / (1.0 + b1_c * ((f_c)**b2_c - 1.0))

    q = k / (13.41 * k_eq)  # k in h/Mpc, k_eq in Mpc^-1, adjusted

    def _T0_tilde(k_val, alpha, beta):
        q_eff = k_val / (13.41 * k_eq)
        C_q = 14.2 / alpha + 386.0 / (1.0 + 69.9 * q_eff**1.08)
        T0 = jnp.log(jnp.e + 1.8 * beta * q_eff) / (
            jnp.log(jnp.e + 1.8 * beta * q_eff) + C_q * q_eff**2)
        return T0

    T_c = (f_c * _T0_tilde(k, 1.0, beta_c)
           + (1.0 - f_c) * _T0_tilde(k, alpha_c, beta_c))

    # Baryon transfer
    s_tilde = s / (1.0 + (k * s / 5.2)**3)**(1.0 / 3.0)
    alpha_b = (2.07 * k_eq * s * (1.0 + R_drag)**(-3.0 / 4.0)
               * _G_func(k_eq * s * (1.0 + z_eq) / (1.0 + z_drag)))

    beta_b = 0.5 + f_b + (3.0 - 2.0 * f_b) * jnp.sqrt((17.2 * Omega_m_h2)**2 + 1.0)
    beta_node = 8.41 * Omega_m_h2**0.435

    j0_arg = k * s_tilde
    j0 = jnp.sinc(j0_arg / jnp.pi)  # sinc(x) = sin(pi*x)/(pi*x), we need sin(x)/x
    j0 = jnp.sin(j0_arg) / (j0_arg + 1e-30)  # sin(ks)/ks

    T_b = (_T0_tilde(k, 1.0, 1.0) / (1.0 + (k * s / 5.2)**2)
           + alpha_b / (1.0 + (beta_b / (k * s))**3) * jnp.exp(-(k / k_silk)**1.4))
    T_b = T_b * j0

    T_k = f_b * T_b + f_c * T_c
    return T_k


@jit
def _G_func(y: jnp.ndarray) -> jnp.ndarray:
    """Helper function for EH98 baryon transfer."""
    return y * (-6.0 * jnp.sqrt(1.0 + y)
                + (2.0 + 3.0 * y) * jnp.log((jnp.sqrt(1.0 + y) + 1.0)
                                              / (jnp.sqrt(1.0 + y) - 1.0 + 1e-30)))


# ---------------------------------------------------------------------------
# Simpler transfer function (BBKS, for validation)
# ---------------------------------------------------------------------------

@jit
def transfer_function_bbks(k: jnp.ndarray, Omega_m: float, h: float) -> jnp.ndarray:
    """BBKS transfer function (Bardeen, Bond, Kaiser, Szalay 1986).

    A simpler approximation valid for CDM-only (no baryon features).
    Gamma = Omega_m * h (shape parameter).
    """
    Gamma = Omega_m * h
    q = k / Gamma  # effective wavenumber

    T = (jnp.log(1.0 + 2.34 * q) / (2.34 * q)
         * (1.0 + 3.89 * q + (16.1 * q)**2 + (5.46 * q)**3 + (6.71 * q)**4)**(-0.25))

    return T


# ---------------------------------------------------------------------------
# Matter power spectrum P(k)
# ---------------------------------------------------------------------------

@jit
def primordial_power_spectrum(k: jnp.ndarray, A_s: float,
                              n_s: float, k_pivot: float) -> jnp.ndarray:
    """Primordial power spectrum from inflation.

    P_prim(k) = A_s * (k / k_pivot)^{n_s - 1}

    Nearly scale-invariant (n_s ~ 0.965), as predicted by single-field
    slow-roll inflation. The slight red tilt (n_s < 1) is one of the
    key signatures of inflation.
    """
    return A_s * (k / k_pivot) ** (n_s - 1.0)


@jit
def matter_power_spectrum(k: jnp.ndarray, T_k: jnp.ndarray,
                          A_s: float, n_s: float, k_pivot: float) -> jnp.ndarray:
    """Matter power spectrum P(k) = P_prim(k) * T^2(k) * k.

    The full P(k) combines the primordial spectrum with the transfer
    function that encodes all post-inflationary evolution.

    Units: (Mpc/h)^3
    """
    P_prim = primordial_power_spectrum(k, A_s, n_s, k_pivot)
    return P_prim * T_k**2 * k


# ---------------------------------------------------------------------------
# Growth factor D(z)
# ---------------------------------------------------------------------------

@partial(jit, static_argnames=("n_points",))
def growth_factor(z: float, Omega_m: float, Omega_Lambda: float,
                  n_points: int = 1000) -> float:
    """Linear growth factor D(z), normalized to D(0) = 1.

    D(a) propto H(a) * integral_0^a da' / (a' H(a'))^3

    Describes how perturbations grow over time due to gravitational
    instability. D(z) = 1 today, D(z) ~ 1/(1+z) in the matter era.
    """
    Omega_k = 1.0 - Omega_m - Omega_Lambda

    def _E(a_val):
        return jnp.sqrt(Omega_m / a_val**3 + Omega_k / a_val**2 + Omega_Lambda)

    a_target = 1.0 / (1.0 + z)
    a_arr = jnp.linspace(1e-6, a_target, n_points)
    E_arr = jnp.array([_E(a) for a in a_arr]) if a_arr.ndim == 0 else jnp.vectorize(_E)(a_arr)

    integrand = 1.0 / (a_arr * E_arr)**3
    da = jnp.diff(a_arr)
    integral = jnp.sum(0.5 * (integrand[:-1] + integrand[1:]) * da)

    D_z = _E(a_target) * integral

    # Normalize to D(z=0) = 1
    a_0_arr = jnp.linspace(1e-6, 1.0, n_points)
    E_0_arr = jnp.vectorize(_E)(a_0_arr)
    integrand_0 = 1.0 / (a_0_arr * E_0_arr)**3
    da_0 = jnp.diff(a_0_arr)
    integral_0 = jnp.sum(0.5 * (integrand_0[:-1] + integrand_0[1:]) * da_0)
    D_0 = _E(1.0) * integral_0

    return D_z / D_0


# ---------------------------------------------------------------------------
# sigma_8: RMS fluctuations in 8 Mpc/h spheres
# ---------------------------------------------------------------------------

@jit
def sigma_R_squared(R: float, k_arr: jnp.ndarray,
                    Pk_arr: jnp.ndarray) -> float:
    """sigma^2(R) = integral k^2/(2*pi^2) * P(k) * |W(kR)|^2 dk.

    W(x) = 3(sin(x) - x*cos(x))/x^3 is the top-hat window function.
    sigma_8 = sqrt(sigma^2(R=8 Mpc/h)) measures the amplitude of
    clustering on ~galaxy-cluster scales.
    """
    x = k_arr * R
    W = 3.0 * (jnp.sin(x) - x * jnp.cos(x)) / x**3

    integrand = k_arr**2 / (2.0 * jnp.pi**2) * Pk_arr * W**2
    dk = jnp.diff(k_arr)
    return jnp.sum(0.5 * (integrand[:-1] + integrand[1:]) * dk)


# ---------------------------------------------------------------------------
# Angular power spectrum C_l (simplified Sachs-Wolfe + acoustic)
# ---------------------------------------------------------------------------

@partial(jit, static_argnames=("n_k",))
def angular_power_spectrum_sw(l_arr: jnp.ndarray, A_s: float, n_s: float,
                              k_pivot: float, chi_star: float,
                              n_k: int = 1000) -> jnp.ndarray:
    """Simplified C_l via Sachs-Wolfe approximation.

    C_l ~ (2/pi) * integral k^2 * P_prim(k) * [j_l(k * chi_star)]^2 dk / (9 * k)

    The full C_l requires line-of-sight integration through the
    Boltzmann hierarchy. This approximation captures the Sachs-Wolfe plateau
    at low l (large angular scales) where C_l ~ l(l+1) ~ const.
    """
    k_min = 1e-4
    k_max = 0.3
    k_arr = jnp.logspace(jnp.log10(k_min), jnp.log10(k_max), n_k)

    P_prim = primordial_power_spectrum(k_arr, A_s, n_s, k_pivot)

    def _cl_for_l(l_val):
        x = k_arr * chi_star
        # Spherical Bessel j_l via recursion (for moderate l, use sin/cos form)
        jl = jnp.where(
            x > 1e-6,
            jnp.sqrt(jnp.pi / (2.0 * x)) * jnp.sin(x - l_val * jnp.pi / 2.0 + jnp.pi / 4.0),
            0.0
        )
        integrand = k_arr**2 * P_prim * jl**2 / (9.0 * k_arr)
        dk = jnp.diff(k_arr)
        return (2.0 / jnp.pi) * jnp.sum(0.5 * (integrand[:-1] + integrand[1:]) * dk)

    # Vectorize over l
    Cl = jnp.array([_cl_for_l(l) for l in l_arr])
    return Cl


# ---------------------------------------------------------------------------
# Convenience: compute P(k) from config
# ---------------------------------------------------------------------------

def compute_matter_pk(k_arr: jnp.ndarray,
                      config_name: str = "planck2018") -> jnp.ndarray:
    """Compute P(k) at z=0 from a named config."""
    cosmo = get_cosmology(config_name)

    T_k = transfer_function_eh98(
        k_arr, cosmo["h"], cosmo["Omega_m"], cosmo["Omega_b"]
    )

    return matter_power_spectrum(
        k_arr, T_k, cosmo["A_s"], cosmo["n_s"], cosmo["k_pivot"]
    )
