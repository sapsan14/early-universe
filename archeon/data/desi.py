"""DESI (Dark Energy Spectroscopic Instrument) data integration.

DESI is the most ambitious galaxy redshift survey (2021-2026):
- 40 million galaxy/quasar spectra over 14,000 deg^2
- Baryon Acoustic Oscillation (BAO) measurements at 0 < z < 3.5
- Growth rate of structure via redshift-space distortions (RSD)
- Constraints on dark energy equation of state w(z)

BAO measurements provide a "standard ruler" (the sound horizon at
drag epoch, r_d ~ 147 Mpc) visible in the galaxy correlation function.
This gives geometric distance measurements: D_A(z) and D_H(z) = c/H(z).

Data access: https://data.desi.lbl.gov/
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


DEFAULT_CACHE_DIR = Path.home() / ".archeon" / "data" / "desi"


@dataclass
class BAOMeasurement:
    """A single BAO distance measurement at redshift z."""
    z_eff: float                # Effective redshift
    DM_over_rd: float           # D_M(z) / r_d (comoving angular diameter distance / sound horizon)
    DM_over_rd_err: float
    DH_over_rd: float           # D_H(z) / r_d = c / (H(z) * r_d)
    DH_over_rd_err: float
    tracer: str                 # Galaxy type: "LRG", "ELG", "QSO", "Lya"


# DESI 2024 BAO measurements (arXiv:2404.03002)
DESI_BAO_2024 = [
    BAOMeasurement(z_eff=0.30, DM_over_rd=7.93, DM_over_rd_err=0.15,
                   DH_over_rd=20.66, DH_over_rd_err=0.62, tracer="BGS"),
    BAOMeasurement(z_eff=0.51, DM_over_rd=13.62, DM_over_rd_err=0.25,
                   DH_over_rd=20.98, DH_over_rd_err=0.61, tracer="LRG1"),
    BAOMeasurement(z_eff=0.71, DM_over_rd=16.85, DM_over_rd_err=0.32,
                   DH_over_rd=20.08, DH_over_rd_err=0.61, tracer="LRG2"),
    BAOMeasurement(z_eff=0.93, DM_over_rd=21.71, DM_over_rd_err=0.28,
                   DH_over_rd=17.88, DH_over_rd_err=0.35, tracer="LRG3+ELG1"),
    BAOMeasurement(z_eff=1.32, DM_over_rd=27.79, DM_over_rd_err=0.69,
                   DH_over_rd=13.82, DH_over_rd_err=0.42, tracer="ELG2"),
    BAOMeasurement(z_eff=1.49, DM_over_rd=26.07, DM_over_rd_err=0.67,
                   DH_over_rd=13.23, DH_over_rd_err=0.48, tracer="QSO"),
    BAOMeasurement(z_eff=2.33, DM_over_rd=39.71, DM_over_rd_err=0.94,
                   DH_over_rd=8.52, DH_over_rd_err=0.17, tracer="Lya"),
]


def get_desi_bao() -> list[BAOMeasurement]:
    """Return DESI 2024 BAO measurements."""
    return DESI_BAO_2024


def bao_distance_prediction(z: float, H0: float, Omega_m: float,
                             Omega_Lambda: float, r_d: float = 147.09) -> dict:
    """Predict BAO observables D_M/r_d and D_H/r_d for given cosmology.

    Compare with DESI measurements to constrain parameters.

    Parameters
    ----------
    z : float
        Redshift.
    H0, Omega_m, Omega_Lambda : float
        Cosmological parameters.
    r_d : float
        Sound horizon at drag epoch [Mpc]. Planck: 147.09 Mpc.

    Returns
    -------
    dict with DM_over_rd and DH_over_rd.
    """
    from archeon.physics.friedmann import comoving_distance, hubble_from_z

    Omega_r = 9.14e-5
    Omega_k = 0.0

    DM = float(comoving_distance(z, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k))
    Hz = float(hubble_from_z(z, H0, Omega_m, Omega_r, Omega_Lambda, Omega_k))
    c_km_s = 299792.458

    return {
        "DM_over_rd": DM / r_d,
        "DH_over_rd": c_km_s / (Hz * r_d),
    }


def bao_chi_squared(H0: float, Omega_m: float,
                    Omega_Lambda: float,
                    r_d: float = 147.09,
                    measurements: list[BAOMeasurement] | None = None) -> float:
    """Compute chi^2 for BAO data given cosmological parameters.

    This is the simplest form of cosmological parameter fitting:
    compare predicted distances with observed, weighted by uncertainties.
    """
    if measurements is None:
        measurements = DESI_BAO_2024

    chi2 = 0.0
    for m in measurements:
        pred = bao_distance_prediction(m.z_eff, H0, Omega_m, Omega_Lambda, r_d)
        chi2 += ((pred["DM_over_rd"] - m.DM_over_rd) / m.DM_over_rd_err) ** 2
        chi2 += ((pred["DH_over_rd"] - m.DH_over_rd) / m.DH_over_rd_err) ** 2

    return chi2
