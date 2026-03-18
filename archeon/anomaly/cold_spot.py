"""CMB Cold Spot analysis and detection.

The Cold Spot is a ~10 deg diameter region centered at (l=209, b=-57)
that is anomalously cold (~-150 uK) vs LCDM predictions. Possible
explanations: statistical fluke, supervoid (ISW), cosmic texture,
or bubble universe collision.
"""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy import ndimage

COLD_SPOT_GAL_L = 209.0
COLD_SPOT_GAL_B = -57.0
COLD_SPOT_RADIUS = 5.0
COLD_SPOT_TEMP = -150.0


@dataclass
class ColdSpotCandidate:
    center_x: int
    center_y: int
    radius_pixels: int
    mean_temperature: float
    min_temperature: float
    area_pixels: int
    significance_sigma: float


@dataclass
class ColdSpotAnalysis:
    candidates: list[ColdSpotCandidate]
    coldest_spot: ColdSpotCandidate | None
    map_mean: float
    map_std: float
    n_candidates: int


def find_cold_spots(cmb_map, threshold_sigma=3.0, min_radius=3,
                    smoothing_scale=2.0):
    """Find anomalously cold regions via connected component analysis.

    1. Gaussian smooth to suppress pixel noise
    2. Threshold at -threshold_sigma * std
    3. Label connected components
    4. Characterize each region
    """
    smoothed = ndimage.gaussian_filter(
        cmb_map.astype(np.float64), sigma=smoothing_scale)
    mm = float(smoothed.mean())
    ms = float(smoothed.std())
    labeled, n_reg = ndimage.label(smoothed < (mm - threshold_sigma * ms))
    cands = []
    for rid in range(1, n_reg + 1):
        rmask = labeled == rid
        area = int(rmask.sum())
        if area < min_radius ** 2:
            continue
        ys, xs = np.where(rmask)
        vals = smoothed[rmask]
        mt = float(vals.mean())
        cands.append(ColdSpotCandidate(
            center_x=int(xs.mean()), center_y=int(ys.mean()),
            radius_pixels=max(int(np.sqrt(area / np.pi)), 1),
            mean_temperature=mt, min_temperature=float(vals.min()),
            area_pixels=area, significance_sigma=abs(mt - mm) / ms))
    cands.sort(key=lambda c: c.significance_sigma, reverse=True)
    return ColdSpotAnalysis(
        candidates=cands,
        coldest_spot=cands[0] if cands else None,
        map_mean=mm, map_std=ms, n_candidates=len(cands))


@dataclass
class RadialProfile:
    radii: np.ndarray
    temperatures: np.ndarray
    n_pixels: np.ndarray
    center: tuple[int, int]


def compute_radial_profile(cmb_map, center, max_radius=None, n_bins=20):
    """Azimuthally-averaged temperature profile around a point.

    The real Cold Spot has a characteristic compensated profile:
    cold center surrounded by a warm ring.
    """
    height, width = cmb_map.shape
    cy, cx = center
    if max_radius is None:
        max_radius = min(cx, cy, width - cx, height - cy) - 1
    ycoord, xcoord = np.ogrid[:height, :width]
    r = np.sqrt((xcoord - cx)**2 + (ycoord - cy)**2)
    edges = np.linspace(0, max_radius, n_bins + 1)
    temps = np.zeros(n_bins)
    npix = np.zeros(n_bins, dtype=int)
    for i in range(n_bins):
        ring = (r >= edges[i]) & (r < edges[i + 1])
        if ring.any():
            temps[i] = cmb_map[ring].mean()
            npix[i] = ring.sum()
    return RadialProfile(
        radii=0.5 * (edges[:-1] + edges[1:]),
        temperatures=temps, n_pixels=npix, center=center)


def cold_spot_mc_significance(observed_temperature, simulated_maps,
                              smoothing=2.0):
    """Estimate Cold Spot significance via Monte Carlo.

    For each simulated LCDM map, find the coldest smoothed pixel.
    p_value = fraction of simulations with a colder spot.
    """
    coldest = []
    for i in range(len(simulated_maps)):
        sm = ndimage.gaussian_filter(
            simulated_maps[i].astype(np.float64), sigma=smoothing)
        coldest.append(float(sm.min()))
    coldest_arr = np.array(coldest)
    nc = int(np.sum(coldest_arr <= observed_temperature))
    pv = float((nc + 1) / (len(simulated_maps) + 1))
    return {"p_value": pv, "n_simulations": len(simulated_maps),
            "n_colder": nc, "coldest_per_sim": coldest_arr,
            "observed": observed_temperature}
