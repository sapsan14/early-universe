"""Spherical harmonics analysis and synthesis for CMB maps.

The CMB temperature field on the sky T(theta, phi) is naturally described
by spherical harmonics Y_lm — the "Fourier modes" on a sphere:

    T(theta, phi) = sum_l sum_m  a_lm * Y_lm(theta, phi)

The coefficients a_lm encode all information. Their variance defines
the angular power spectrum: C_l = <|a_lm|^2>.

This module wraps healpy (HEALPix for Python) for:
- Map <-> a_lm conversion (analysis/synthesis)
- Power spectrum estimation from maps
- Map generation from theoretical C_l
- Visualization utilities

HEALPix (Hierarchical Equal Area isoLatitude Pixelization) is the standard
pixelization scheme for CMB data, used by Planck, WMAP, etc.
"""

from __future__ import annotations

import numpy as np

try:
    import healpy as hp

    HEALPY_AVAILABLE = True
except ImportError:
    HEALPY_AVAILABLE = False


def _require_healpy():
    if not HEALPY_AVAILABLE:
        raise ImportError(
            "healpy is required for spherical harmonics operations. "
            "Install with: pip install healpy"
        )


# ---------------------------------------------------------------------------
# Map <-> a_lm conversion
# ---------------------------------------------------------------------------

def map_to_alm(cmb_map: np.ndarray, lmax: int | None = None) -> np.ndarray:
    """Decompose a HEALPix map into spherical harmonic coefficients a_lm.

    Parameters
    ----------
    cmb_map : array
        HEALPix map (npix = 12 * nside^2 pixels).
    lmax : int, optional
        Maximum multipole. Default: 3 * nside - 1.

    Returns
    -------
    alm : complex array
        Spherical harmonic coefficients in healpy ordering.
    """
    _require_healpy()
    return hp.map2alm(cmb_map, lmax=lmax)


def alm_to_map(alm: np.ndarray, nside: int, lmax: int | None = None) -> np.ndarray:
    """Synthesize a HEALPix map from spherical harmonic coefficients.

    Parameters
    ----------
    alm : complex array
        Spherical harmonic coefficients.
    nside : int
        HEALPix resolution (npix = 12 * nside^2).
    lmax : int, optional
        Maximum multipole used.

    Returns
    -------
    cmb_map : array
        Reconstructed HEALPix map.
    """
    _require_healpy()
    return hp.alm2map(alm, nside, lmax=lmax, verbose=False)


# ---------------------------------------------------------------------------
# Power spectrum estimation
# ---------------------------------------------------------------------------

def map_to_cl(cmb_map: np.ndarray, lmax: int | None = None) -> np.ndarray:
    """Estimate angular power spectrum C_l from a HEALPix map.

    Uses the pseudo-C_l estimator: C_l = (1/(2l+1)) * sum_m |a_lm|^2.
    This is the full-sky estimator; for partial sky coverage, mode coupling
    corrections (e.g. MASTER/NaMaster) are needed.

    Returns
    -------
    cl : array of shape (lmax+1,)
        Power spectrum C_l for l = 0, 1, ..., lmax.
    """
    _require_healpy()
    return hp.anafast(cmb_map, lmax=lmax)


def alm_to_cl(alm: np.ndarray, lmax: int | None = None) -> np.ndarray:
    """Compute C_l directly from a_lm coefficients."""
    _require_healpy()
    return hp.alm2cl(alm, lmax=lmax)


# ---------------------------------------------------------------------------
# Map generation from theoretical C_l
# ---------------------------------------------------------------------------

def generate_cmb_map(cl: np.ndarray, nside: int,
                     seed: int | None = None) -> np.ndarray:
    """Generate a random CMB realization from a theoretical C_l spectrum.

    Each a_lm is drawn from a Gaussian: a_lm ~ N(0, C_l).
    This is the basic synthetic CMB map generation used for training data.

    Parameters
    ----------
    cl : array
        Theoretical power spectrum C_l (e.g. from CLASS or our emulator).
    nside : int
        HEALPix resolution. Common values:
          64  — quick tests (~49k pixels)
          256 — training data (~786k pixels)
          2048 — Planck resolution (~50M pixels)
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    cmb_map : array
        Simulated CMB temperature map in HEALPix format.
    """
    _require_healpy()
    if seed is not None:
        np.random.seed(seed)
    return hp.synfast(cl, nside, verbose=False)


def generate_alm_from_cl(cl: np.ndarray,
                         seed: int | None = None) -> np.ndarray:
    """Generate random a_lm from C_l without synthesizing a map.

    Useful when working directly in harmonic space.
    """
    _require_healpy()
    if seed is not None:
        np.random.seed(seed)
    lmax = len(cl) - 1
    return hp.synalm(cl, lmax=lmax)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def nside_to_npix(nside: int) -> int:
    """Number of pixels for a given nside: npix = 12 * nside^2."""
    return 12 * nside**2


def npix_to_nside(npix: int) -> int:
    """Infer nside from number of pixels."""
    _require_healpy()
    return hp.npix2nside(npix)


def get_pixel_area(nside: int) -> float:
    """Area of one HEALPix pixel in steradians."""
    return 4.0 * np.pi / nside_to_npix(nside)


def mollweide_data(cmb_map: np.ndarray) -> np.ndarray:
    """Return Mollweide-projected image array for custom visualization.

    For standard visualization, use healpy.mollview() directly.
    """
    _require_healpy()
    return hp.mollview(cmb_map, return_projected_map=True)


def angular_distance(theta1: float, phi1: float,
                     theta2: float, phi2: float) -> float:
    """Great-circle distance between two points on the sphere [radians].

    theta: colatitude (0=north pole, pi=south pole)
    phi: longitude
    """
    cos_d = (np.sin(theta1) * np.sin(theta2) * np.cos(phi1 - phi2)
             + np.cos(theta1) * np.cos(theta2))
    return np.arccos(np.clip(cos_d, -1, 1))
