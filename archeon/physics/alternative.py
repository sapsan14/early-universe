"""Alternative cosmological models beyond standard ΛCDM.

Implements a hierarchy of cosmological models with modified Friedmann
equations, enabling exploration of:
- f(R) modified gravity
- MOND-inspired cosmology
- Varying fundamental constants (α, G, c)
- Cyclic models (Penrose CCC, Steinhardt-Turok)
- Brane cosmology (Randall-Sundrum)

All models share a common interface: given scale factor a, compute H(a),
the effective equation of state w(a), and the growth factor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp


# ---------------------------------------------------------------------------
# Base cosmology interface
# ---------------------------------------------------------------------------

@dataclass
class CosmoState:
    """Physical state of the Universe at a given scale factor."""
    a: float
    H: float                  # Hubble parameter (km/s/Mpc)
    w_eff: float              # effective equation of state
    rho_total: float          # total energy density (arbitrary units)
    q: float                  # deceleration parameter: q = -a*a''/(a')^2
    extra: dict = field(default_factory=dict)


class BaseCosmology(ABC):
    """Abstract base class for cosmological models."""

    @abstractmethod
    def hubble(self, a: float) -> float:
        """Hubble parameter H(a) in km/s/Mpc."""
        ...

    @abstractmethod
    def w_eff(self, a: float) -> float:
        """Effective equation of state at scale factor a."""
        ...

    def state(self, a: float) -> CosmoState:
        """Full state at scale factor a."""
        H = self.hubble(a)
        w = self.w_eff(a)
        # Deceleration parameter from Friedmann: q = (1 + 3w)/2 * Omega_total
        q = 0.5 * (1.0 + 3.0 * w)
        return CosmoState(a=a, H=H, w_eff=w, rho_total=H**2, q=q)

    def expansion_history(self, a_arr: np.ndarray) -> dict[str, np.ndarray]:
        """Compute H(a) and w(a) over an array of scale factors."""
        H_arr = np.array([self.hubble(float(a)) for a in a_arr])
        w_arr = np.array([self.w_eff(float(a)) for a in a_arr])
        return {"a": a_arr, "H": H_arr, "w_eff": w_arr}

    def growth_factor(self, a_arr: np.ndarray) -> np.ndarray:
        """Linear growth factor D(a) via numerical ODE integration.

        Solves: D'' + 2H D' - 3/2 Omega_m(a) H^2 D = 0
        using the scale factor as independent variable.
        """
        a_min = float(a_arr[0])
        a_max = float(a_arr[-1])

        def deriv(a, y):
            D, dD_da = y
            H = self.hubble(a)
            H0 = self.hubble(1.0)
            # Approximate Omega_m(a) from H ratio
            Omega_m_a = (H0 / H)**2 * 0.315 / a**3
            Omega_m_a = min(Omega_m_a, 1.0)

            dH_da = (self.hubble(a * 1.001) - self.hubble(a * 0.999)) / (0.002 * a)
            term1 = -(3.0 / a + dH_da / H) * dD_da
            term2 = 1.5 * Omega_m_a * (H0 / H)**2 / a**2 * D
            d2D_da2 = term1 + term2
            return [dD_da, d2D_da2]

        sol = solve_ivp(deriv, [a_min, a_max], [a_min, 1.0],
                        t_eval=a_arr, method="RK45", rtol=1e-8)
        D = sol.y[0]
        return D / D[-1]  # normalize to D(a_max) = 1


# ---------------------------------------------------------------------------
# Standard ΛCDM (reference)
# ---------------------------------------------------------------------------

@dataclass
class LCDMCosmology(BaseCosmology):
    """Standard flat ΛCDM cosmology."""
    H0: float = 67.36
    Omega_m: float = 0.3153
    Omega_r: float = 9.1e-5
    Omega_Lambda: float = 0.6847

    def hubble(self, a: float) -> float:
        a = max(a, 1e-10)
        return self.H0 * np.sqrt(
            self.Omega_r / a**4 + self.Omega_m / a**3 + self.Omega_Lambda
        )

    def w_eff(self, a: float) -> float:
        a = max(a, 1e-10)
        rho_r = self.Omega_r / a**4
        rho_m = self.Omega_m / a**3
        rho_L = self.Omega_Lambda
        rho_tot = rho_r + rho_m + rho_L
        if rho_tot < 1e-30:
            return -1.0
        # w_eff = (1/3 * rho_r + 0 * rho_m + (-1) * rho_L) / rho_tot
        return (rho_r / 3.0 - rho_L) / rho_tot


# ---------------------------------------------------------------------------
# f(R) Modified Gravity
# ---------------------------------------------------------------------------

@dataclass
class FRGravity(BaseCosmology):
    """f(R) modified gravity: Hu-Sawicki model.

    f(R) = R - 2Λ + f_R0 * R_0^2 / R

    The modified Friedmann equation:
    H^2 = H0^2 [Omega_m/a^3 + Omega_Lambda + Omega_fR(a)]

    where Omega_fR is the correction from the f(R) modification.

    Parameters
    ----------
    f_R0 : float
        Present-day value of df/dR - 1. |f_R0| < 1e-4 for viability.
        f_R0 = 0 recovers GR.
    n_fR : float
        Power-law index of the Hu-Sawicki model (typically n=1).
    """
    H0: float = 67.36
    Omega_m: float = 0.3153
    Omega_Lambda: float = 0.6847
    f_R0: float = 1e-5
    n_fR: float = 1.0

    def _fR_correction(self, a: float) -> float:
        """Extra term in Friedmann equation from f(R)."""
        a = max(a, 1e-10)
        # Hu-Sawicki: correction scales as f_R0 * (Omega_Lambda / (Omega_m/a^3 + Omega_Lambda))^(n+1)
        rho_m = self.Omega_m / a**3
        rho_L = self.Omega_Lambda
        ratio = rho_L / (rho_m + rho_L + 1e-30)
        return abs(self.f_R0) * ratio ** (self.n_fR + 1)

    def hubble(self, a: float) -> float:
        a = max(a, 1e-10)
        correction = self._fR_correction(a)
        H2 = self.H0**2 * (
            self.Omega_m / a**3 + self.Omega_Lambda * (1.0 + correction)
        )
        return np.sqrt(max(H2, 0))

    def w_eff(self, a: float) -> float:
        a = max(a, 1e-10)
        correction = self._fR_correction(a)
        rho_m = self.Omega_m / a**3
        rho_L = self.Omega_Lambda * (1.0 + correction)
        rho_tot = rho_m + rho_L
        if rho_tot < 1e-30:
            return -1.0
        return -rho_L / rho_tot

    def scalar_field_mass(self, a: float) -> float:
        """Scalaron mass m^2 = (f' - R*f'')/3f'' in Hubble units."""
        a = max(a, 1e-10)
        fR = self._fR_correction(a)
        return 1.0 / (3.0 * abs(fR) + 1e-30)


# ---------------------------------------------------------------------------
# MOND-inspired Cosmology
# ---------------------------------------------------------------------------

@dataclass
class MONDCosmology(BaseCosmology):
    """Modified Newtonian Dynamics (MOND) inspired cosmology.

    At low accelerations (a < a0), the gravitational force transitions
    from Newtonian F = GMm/r^2 to F = GMm*a0/r^2.

    Cosmological MOND: modifies the matter term in Friedmann equation
    by an interpolation function μ(x) where x = a_grav / a0.

    This is TeVeS/AQUAL-inspired, not a strict derivation.
    """
    H0: float = 67.36
    Omega_b: float = 0.049   # baryons only (no CDM in MOND)
    Omega_Lambda: float = 0.951
    a0: float = 1.2e-10      # MOND acceleration scale (m/s^2)
    mu_type: str = "simple"  # "simple" or "standard"

    def _mu(self, x: float) -> float:
        """MOND interpolation function μ(x)."""
        if self.mu_type == "simple":
            return x / (1.0 + x)
        else:
            return x / np.sqrt(1.0 + x**2)

    def hubble(self, a: float) -> float:
        a = max(a, 1e-10)
        # Standard Friedmann with only baryonic matter
        rho_b = self.Omega_b / a**3
        # MOND enhancement: effective matter density is boosted at low accelerations
        H_newton = self.H0 * np.sqrt(rho_b + self.Omega_Lambda)
        # Acceleration in Hubble units
        a_grav = H_newton * self.H0 * 3.086e19  # rough conversion to m/s^2
        x = a_grav / (self.a0 + 1e-30)
        mu = self._mu(x)
        # Effective: H^2 = H0^2 [Omega_b / (a^3 * μ) + Omega_Lambda]
        rho_eff = rho_b / (mu + 1e-10)
        H2 = self.H0**2 * (rho_eff + self.Omega_Lambda)
        return np.sqrt(max(H2, 0))

    def w_eff(self, a: float) -> float:
        a = max(a, 1e-10)
        rho_b = self.Omega_b / a**3
        rho_L = self.Omega_Lambda
        return -rho_L / (rho_b + rho_L + 1e-30)


# ---------------------------------------------------------------------------
# Varying Constants
# ---------------------------------------------------------------------------

@dataclass
class VaryingConstantsCosmology(BaseCosmology):
    """Cosmology with time-varying fundamental constants.

    Explores the impact of varying:
    - alpha (fine structure constant)
    - G (gravitational constant)
    - c (speed of light, mostly theoretical)

    Parameterisation: X(a) = X_0 * (1 + delta_X * (1 - a))
    i.e., linear drift from high-z to today.
    """
    H0: float = 67.36
    Omega_m: float = 0.3153
    Omega_Lambda: float = 0.6847
    delta_alpha: float = 0.0     # Δα/α: e.g. ±1e-5
    delta_G: float = 0.0         # ΔG/G: e.g. ±0.01
    delta_c: float = 0.0         # Δc/c: theoretical only

    def _G_ratio(self, a: float) -> float:
        """G(a) / G_0."""
        return 1.0 + self.delta_G * (1.0 - a)

    def _alpha_ratio(self, a: float) -> float:
        """alpha(a) / alpha_0."""
        return 1.0 + self.delta_alpha * (1.0 - a)

    def hubble(self, a: float) -> float:
        a = max(a, 1e-10)
        G_ratio = self._G_ratio(a)
        # H^2 ∝ G * rho → modified by G(a)/G_0
        H2 = self.H0**2 * G_ratio * (
            self.Omega_m / a**3 + self.Omega_Lambda / G_ratio
        )
        return np.sqrt(max(H2, 0))

    def w_eff(self, a: float) -> float:
        a = max(a, 1e-10)
        G_ratio = self._G_ratio(a)
        rho_m = G_ratio * self.Omega_m / a**3
        rho_L = self.Omega_Lambda
        return -rho_L / (rho_m + rho_L + 1e-30)

    def recombination_shift(self) -> float:
        """Shift in recombination temperature from varying alpha.

        T_rec ∝ alpha^2 * m_e, so ΔT/T ≈ 2 * Δα/α.
        """
        return 2.0 * self.delta_alpha

    def bbn_helium_shift(self) -> float:
        """Shift in primordial He-4 abundance from varying G.

        Higher G → faster expansion → earlier n/p freeze-out → more He-4.
        ΔY_p ≈ 0.012 * ΔG/G (empirical).
        """
        return 0.012 * self.delta_G


# ---------------------------------------------------------------------------
# Cyclic Cosmology
# ---------------------------------------------------------------------------

@dataclass
class CyclicCosmology(BaseCosmology):
    """Cyclic cosmology: Steinhardt-Turok / Penrose CCC inspired.

    The Universe undergoes repeated cycles of expansion and contraction.
    Each cycle ends with a "bounce" or "crunch" followed by a new Big Bang.

    Parameterisation:
    - cycle_period: duration of one cycle (in Hubble times)
    - bounce_scale: minimum scale factor at bounce
    - n_cycles: number of past cycles (for CCC, effectively infinite)

    This is a phenomenological model, not derived from string theory.
    """
    H0: float = 67.36
    Omega_m: float = 0.3153
    Omega_Lambda: float = 0.6847
    cycle_period: float = 2.0   # in units of current Hubble time
    bounce_scale: float = 1e-6  # minimum a at bounce
    turnaround_scale: float = 10.0  # max a before contraction

    def _cycle_phase(self, a: float) -> float:
        """Map scale factor to phase within current cycle [0, 1]."""
        a = max(a, self.bounce_scale)
        log_a = np.log(a / self.bounce_scale)
        log_range = np.log(self.turnaround_scale / self.bounce_scale)
        phase = log_a / log_range
        return min(max(phase, 0.0), 1.0)

    def hubble(self, a: float) -> float:
        a = max(a, 1e-10)
        phase = self._cycle_phase(a)
        # Standard ΛCDM expansion modified by cycle phase
        H_lcdm = self.H0 * np.sqrt(
            self.Omega_m / a**3 + self.Omega_Lambda
        )
        # Near turnaround (phase → 1): H → 0 (deceleration)
        # At bounce (phase → 0): H → large
        cycle_mod = 1.0 - 0.5 * np.sin(np.pi * phase)
        return H_lcdm * cycle_mod

    def w_eff(self, a: float) -> float:
        phase = self._cycle_phase(a)
        # Expanding phase: w transitions from ~0 (matter) to < -1 (phantom)
        # Near turnaround: effective w crosses phantom divide
        w_base = -self.Omega_Lambda / (self.Omega_m / max(a, 1e-10)**3 + self.Omega_Lambda + 1e-30)
        phantom_correction = -0.5 * np.sin(np.pi * phase)**2
        return w_base + phantom_correction

    def time_to_turnaround(self) -> float:
        """Remaining time until next turnaround (in Gyr)."""
        return self.cycle_period * 13.8 / 2.0  # rough estimate


# ---------------------------------------------------------------------------
# Brane Cosmology (Randall-Sundrum II)
# ---------------------------------------------------------------------------

@dataclass
class BraneCosmology(BaseCosmology):
    """Brane cosmology: Randall-Sundrum type II.

    Our 4D Universe is a brane embedded in a 5D bulk.
    The modified Friedmann equation on the brane:

    H^2 = H0^2 [Omega_m/a^3 + Omega_Lambda + Omega_m^2/(a^6 * lambda_brane)]

    The ρ^2 term is the high-energy correction from extra dimensions.

    Parameters
    ----------
    lambda_brane : float
        Brane tension (in units of critical density).
        Large lambda_brane → GR recovered.
    """
    H0: float = 67.36
    Omega_m: float = 0.3153
    Omega_Lambda: float = 0.6847
    lambda_brane: float = 1e4   # brane tension

    def hubble(self, a: float) -> float:
        a = max(a, 1e-10)
        rho_m = self.Omega_m / a**3
        # ρ^2 / λ term: significant only at high densities (early Universe)
        rho2_correction = rho_m**2 / (2.0 * self.lambda_brane)
        H2 = self.H0**2 * (rho_m + self.Omega_Lambda + rho2_correction)
        return np.sqrt(max(H2, 0))

    def w_eff(self, a: float) -> float:
        a = max(a, 1e-10)
        rho_m = self.Omega_m / a**3
        rho_L = self.Omega_Lambda
        rho2 = rho_m**2 / (2.0 * self.lambda_brane)
        rho_tot = rho_m + rho_L + rho2
        # ρ^2 term has w = 1 (stiff matter)
        return (-rho_L + rho2) / (rho_tot + 1e-30)

    def extra_dimension_scale(self, a: float) -> float:
        """Effective size of the extra dimension (in Hubble lengths)."""
        rho_m = self.Omega_m / max(a, 1e-10)**3
        return 1.0 / np.sqrt(self.lambda_brane / (rho_m + 1e-30))


# ---------------------------------------------------------------------------
# Model comparison utilities
# ---------------------------------------------------------------------------

def compare_models(
    models: dict[str, BaseCosmology],
    a_arr: np.ndarray | None = None,
) -> dict[str, dict]:
    """Compare expansion histories of multiple cosmological models.

    Returns dict[model_name] → {a, H, w_eff, H_ratio} where H_ratio
    is relative to the first model.
    """
    if a_arr is None:
        a_arr = np.linspace(0.01, 1.0, 500)

    results = {}
    ref_H = None
    for name, model in models.items():
        history = model.expansion_history(a_arr)
        if ref_H is None:
            ref_H = history["H"]
        history["H_ratio"] = history["H"] / (ref_H + 1e-30)
        results[name] = history

    return results


def compute_observables(model: BaseCosmology, z_arr: np.ndarray) -> dict:
    """Compute observable quantities for a cosmological model.

    Returns luminosity distance, angular diameter distance, and
    comoving distance as functions of redshift.
    """
    from scipy.integrate import cumulative_trapezoid

    a_arr = 1.0 / (1.0 + z_arr)
    H_arr = np.array([model.hubble(float(a)) for a in a_arr])

    c_km_s = 299792.458  # speed of light in km/s

    # Comoving distance: chi = c * integral(dz / H(z))
    integrand = c_km_s / H_arr
    chi = np.zeros_like(z_arr)
    chi[1:] = cumulative_trapezoid(integrand, z_arr)

    d_L = chi * (1.0 + z_arr)        # luminosity distance
    d_A = chi / (1.0 + z_arr + 1e-30)  # angular diameter distance

    return {
        "z": z_arr,
        "chi_Mpc": chi,
        "d_L_Mpc": d_L,
        "d_A_Mpc": d_A,
        "H_km_s_Mpc": H_arr,
    }
