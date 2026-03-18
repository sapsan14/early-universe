"""Gaia DR3 data integration.

Gaia (ESA mission) provides the most precise astrometric catalog:
- Positions, parallaxes, proper motions for ~1.8 billion stars
- Radial velocities for ~33 million stars
- Used for: Milky Way dynamics, distance ladder, H0 measurement

While Gaia is primarily stellar, it connects to cosmology through:
1. Distance ladder calibration (Cepheids -> H0)
2. Milky Way structure (dark matter halo constraints)
3. Gravitational lensing calibration

Data access: astroquery / ESA Gaia Archive TAP.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    from astroquery.gaia import Gaia
    GAIA_AVAILABLE = True
except ImportError:
    GAIA_AVAILABLE = False


DEFAULT_CACHE_DIR = Path.home() / ".archeon" / "data" / "gaia"


def query_stars(ra: float = 180.0, dec: float = 0.0,
                radius_deg: float = 1.0,
                mag_limit: float = 15.0,
                limit: int = 5000) -> dict:
    """Query Gaia DR3 stars in a cone around (ra, dec).

    Parameters
    ----------
    ra, dec : float
        Center coordinates [degrees].
    radius_deg : float
        Search radius [degrees].
    mag_limit : float
        G-band magnitude limit.
    limit : int
        Maximum results.

    Returns
    -------
    dict with keys: ra, dec, parallax, pmra, pmdec, phot_g_mean_mag, etc.
    """
    if not GAIA_AVAILABLE:
        raise ImportError("astroquery required. Install: pip install astroquery")

    query = f"""
    SELECT TOP {limit}
        source_id, ra, dec, parallax, parallax_error,
        pmra, pmdec, phot_g_mean_mag,
        bp_rp, radial_velocity
    FROM gaiadr3.gaia_source
    WHERE
        CONTAINS(POINT('ICRS', ra, dec),
                 CIRCLE('ICRS', {ra}, {dec}, {radius_deg})) = 1
        AND phot_g_mean_mag < {mag_limit}
        AND parallax IS NOT NULL
        AND parallax > 0
    ORDER BY phot_g_mean_mag
    """

    job = Gaia.launch_job(query)
    result = job.get_results()

    return {col: np.array(result[col]) for col in result.colnames}


def parallax_to_distance(parallax_mas: np.ndarray) -> np.ndarray:
    """Convert parallax [milliarcseconds] to distance [parsec].

    d [pc] = 1000 / parallax [mas]

    Simple inversion — for precise distances with significant
    parallax errors, use a Bayesian approach (e.g. Bailer-Jones).
    """
    valid = parallax_mas > 0
    dist = np.full_like(parallax_mas, np.nan)
    dist[valid] = 1000.0 / parallax_mas[valid]
    return dist


def query_cepheids(limit: int = 1000) -> dict:
    """Query known Cepheid variable stars from Gaia DR3.

    Cepheids are the first rung of the distance ladder:
    their period-luminosity relation gives absolute distances,
    which calibrate Type Ia supernovae, which give H0.
    """
    if not GAIA_AVAILABLE:
        raise ImportError("astroquery required")

    query = f"""
    SELECT TOP {limit}
        g.source_id, g.ra, g.dec, g.parallax, g.parallax_error,
        g.phot_g_mean_mag, v.pf, v.type_best_classification
    FROM gaiadr3.gaia_source AS g
    JOIN gaiadr3.vari_cepheid AS v
        ON g.source_id = v.source_id
    WHERE g.parallax > 0
    ORDER BY g.phot_g_mean_mag
    """

    job = Gaia.launch_job(query)
    result = job.get_results()
    return {col: np.array(result[col]) for col in result.colnames}
