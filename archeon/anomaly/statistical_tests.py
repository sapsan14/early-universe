"""Statistical tests for CMB anomaly significance.

Anomaly detection isn't enough — we need to quantify how
statistically significant each anomaly is. Methods:

1. Pixel-level: Kolmogorov-Smirnov, Anderson-Darling
2. Multipole-level: chi-squared per ell, cumulative deviation
3. Non-Gaussianity: skewness, kurtosis, Minkowski functionals
4. Monte Carlo significance: compare to N simulated realizations
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats as sp_stats


# ---------------------------------------------------------------------------
# Pixel-level tests
# ---------------------------------------------------------------------------

@dataclass
class PixelTestResult:
    """Result of pixel-level statistical test."""
    test_name: str
    statistic: float
    p_value: float
    significant: bool     # p < 0.05
    highly_significant: bool  # p < 0.001


def ks_test_pixels(
    map_observed: np.ndarray,
    map_reference: np.ndarray,
) -> PixelTestResult:
    """Kolmogorov-Smirnov test on pixel value distributions.

    Tests whether observed and reference pixel distributions
    are drawn from the same underlying distribution.

    Low p-value → distributions differ significantly.
    """
    stat, p = sp_stats.ks_2samp(map_observed.ravel(), map_reference.ravel())
    return PixelTestResult(
        test_name="Kolmogorov-Smirnov",
        statistic=float(stat),
        p_value=float(p),
        significant=p < 0.05,
        highly_significant=p < 0.001,
    )


def anderson_darling_test(
    map_observed: np.ndarray,
) -> PixelTestResult:
    """Anderson-Darling test for Gaussianity of pixel values.

    CMB should be Gaussian (from inflation). Deviation from
    Gaussianity could indicate non-standard physics.
    """
    result = sp_stats.anderson(map_observed.ravel(), dist="norm")
    # Anderson-Darling doesn't give a simple p-value;
    # use the 5% significance level
    stat = float(result.statistic)
    # Critical values at [15%, 10%, 5%, 2.5%, 1%]
    critical_5pct = result.critical_values[2] if len(result.critical_values) > 2 else 1.0
    critical_1pct = result.critical_values[4] if len(result.critical_values) > 4 else 2.0

    return PixelTestResult(
        test_name="Anderson-Darling (Gaussianity)",
        statistic=stat,
        p_value=0.05 if stat > critical_5pct else 0.5,
        significant=stat > critical_5pct,
        highly_significant=stat > critical_1pct,
    )


# ---------------------------------------------------------------------------
# Non-Gaussianity statistics
# ---------------------------------------------------------------------------

@dataclass
class NonGaussianityResult:
    """Non-Gaussianity statistics for a CMB map."""
    skewness: float
    kurtosis: float          # excess kurtosis (0 for Gaussian)
    skewness_p: float        # p-value for skewness
    kurtosis_p: float        # p-value for kurtosis
    is_gaussian: bool        # both p > 0.05


def check_non_gaussianity(
    cmb_map: np.ndarray,
) -> NonGaussianityResult:
    """Test for non-Gaussianity using skewness and kurtosis.

    For Gaussian fields (standard LCDM prediction):
    - Skewness = 0
    - Excess kurtosis = 0

    Significant deviation could indicate:
    - Primordial non-Gaussianity (e.g., f_NL ≠ 0)
    - Secondary anisotropies (lensing, SZ effect)
    - Foreground contamination
    """
    pixels = cmb_map.ravel()

    skew = float(sp_stats.skew(pixels))
    kurt = float(sp_stats.kurtosis(pixels))  # excess kurtosis
    _, skew_p = sp_stats.skewtest(pixels)
    _, kurt_p = sp_stats.kurtosistest(pixels)

    return NonGaussianityResult(
        skewness=skew,
        kurtosis=kurt,
        skewness_p=float(skew_p),
        kurtosis_p=float(kurt_p),
        is_gaussian=(skew_p > 0.05) and (kurt_p > 0.05),
    )


# ---------------------------------------------------------------------------
# Multipole-level tests
# ---------------------------------------------------------------------------

@dataclass
class MultipoleTestResult:
    """Chi-squared test of power spectrum against theoretical prediction."""
    ell_range: tuple[int, int]
    chi_squared: float
    dof: int
    p_value: float
    reduced_chi2: float
    significant: bool
    deviant_ells: np.ndarray   # multipoles with >3σ deviation


def chi_squared_power_spectrum(
    cl_observed: np.ndarray,
    cl_theory: np.ndarray,
    l_min: int = 2,
    l_max: int | None = None,
) -> MultipoleTestResult:
    """Chi-squared test comparing observed vs theoretical C_l.

    Uses cosmic variance as the expected uncertainty:
      Var(C_l) = 2 * C_l^2 / (2l + 1)

    Low p-value → power spectrum deviates from theory.
    """
    if l_max is None:
        l_max = min(len(cl_observed), len(cl_theory)) + l_min - 1

    n = min(len(cl_observed), len(cl_theory), l_max - l_min + 1)
    cl_obs = cl_observed[:n]
    cl_th = cl_theory[:n]

    ells = np.arange(l_min, l_min + n)
    variance = 2.0 * cl_th**2 / (2.0 * ells + 1.0)

    mask = variance > 0
    chi2_per_ell = np.zeros(n)
    chi2_per_ell[mask] = (cl_obs[mask] - cl_th[mask])**2 / variance[mask]

    chi2 = float(chi2_per_ell[mask].sum())
    dof = int(mask.sum())
    p = float(1.0 - sp_stats.chi2.cdf(chi2, dof)) if dof > 0 else 1.0

    deviant = ells[chi2_per_ell > 9.0]  # > 3σ

    return MultipoleTestResult(
        ell_range=(l_min, l_min + n - 1),
        chi_squared=chi2,
        dof=dof,
        p_value=p,
        reduced_chi2=chi2 / max(dof, 1),
        significant=p < 0.05,
        deviant_ells=deviant,
    )


# ---------------------------------------------------------------------------
# Monte Carlo significance
# ---------------------------------------------------------------------------

@dataclass
class MonteCarloSignificance:
    """Significance from Monte Carlo comparison."""
    observed_statistic: float
    simulated_statistics: np.ndarray
    p_value: float
    n_simulations: int
    sigma_equivalent: float


def monte_carlo_significance(
    observed_statistic: float,
    simulated_statistics: np.ndarray,
) -> MonteCarloSignificance:
    """Compute p-value from Monte Carlo simulations.

    p = fraction of simulations with statistic >= observed.

    This is the most robust significance estimate: it doesn't
    assume any distributional form.
    """
    n_sim = len(simulated_statistics)
    n_exceed = np.sum(simulated_statistics >= observed_statistic)
    p = float((n_exceed + 1) / (n_sim + 1))  # +1 to avoid p=0

    # Convert to sigma equivalent
    sigma = float(sp_stats.norm.isf(p)) if p < 0.5 else 0.0

    return MonteCarloSignificance(
        observed_statistic=observed_statistic,
        simulated_statistics=simulated_statistics,
        p_value=p,
        n_simulations=n_sim,
        sigma_equivalent=sigma,
    )
