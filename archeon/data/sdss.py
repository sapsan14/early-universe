"""SDSS (Sloan Digital Sky Survey) data integration.

SDSS is the largest optical galaxy survey, providing:
- Photometry and spectroscopy for millions of galaxies
- Redshifts, magnitudes, morphologies
- Galaxy clustering measurements for cosmological constraints

Data access: SciServer/CasJobs SQL interface or astroquery.
Current release: DR18.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    from astroquery.sdss import SDSS
    ASTROQUERY_AVAILABLE = True
except ImportError:
    ASTROQUERY_AVAILABLE = False


DEFAULT_CACHE_DIR = Path.home() / ".archeon" / "data" / "sdss"


def query_galaxies(ra_range: tuple[float, float] = (150.0, 160.0),
                   dec_range: tuple[float, float] = (30.0, 40.0),
                   z_min: float = 0.0, z_max: float = 0.5,
                   mag_limit: float = 21.0,
                   limit: int = 10000) -> dict:
    """Query SDSS galaxy catalog via astroquery.

    Parameters
    ----------
    ra_range : tuple
        Right ascension range [degrees].
    dec_range : tuple
        Declination range [degrees].
    z_min, z_max : float
        Redshift range.
    mag_limit : float
        Apparent magnitude limit (r-band).
    limit : int
        Maximum number of results.

    Returns
    -------
    dict with keys: ra, dec, z, mag_r, mag_g, objID
    """
    if not ASTROQUERY_AVAILABLE:
        raise ImportError("astroquery required. Install: pip install astroquery")

    sql = f"""
    SELECT TOP {limit}
        p.objID, p.ra, p.dec,
        p.modelMag_r as mag_r, p.modelMag_g as mag_g,
        s.z as redshift, s.zErr as z_err
    FROM PhotoObj AS p
    JOIN SpecObj AS s ON s.bestobjid = p.objid
    WHERE
        p.ra BETWEEN {ra_range[0]} AND {ra_range[1]}
        AND p.dec BETWEEN {dec_range[0]} AND {dec_range[1]}
        AND s.z BETWEEN {z_min} AND {z_max}
        AND p.modelMag_r < {mag_limit}
        AND s.class = 'GALAXY'
        AND s.zWarning = 0
    ORDER BY s.z
    """

    result = SDSS.query_sql(sql)

    if result is None:
        return {"ra": np.array([]), "dec": np.array([]),
                "z": np.array([]), "mag_r": np.array([])}

    return {
        "ra": np.array(result["ra"]),
        "dec": np.array(result["dec"]),
        "z": np.array(result["redshift"]),
        "z_err": np.array(result["z_err"]),
        "mag_r": np.array(result["mag_r"]),
        "mag_g": np.array(result["mag_g"]),
        "objID": np.array(result["objID"]),
    }


def compute_galaxy_correlation(ra: np.ndarray, dec: np.ndarray,
                               z: np.ndarray,
                               n_bins: int = 20,
                               max_sep_deg: float = 5.0) -> tuple[np.ndarray, np.ndarray]:
    """Estimate angular two-point correlation function w(theta).

    w(theta) measures excess galaxy pairs at separation theta compared
    to a random distribution. Related to the matter power spectrum P(k)
    via Limber's equation.

    Uses the Landy-Szalay estimator: w = (DD - 2DR + RR) / RR.

    Returns
    -------
    theta_bins : array of bin centers [degrees]
    w_theta : array of correlation values
    """
    n = len(ra)
    n_random = n * 3

    rng = np.random.default_rng(42)
    ra_rand = rng.uniform(ra.min(), ra.max(), n_random)
    dec_rand = rng.uniform(dec.min(), dec.max(), n_random)

    theta_bins = np.linspace(0.01, max_sep_deg, n_bins + 1)
    theta_centers = 0.5 * (theta_bins[:-1] + theta_bins[1:])

    def _count_pairs(ra1, dec1, ra2, dec2, bins):
        counts = np.zeros(len(bins) - 1)
        for i in range(min(len(ra1), 5000)):
            sep = np.sqrt((ra1[i] - ra2)**2 + (dec1[i] - dec2)**2)
            hist, _ = np.histogram(sep, bins=bins)
            counts += hist
        return counts

    DD = _count_pairs(ra, dec, ra, dec, theta_bins)
    DR = _count_pairs(ra, dec, ra_rand, dec_rand, theta_bins)
    RR = _count_pairs(ra_rand, dec_rand, ra_rand, dec_rand, theta_bins)

    f = n_random / n
    w = np.where(RR > 0,
                 (f**2 * DD - 2 * f * DR + RR) / (RR + 1e-10),
                 0.0)

    return theta_centers, w
