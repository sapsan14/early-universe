"""Planck CMB data loading utilities.

Downloads and loads data products from the Planck Legacy Archive (PLA):
- CMB temperature maps (HEALPix FITS, Nside=2048)
- Angular power spectra C_l (FITS tables)
- Component-separated maps (SMICA, NILC, SEVEM, Commander)

Planck (ESA mission, 2009-2013) is the gold standard for CMB observations.
The 2018 data release contains:
- Temperature maps with ~5 arcminute resolution
- 6 cosmological parameters determined to <1% precision
- Full-sky coverage (with Galactic mask for analysis)

Data source: https://pla.esac.esa.int/
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np

try:
    import healpy as hp
    HEALPY_AVAILABLE = True
except ImportError:
    HEALPY_AVAILABLE = False

try:
    from astropy.io import fits
    from astropy.utils.data import download_file
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Planck data URLs (2018 release, PR3)
# ---------------------------------------------------------------------------

PLANCK_URLS = {
    # Component-separated CMB maps
    "smica": (
        "http://pla.esac.esa.int/pla/aio/product-action?"
        "MAP.MAP_ID=COM_CMB_IQU-smica_2048_R3.00_full.fits"
    ),
    "nilc": (
        "http://pla.esac.esa.int/pla/aio/product-action?"
        "MAP.MAP_ID=COM_CMB_IQU-nilc_2048_R3.00_full.fits"
    ),
    "sevem": (
        "http://pla.esac.esa.int/pla/aio/product-action?"
        "MAP.MAP_ID=COM_CMB_IQU-sevem_2048_R3.00_full.fits"
    ),
    "commander": (
        "http://pla.esac.esa.int/pla/aio/product-action?"
        "MAP.MAP_ID=COM_CMB_IQU-commander_2048_R3.00_full.fits"
    ),
    # Power spectrum (best-fit)
    "power_spectrum": (
        "http://pla.esac.esa.int/pla/aio/product-action?"
        "MAP.MAP_ID=COM_PowerSpect_CMB-TT-full_R3.01.txt"
    ),
    # Common mask
    "mask": (
        "http://pla.esac.esa.int/pla/aio/product-action?"
        "MAP.MAP_ID=COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
    ),
}

# Simpler alternative URLs from the IRSA/LAMBDA archive
LAMBDA_URLS = {
    "smica": (
        "https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/"
        "maps/component-maps/cmb/COM_CMB_IQU-smica_2048_R3.00_full.fits"
    ),
    "power_spectrum_tt": (
        "https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/"
        "cosmoparams/COM_PowerSpect_CMB-TT-full_R3.01.txt"
    ),
}

DEFAULT_CACHE_DIR = Path.home() / ".archeon" / "data" / "planck"


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def _ensure_cache_dir(cache_dir: Path | None = None) -> Path:
    d = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def download_planck_map(
    component: Literal["smica", "nilc", "sevem", "commander"] = "smica",
    cache_dir: Path | str | None = None,
) -> Path:
    """Download a Planck component-separated CMB map.

    The four pipelines (SMICA, NILC, SEVEM, Commander) use different
    methods to separate CMB from foregrounds (dust, synchrotron, etc.).
    SMICA is the default "best" map.

    Downloads ~1.5 GB per map (Nside=2048, ~50M pixels).

    Parameters
    ----------
    component : str
        Which pipeline: "smica", "nilc", "sevem", "commander".
    cache_dir : Path, optional

    Returns
    -------
    path : Path to the downloaded FITS file.
    """
    if not ASTROPY_AVAILABLE:
        raise ImportError("astropy required. Install: pip install astropy")

    cache = _ensure_cache_dir(cache_dir)
    filename = f"planck_{component}_2048_R3.00.fits"
    filepath = cache / filename

    if filepath.exists():
        print(f"Using cached: {filepath}")
        return filepath

    url = PLANCK_URLS.get(component) or LAMBDA_URLS.get(component)
    if url is None:
        raise ValueError(f"Unknown component: {component}")

    print(f"Downloading Planck {component} map (~1.5 GB)...")
    tmp = download_file(url, cache=False)
    Path(tmp).rename(filepath)
    print(f"Saved to: {filepath}")
    return filepath


# ---------------------------------------------------------------------------
# Map loading
# ---------------------------------------------------------------------------

def load_planck_map(
    component: Literal["smica", "nilc", "sevem", "commander"] = "smica",
    field: int = 0,
    nside_out: int | None = None,
    cache_dir: Path | str | None = None,
) -> np.ndarray:
    """Load a Planck CMB map as a HEALPix array.

    Parameters
    ----------
    component : str
        Which pipeline.
    field : int
        0 = temperature (I), 1 = Q polarization, 2 = U polarization.
    nside_out : int, optional
        If set, downgrade resolution (e.g. 2048 -> 64 for quick tests).
    cache_dir : Path, optional

    Returns
    -------
    cmb_map : array of shape (12*nside^2,)
        Temperature map in Kelvin (or micro-Kelvin depending on convention).
    """
    if not HEALPY_AVAILABLE:
        raise ImportError("healpy required")

    filepath = download_planck_map(component, cache_dir=cache_dir)

    cmb_map = hp.read_map(filepath, field=field, verbose=False)

    if nside_out is not None:
        nside_in = hp.npix2nside(len(cmb_map))
        if nside_out != nside_in:
            cmb_map = hp.ud_grade(cmb_map, nside_out)

    return cmb_map


def load_planck_mask(
    nside_out: int | None = None,
    cache_dir: Path | str | None = None,
) -> np.ndarray:
    """Load the Planck common analysis mask.

    The mask removes the Galactic plane and point sources where
    foreground contamination is too strong for CMB analysis.
    ~78% of the sky is unmasked.

    Returns
    -------
    mask : array of 0s and 1s (1 = valid pixel).
    """
    if not HEALPY_AVAILABLE:
        raise ImportError("healpy required")

    cache = _ensure_cache_dir(cache_dir)
    filename = "planck_mask_common_2048.fits"
    filepath = cache / filename

    if not filepath.exists():
        url = PLANCK_URLS["mask"]
        print("Downloading Planck common mask...")
        tmp = download_file(url, cache=False)
        Path(tmp).rename(filepath)

    mask = hp.read_map(filepath, verbose=False)

    if nside_out is not None:
        nside_in = hp.npix2nside(len(mask))
        if nside_out != nside_in:
            mask = hp.ud_grade(mask, nside_out)
            mask = (mask > 0.5).astype(np.float64)

    return mask


# ---------------------------------------------------------------------------
# Power spectrum loading
# ---------------------------------------------------------------------------

def load_planck_power_spectrum(
    cache_dir: Path | str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load Planck 2018 TT power spectrum.

    Returns
    -------
    ell : array
        Multipole values.
    Dl : array
        D_l = l(l+1) C_l / (2*pi) in (micro-K)^2.
    sigma : array
        1-sigma uncertainties.
    """
    cache = _ensure_cache_dir(cache_dir)
    filename = "planck_power_spectrum_TT.txt"
    filepath = cache / filename

    if not filepath.exists():
        url = PLANCK_URLS.get("power_spectrum") or LAMBDA_URLS.get("power_spectrum_tt")
        if not ASTROPY_AVAILABLE:
            raise ImportError("astropy required for download")
        print("Downloading Planck TT power spectrum...")
        tmp = download_file(url, cache=False)
        Path(tmp).rename(filepath)

    data = np.loadtxt(filepath, comments="#")

    if data.shape[1] >= 3:
        ell = data[:, 0]
        Dl = data[:, 1]
        sigma = data[:, 2] if data.shape[1] > 2 else np.zeros_like(Dl)
    else:
        raise ValueError(f"Unexpected format in {filepath}")

    return ell, Dl, sigma


def planck_dl_to_cl(ell: np.ndarray, Dl: np.ndarray) -> np.ndarray:
    """Convert D_l to C_l: C_l = 2*pi * D_l / [l*(l+1)]."""
    cl = np.zeros_like(Dl)
    valid = ell > 1
    cl[valid] = 2.0 * np.pi * Dl[valid] / (ell[valid] * (ell[valid] + 1.0))
    return cl


# ---------------------------------------------------------------------------
# Quick visualization
# ---------------------------------------------------------------------------

def plot_planck_map(cmb_map: np.ndarray, title: str = "Planck CMB",
                    unit: str = "K", **kwargs) -> None:
    """Display a CMB map using Mollweide projection."""
    if not HEALPY_AVAILABLE:
        raise ImportError("healpy required")
    hp.mollview(cmb_map, title=title, unit=unit, **kwargs)


def plot_power_spectrum(ell: np.ndarray, Dl: np.ndarray,
                        sigma: np.ndarray | None = None,
                        title: str = "Planck 2018 TT") -> None:
    """Plot D_l = l(l+1)C_l/(2pi) vs l."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5))
    if sigma is not None and np.any(sigma > 0):
        ax.errorbar(ell, Dl, yerr=sigma, fmt=".", markersize=1, alpha=0.5,
                     label="Planck 2018")
    else:
        ax.plot(ell, Dl, ".", markersize=1, label="Planck 2018")

    ax.set_xlabel(r"Multipole $\ell$")
    ax.set_ylabel(r"$D_\ell = \ell(\ell+1)C_\ell / 2\pi$ [$\mu K^2$]")
    ax.set_title(title)
    ax.set_xlim(2, max(ell))
    ax.legend()
    plt.tight_layout()
    return fig
