"""Boltzmann hierarchy for cosmological perturbations.

In the early universe, photons, baryons, CDM, and neutrinos form a coupled
fluid. Perturbations in this fluid evolve according to a hierarchy of coupled
ODEs — the Boltzmann equations in Fourier space.

The photon distribution is expanded in multipole moments Theta_l(k, tau):
  l=0: monopole (temperature perturbation / overdensity)
  l=1: dipole (velocity)
  l=2: quadrupole (anisotropic stress, drives polarization)
  l>=3: higher multipoles (free-streaming)

This module implements the truncated hierarchy in conformal Newtonian gauge,
following Ma & Bertschinger (1995) and Dodelson "Modern Cosmology" Ch. 8.
"""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp
from jax import jit

from archeon.config import get_constants, get_cosmology
from archeon.physics.friedmann import E_squared


class PerturbationState(NamedTuple):
    """State vector for a single Fourier mode k at conformal time tau."""
    delta_cdm: float    # CDM overdensity delta_c
    v_cdm: float        # CDM velocity (in units of k * conformal time)
    delta_b: float      # Baryon overdensity
    v_b: float          # Baryon velocity
    Theta: jnp.ndarray  # Photon multipoles [Theta_0, Theta_1, ..., Theta_lmax]
    Theta_P: jnp.ndarray  # Polarization multipoles [Theta_P0, ..., Theta_Plmax]
    Nu: jnp.ndarray     # Massless neutrino multipoles [Nu_0, Nu_1, ..., Nu_lmax]
    Phi: float          # Gravitational potential (Bardeen)
    Psi: float          # Gravitational potential (Bardeen)


# ---------------------------------------------------------------------------
# Thomson scattering optical depth rate
# ---------------------------------------------------------------------------

@jit
def thomson_scattering_rate(a: float, x_e: float, Omega_b: float,
                            H0: float) -> float:
    """Thomson scattering rate dtau/d(conf.time) = n_e * sigma_T * a.

    This is the interaction rate between photons and electrons. When large,
    the photon-baryon fluid is tightly coupled.
    """
    Mpc_to_m = 3.0857e22
    sigma_T = 6.6524587e-29
    m_p = 1.67262192e-27
    c_m = 2.99792458e8

    H0_si = H0 * 1e3 / Mpc_to_m
    rho_crit = 3.0 * H0_si**2 / (8.0 * jnp.pi * 6.674e-11)
    n_b0 = Omega_b * rho_crit / m_p
    n_e = x_e * n_b0 / a**3

    return n_e * sigma_T * c_m * a


# ---------------------------------------------------------------------------
# Boltzmann hierarchy ODEs
# ---------------------------------------------------------------------------

@jit
def photon_hierarchy_rhs(k: float, Theta: jnp.ndarray, Theta_P: jnp.ndarray,
                         Psi: float, Phi_dot: float,
                         v_b: float, dtau_dtau_c: float) -> jnp.ndarray:
    """Right-hand side for photon temperature multipoles.

    dTheta_0/dtau = -k * Theta_1 - Phi_dot
    dTheta_1/dtau = k/3 * (Theta_0 - 2*Theta_2 + Psi) + dtau_c * (Theta_1 - v_b/3)
    dTheta_l/dtau = k/(2l+1) * [l*Theta_{l-1} - (l+1)*Theta_{l+1}]
                    - dtau_c * [Theta_l - delta_{l,0}*Theta_0 - delta_{l,1}*v_b/3
                                - delta_{l,2}*Pi/10]

    where Pi = Theta_2 + Theta_P0 + Theta_P2 is the polarization source.
    dtau_c < 0 for scattering (convention: opacity rate).
    """
    l_max = Theta.shape[0] - 1
    Pi = Theta[2] + Theta_P[0] + Theta_P[2] if Theta_P.shape[0] > 2 else Theta[2]

    dTheta = jnp.zeros_like(Theta)

    # l = 0: monopole
    dTheta = dTheta.at[0].set(-k * Theta[1] - Phi_dot)

    # l = 1: dipole
    dTheta = dTheta.at[1].set(
        k / 3.0 * (Theta[0] - 2.0 * Theta[2] + Psi)
        + dtau_dtau_c * (Theta[1] - v_b / 3.0)
    )

    # l = 2: quadrupole (source of polarization)
    dTheta = dTheta.at[2].set(
        k / 5.0 * (2.0 * Theta[1] - 3.0 * Theta[3])
        + dtau_dtau_c * (Theta[2] - Pi / 10.0)
    )

    # l >= 3
    for l in range(3, l_max):
        dTheta = dTheta.at[l].set(
            k / (2.0 * l + 1.0) * (l * Theta[l - 1] - (l + 1.0) * Theta[l + 1])
            + dtau_dtau_c * Theta[l]
        )

    # l = l_max: truncation (free-streaming approximation)
    dTheta = dTheta.at[l_max].set(
        k * Theta[l_max - 1] - (l_max + 1.0) * Theta[l_max] / 1.0  # placeholder eta
        + dtau_dtau_c * Theta[l_max]
    )

    return dTheta


@jit
def cdm_equations_rhs(k: float, delta_cdm: float, v_cdm: float,
                      Psi: float, Phi_dot: float,
                      aH: float) -> tuple[float, float]:
    """CDM perturbation equations (pressureless, collisionless).

    d(delta_c)/dtau = -k * v_c - 3 * Phi_dot
    d(v_c)/dtau     = -aH * v_c - k * Psi

    CDM only feels gravity — no pressure, no scattering.
    """
    d_delta = -k * v_cdm - 3.0 * Phi_dot
    d_v = -aH * v_cdm - k * Psi
    return d_delta, d_v


@jit
def baryon_equations_rhs(k: float, delta_b: float, v_b: float,
                         Theta_1: float, Psi: float, Phi_dot: float,
                         aH: float, dtau_dtau_c: float,
                         R: float) -> tuple[float, float]:
    """Baryon perturbation equations.

    d(delta_b)/dtau = -k * v_b - 3 * Phi_dot
    d(v_b)/dtau     = -aH * v_b - k * c_s^2 * delta_b - k * Psi
                      + dtau_c / R * (v_b - 3 * Theta_1)

    R = 3 rho_b / (4 rho_gamma) is the baryon-to-photon momentum ratio.
    Before decoupling, Thomson scattering tightly couples v_b to Theta_1.
    """
    cs2 = 1.0 / (3.0 * (1.0 + R))  # baryon sound speed squared (with photon pressure)
    d_delta = -k * v_b - 3.0 * Phi_dot
    d_v = (-aH * v_b - k * cs2 * delta_b - k * Psi
           + dtau_dtau_c / R * (v_b - 3.0 * Theta_1))
    return d_delta, d_v


@jit
def neutrino_hierarchy_rhs(k: float, Nu: jnp.ndarray,
                           Psi: float, Phi_dot: float) -> jnp.ndarray:
    """Massless neutrino hierarchy (same as photons but no scattering).

    dNu_0/dtau = -k * Nu_1 - Phi_dot
    dNu_1/dtau = k/3 * (Nu_0 - 2*Nu_2 + Psi)
    dNu_l/dtau = k/(2l+1) * [l*Nu_{l-1} - (l+1)*Nu_{l+1}]

    Neutrinos decouple at T ~ 1 MeV (z ~ 10^10), so they free-stream
    throughout the epochs relevant for CMB.
    """
    l_max = Nu.shape[0] - 1
    dNu = jnp.zeros_like(Nu)

    dNu = dNu.at[0].set(-k * Nu[1] - Phi_dot)
    dNu = dNu.at[1].set(k / 3.0 * (Nu[0] - 2.0 * Nu[2] + Psi))

    for l in range(2, l_max):
        dNu = dNu.at[l].set(
            k / (2.0 * l + 1.0) * (l * Nu[l - 1] - (l + 1.0) * Nu[l + 1])
        )

    dNu = dNu.at[l_max].set(k * Nu[l_max - 1] - (l_max + 1.0) * Nu[l_max] / 1.0)

    return dNu


# ---------------------------------------------------------------------------
# Metric perturbation equations (conformal Newtonian gauge)
# ---------------------------------------------------------------------------

@jit
def poisson_equation(k: float, a: float, H0: float,
                     Omega_m: float, Omega_r: float,
                     delta_cdm: float, delta_b: float,
                     Theta_0: float, Nu_0: float,
                     Omega_cdm: float, Omega_b: float) -> float:
    """Poisson equation for the gravitational potential Phi.

    k^2 Phi = -4 pi G a^2 (rho_cdm delta_cdm + rho_b delta_b + 4 rho_gamma Theta_0 + ...)

    In dimensionless form with E = H/H0:
    k^2 Phi = -(3/2) H0^2 [Omega_cdm/a * delta_cdm + Omega_b/a * delta_b
                            + 4*Omega_gamma/a^2 * Theta_0 + 4*Omega_nu/a^2 * Nu_0]
    """
    Mpc_to_m = 3.0857e22
    H0_per_c = H0 * 1e3 / (Mpc_to_m * 2.99792458e8)  # H0/c in Mpc^-1

    source = (Omega_cdm * delta_cdm / a
              + Omega_b * delta_b / a
              + 4.0 * Omega_r * Theta_0 / a**2)

    return -1.5 * H0_per_c**2 * source / k**2


# ---------------------------------------------------------------------------
# Initial conditions (adiabatic mode)
# ---------------------------------------------------------------------------

def adiabatic_initial_conditions(k: float, l_max_photon: int = 10,
                                 l_max_nu: int = 10,
                                 A_s: float = 2.1e-9) -> PerturbationState:
    """Set adiabatic initial conditions deep in the radiation era.

    All species start with correlated perturbations set by a single
    curvature mode (the "adiabatic" mode from inflation):
      delta_cdm = delta_b = 3/4 * delta_gamma = 3/4 * delta_nu
      Theta_0 = -Psi/2,  Theta_1 ~ k/(6*dtau_c) (tight coupling)
    """
    Phi_init = 1.0  # normalized (will be scaled by A_s later)
    Psi_init = -Phi_init  # no anisotropic stress initially

    Theta = jnp.zeros(l_max_photon + 1)
    Theta = Theta.at[0].set(-Psi_init / 2.0)
    Theta = Theta.at[1].set(Psi_init * k / 6.0)  # tight-coupling approx

    Theta_P = jnp.zeros(l_max_photon + 1)

    Nu = jnp.zeros(l_max_nu + 1)
    Nu = Nu.at[0].set(-Psi_init / 2.0)
    Nu = Nu.at[1].set(Psi_init * k / 6.0)

    delta_cdm = -1.5 * Psi_init
    v_cdm = Psi_init * k / 2.0
    delta_b = delta_cdm
    v_b = v_cdm

    return PerturbationState(
        delta_cdm=delta_cdm, v_cdm=v_cdm,
        delta_b=delta_b, v_b=v_b,
        Theta=Theta, Theta_P=Theta_P, Nu=Nu,
        Phi=Phi_init, Psi=Psi_init,
    )
