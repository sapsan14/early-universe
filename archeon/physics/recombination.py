"""Recombination physics: Saha equation and Peebles three-level model.

Computes the ionization fraction x_e(z) — the fraction of free electrons
in the primordial hydrogen plasma. This determines when photons decouple
from baryons, forming the CMB (z ~ 1100).

Two approaches:
1. Saha equation — equilibrium approximation, accurate for high T
2. Peebles equation — non-equilibrium ODE, accurate through freeze-out

The optical depth tau(z) and visibility function g(z) are also computed,
as they define the "surface of last scattering".
"""

from __future__ import annotations

from functools import partial

import jax.numpy as jnp
from jax import jit

from archeon.config import get_constants, get_cosmology
from archeon.physics.friedmann import hubble_from_z


# ---------------------------------------------------------------------------
# Physical constants (SI unless noted)
# ---------------------------------------------------------------------------

def _load_constants():
    c = get_constants()
    return {
        "k_B": c["k_B"],             # J/K
        "k_B_eV": c["k_B_eV"],       # eV/K
        "hbar": c["hbar"],            # J s
        "m_e": c["m_e"],              # kg
        "sigma_T": c["sigma_T"],      # m^2
        "c": c["c_cgs"] * 1e-2,      # m/s (from cm/s)
        "T_cmb": c["T_cmb"],         # K
        "E_ion": c["E_ion_H"],       # eV
        "Mpc_to_m": c["Mpc_to_m"],   # m
    }


# ---------------------------------------------------------------------------
# Saha equation (equilibrium)
# ---------------------------------------------------------------------------

@jit
def saha_ionization_fraction(T: jnp.ndarray, n_b: jnp.ndarray,
                             k_B: float, m_e: float, hbar: float,
                             E_ion_eV: float, k_B_eV: float) -> jnp.ndarray:
    """Ionization fraction x_e from the Saha equation.

    x_e^2 / (1 - x_e) = (1/n_b) * (m_e k_B T / (2 pi hbar^2))^{3/2} * exp(-E_I / k_B T)

    Valid in thermal equilibrium (high T). Breaks down during freeze-out
    where actual x_e stays higher than Saha predicts (recombination is slower
    than the expansion rate).
    """
    T = jnp.float64(T)
    n_b = jnp.float64(n_b)

    thermal_factor = (m_e * k_B * T / (2.0 * jnp.pi * hbar**2))**1.5
    exp_factor = jnp.exp(-E_ion_eV / (k_B_eV * T))
    rhs = thermal_factor * exp_factor / n_b

    # Solve quadratic: x^2 + rhs*x - rhs = 0
    # Numerically stable form: x = 2*rhs / (rhs + sqrt(rhs^2 + 4*rhs))
    # Avoids catastrophic cancellation when rhs >> 1 (high T / fully ionized)
    discriminant = rhs**2 + 4.0 * rhs
    x_e = 2.0 * rhs / (rhs + jnp.sqrt(discriminant) + 1e-300)
    return jnp.clip(x_e, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Peebles equation (non-equilibrium)
# ---------------------------------------------------------------------------

@jit
def case_B_recombination_rate(T: jnp.ndarray) -> jnp.ndarray:
    """Case-B recombination coefficient alpha^(2)(T) in m^3/s.

    Recombination to excited states only (Lyman-alpha photons escape
    or are reabsorbed, so direct-to-ground recombination doesn't count).
    Fitting formula from Pequignot et al. (1991).
    """
    t4 = T / 1e4
    return 4.309e-19 * t4**(-0.6166) / (1.0 + 0.6703 * t4**0.5300)


@jit
def photoionization_rate(T: jnp.ndarray, alpha2: jnp.ndarray,
                         k_B: float, m_e: float, hbar: float,
                         E_ion_eV: float, k_B_eV: float) -> jnp.ndarray:
    """Photoionization rate beta(T) from detailed balance.

    beta = alpha^(2) * (m_e k_B T / (2 pi hbar^2))^{3/2} * exp(-E_I / k_BT)
    """
    thermal = (m_e * k_B * T / (2.0 * jnp.pi * hbar**2))**1.5
    return alpha2 * thermal * jnp.exp(-E_ion_eV / (k_B_eV * T))


@jit
def peebles_Cr(n_b: jnp.ndarray, alpha2: jnp.ndarray,
               beta: jnp.ndarray, H: jnp.ndarray,
               k_B_eV: float, T: jnp.ndarray, E_ion_eV: float) -> jnp.ndarray:
    """Peebles correction factor C_r.

    Accounts for the fact that Lyman-alpha photons are reabsorbed
    (so only two-photon decay from 2s state actually removes ionizations).

    C_r = (Lambda_2s + Lambda_alpha) / (Lambda_2s + Lambda_alpha + beta^(2))

    where Lambda_2s = 8.227 s^-1 (two-photon decay rate),
    Lambda_alpha = H * (3 E_ion / (8 pi))^3 / (n_1s * c^3) from Sobolev escape.
    """
    Lambda_2s = 8.227  # s^-1, two-photon decay rate of 2s state
    E_Lya_eV = E_ion_eV * 3.0 / 4.0

    # beta^(2) is the photoionization rate from n=2
    beta2 = beta * jnp.exp(E_Lya_eV / (k_B_eV * T))

    # Effective Lyman-alpha escape (cosmological redshift out of line)
    H_si = H * 1e3 / 3.0857e22  # km/s/Mpc -> s^-1
    Lambda_alpha = H_si * (E_Lya_eV * 1.602e-19)**3 / (
        8.0 * jnp.pi * (1.0546e-34)**3 * (3e8)**3 * n_b
    )

    return (Lambda_2s + Lambda_alpha) / (Lambda_2s + Lambda_alpha + beta2)


def solve_peebles(z_start: float = 1800.0, z_end: float = 200.0,
                  n_steps: int = 5000,
                  config_name: str = "planck2018") -> tuple[jnp.ndarray, jnp.ndarray]:
    """Integrate the Peebles equation for x_e(z).

    dx_e/dz = (1/(1+z)) * [beta(T)(1 - x_e) - alpha^(2)(T) n_b x_e^2] * C_r / H(z)

    Parameters
    ----------
    z_start : float
        Starting redshift (fully ionized, x_e ~ 1).
    z_end : float
        Final redshift.
    n_steps : int
        Number of integration steps.

    Returns
    -------
    z_arr : array of shape (n_steps,)
    xe_arr : array of shape (n_steps,)
    """
    cosmo = get_cosmology(config_name)
    const = get_constants(config_name)

    H0 = cosmo["H0"]
    Omega_m = cosmo["Omega_m"]
    Omega_r = cosmo["Omega_r"]
    Omega_Lambda = cosmo["Omega_Lambda"]
    Omega_k = cosmo["Omega_k"]
    Omega_b = cosmo["Omega_b"]
    T_cmb = const["T_cmb"]
    k_B = const["k_B"]
    k_B_eV = const["k_B_eV"]
    m_e = const["m_e"]
    hbar = const["hbar"]
    E_ion = const["E_ion_H"]
    m_p = const["m_p"]
    Mpc_to_m = const["Mpc_to_m"]

    rho_crit = 3.0 * (H0 * 1e3 / Mpc_to_m)**2 / (8.0 * jnp.pi * 6.674e-11)
    n_b0 = Omega_b * rho_crit / m_p

    z_arr = jnp.linspace(z_start, z_end, n_steps)
    dz = z_arr[1] - z_arr[0]

    # Forward Euler integration (z decreasing, dz < 0)
    xe = jnp.ones(n_steps)
    xe_list = [1.0]
    x_e_current = 1.0

    z_np = jnp.asarray(z_arr)
    T_arr = T_cmb * (1.0 + z_np)
    n_b_arr = n_b0 * (1.0 + z_np)**3
    H_arr = hubble_from_z(z_np, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k)

    alpha2_arr = case_B_recombination_rate(T_arr)
    beta_arr = photoionization_rate(T_arr, alpha2_arr, k_B, m_e, hbar, E_ion, k_B_eV)
    Cr_arr = peebles_Cr(n_b_arr, alpha2_arr, beta_arr, H_arr, k_B_eV, T_arr, E_ion)

    H_si_arr = H_arr * 1e3 / Mpc_to_m

    xe_out = [1.0]
    x_e = 1.0
    for i in range(1, n_steps):
        n_b = float(n_b_arr[i])
        alpha2 = float(alpha2_arr[i])
        beta_val = float(beta_arr[i])
        Cr = float(Cr_arr[i])
        H_si = float(H_si_arr[i])
        z_val = float(z_arr[i])

        # dx_e/dz via chain rule: dx_e/dt * dt/dz, where dt/dz = -1/((1+z)*H)
        recomb = alpha2 * n_b * x_e**2
        ioniz = beta_val * (1.0 - x_e)
        dx_e_dt = Cr * (ioniz - recomb)
        dx_e_dz = dx_e_dt * (-1.0 / ((1.0 + z_val) * H_si))

        x_e = x_e + dx_e_dz * dz
        x_e = max(min(x_e, 1.0), 1e-12)
        xe_out.append(x_e)

    return z_arr, jnp.array(xe_out)


# ---------------------------------------------------------------------------
# Optical depth and visibility function
# ---------------------------------------------------------------------------

def optical_depth(z_arr: jnp.ndarray, xe_arr: jnp.ndarray,
                  config_name: str = "planck2018") -> jnp.ndarray:
    """Thomson optical depth tau(z) = integral n_e sigma_T c dt/dz dz.

    Measures how opaque the universe is to photons looking back to redshift z.
    tau >> 1 means photons cannot free-stream (tightly coupled to baryons).
    """
    cosmo = get_cosmology(config_name)
    const = get_constants(config_name)

    H0 = cosmo["H0"]
    Omega_m = cosmo["Omega_m"]
    Omega_r = cosmo["Omega_r"]
    Omega_Lambda = cosmo["Omega_Lambda"]
    Omega_k = cosmo["Omega_k"]
    Omega_b = cosmo["Omega_b"]
    sigma_T = const["sigma_T"]
    T_cmb = const["T_cmb"]
    m_p = const["m_p"]
    Mpc_to_m = const["Mpc_to_m"]
    c_m = const["c_cgs"] * 1e-2

    rho_crit = 3.0 * (H0 * 1e3 / Mpc_to_m)**2 / (8.0 * jnp.pi * 6.674e-11)
    n_b0 = Omega_b * rho_crit / m_p

    H_arr = hubble_from_z(z_arr, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k)
    H_si = H_arr * 1e3 / Mpc_to_m

    n_e = xe_arr * n_b0 * (1.0 + z_arr)**3
    integrand = n_e * sigma_T * c_m / ((1.0 + z_arr) * H_si)

    # Cumulative integral from low z to high z
    tau = jnp.zeros_like(z_arr)
    dz = jnp.diff(z_arr)
    d_tau = 0.5 * (integrand[:-1] + integrand[1:]) * jnp.abs(dz)
    tau = jnp.concatenate([jnp.array([0.0]), jnp.cumsum(d_tau)])

    return tau


def visibility_function(z_arr: jnp.ndarray, xe_arr: jnp.ndarray,
                        config_name: str = "planck2018") -> jnp.ndarray:
    """Visibility function g(z) = d(tau)/dz * exp(-tau).

    The probability that a CMB photon last scattered at redshift z.
    Sharply peaked at z ~ 1100 — the surface of last scattering.
    """
    tau = optical_depth(z_arr, xe_arr, config_name)
    dtau_dz = jnp.gradient(tau, z_arr)
    g = jnp.abs(dtau_dz) * jnp.exp(-tau)
    return g
