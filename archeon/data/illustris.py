"""IllustrisTNG cosmological simulation data access.

IllustrisTNG is a suite of large-volume magnetohydrodynamic cosmological
simulations (Pillepich+18, Nelson+19) providing:
- Dark matter halo catalogs
- Galaxy properties (masses, SFR, morphology)
- Gas density/temperature fields
- Merger trees

Used in ARCHEON for:
1. Validating our N-body engine (Phase 6) against state-of-the-art simulations
2. Training data for structure formation ML models
3. Ground truth for the Playable Universe

Data access: https://www.tng-project.org/data/ (requires free API key)
Available simulations: TNG50, TNG100, TNG300 (box sizes in Mpc/h)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


BASE_URL = "https://www.tng-project.org/api"
DEFAULT_CACHE_DIR = Path.home() / ".archeon" / "data" / "illustris"


class IllustrisTNGClient:
    """HTTP client for IllustrisTNG public API.

    Requires an API key from https://www.tng-project.org/data/
    Set via environment variable ILLUSTRIS_API_KEY or pass directly.
    """

    def __init__(self, api_key: str | None = None):
        import os
        self.api_key = api_key or os.environ.get("ILLUSTRIS_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "IllustrisTNG API key required. "
                "Get one at https://www.tng-project.org/data/ "
                "and set ILLUSTRIS_API_KEY environment variable."
            )
        self.headers = {"api-key": self.api_key}

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests required. Install: pip install requests")
        url = f"{BASE_URL}/{endpoint}"
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def list_simulations(self) -> list[dict]:
        """List available simulations."""
        return self._get("")

    def get_simulation(self, sim: str = "TNG100-1") -> dict:
        """Get simulation metadata (box size, particle count, snapshots)."""
        return self._get(sim)

    def get_snapshot(self, sim: str = "TNG100-1", snap: int = 99) -> dict:
        """Get snapshot metadata (redshift, num_halos, etc.)."""
        return self._get(f"{sim}/snapshots/{snap}")

    def get_halos(self, sim: str = "TNG100-1", snap: int = 99,
                  limit: int = 100, min_mass: float = 1e12) -> list[dict]:
        """Query halo catalog.

        Parameters
        ----------
        sim : str
            Simulation name.
        snap : int
            Snapshot number (99 = z=0 for TNG).
        limit : int
            Max halos to return.
        min_mass : float
            Minimum halo mass [M_sun/h].

        Returns
        -------
        list of halo dictionaries with mass, position, velocity, etc.
        """
        params = {
            "limit": limit,
            "mass__gt": min_mass,
            "order_by": "-mass",
        }
        result = self._get(f"{sim}/snapshots/{snap}/halos/", params)
        return result.get("results", [])

    def get_subhalos(self, sim: str = "TNG100-1", snap: int = 99,
                     limit: int = 100) -> list[dict]:
        """Query subhalo (galaxy) catalog."""
        params = {"limit": limit, "order_by": "-mass_stars"}
        result = self._get(f"{sim}/snapshots/{snap}/subhalos/", params)
        return result.get("results", [])


def compute_halo_mass_function(masses: np.ndarray,
                               box_size_mpc: float,
                               n_bins: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """Compute the halo mass function dn/dlog10(M).

    The halo mass function is a key prediction of cosmology:
    how many dark matter halos of each mass exist per unit volume.

    Sensitive to sigma_8 and Omega_m — useful for cosmological constraints.

    Parameters
    ----------
    masses : array
        Halo masses [M_sun/h].
    box_size_mpc : float
        Simulation box size [Mpc/h].
    n_bins : int

    Returns
    -------
    log_mass_bins : array of bin centers
    dn_dlogM : array of number density [h^3 Mpc^{-3}]
    """
    volume = box_size_mpc ** 3
    log_masses = np.log10(masses)

    counts, bin_edges = np.histogram(log_masses, bins=n_bins)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    dlogM = bin_edges[1] - bin_edges[0]

    dn_dlogM = counts / (volume * dlogM)

    return bin_centers, dn_dlogM
