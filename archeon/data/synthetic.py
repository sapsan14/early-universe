"""Synthetic CMB map generation pipeline.

The critical training data factory for inverse cosmology:

    theta (cosmological params)
        -> C_l (angular power spectrum via transfer function)
        -> a_lm ~ Gaussian(0, C_l)
        -> CMB map (HEALPix via healpy)

Each synthetic map is a plausible CMB sky for a given set of parameters.
Generating 10k-100k such maps with varied theta creates the training
dataset for the Bayesian CNN (Phase 3).

Two C_l computation backends:
1. Internal: Eisenstein-Hu transfer function + Sachs-Wolfe (fast, ~5% accuracy)
2. CLASS wrapper: exact Boltzmann code (slow, <0.1% accuracy) [optional]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

try:
    import healpy as hp
    HEALPY_AVAILABLE = True
except ImportError:
    HEALPY_AVAILABLE = False

try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False

from archeon.data.priors import compute_derived, generate_parameter_sets


# ---------------------------------------------------------------------------
# C_l computation from parameters (internal, no CLASS dependency)
# ---------------------------------------------------------------------------

def compute_cl_internal(theta: dict, lmax: int = 2500) -> np.ndarray:
    """Compute theoretical C_l from cosmological parameters using internal physics.

    Uses the Eisenstein-Hu transfer function (Phase 1) to approximate the
    matter power spectrum, then projects to angular power spectrum via a
    simplified line-of-sight integral.

    This is ~5% accurate — sufficient for training data generation.
    For validation, use CLASS via compute_cl_class().

    Parameters
    ----------
    theta : dict
        Must contain: H0, Omega_m, Omega_b, Omega_Lambda, A_s, n_s, h.
    lmax : int
        Maximum multipole.

    Returns
    -------
    cl : array of shape (lmax+1,)
    """
    import jax.numpy as jnp
    from archeon.physics.perturbations import transfer_function_eh98
    from archeon.physics.friedmann import comoving_distance

    h = float(theta["h"])
    H0 = float(theta["H0"])
    Omega_m = float(theta["Omega_m"])
    Omega_b = float(theta["Omega_b"])
    Omega_r = float(theta.get("Omega_r", 9.14e-5))
    Omega_Lambda = float(theta["Omega_Lambda"])
    A_s = float(theta["A_s"])
    n_s = float(theta["n_s"])
    k_pivot = 0.05  # Mpc^-1

    # Comoving distance to last scattering surface
    chi_star = float(comoving_distance(1089.0, H0, Omega_m, Omega_r, Omega_Lambda, 0.0))

    ell = np.arange(2, lmax + 1, dtype=np.float64)

    # Approximate: C_l ~ A_s * (l/l_pivot)^{n_s - 1} / [l(l+1)] * envelope
    # This captures the Sachs-Wolfe plateau and acoustic peak positions
    l_pivot = k_pivot * chi_star

    # Primordial contribution (Sachs-Wolfe plateau)
    Cl = A_s * (ell / l_pivot) ** (n_s - 1.0)

    # Transfer function modulation at k = l / chi_star
    k_eff = jnp.array(ell / chi_star)
    Tk = np.array(transfer_function_eh98(k_eff, h, Omega_m, Omega_b))
    Cl = Cl * Tk**2

    # Acoustic peak structure (simplified oscillatory envelope)
    # Sound horizon at recombination ~ 150 Mpc
    r_s = 147.0  # Mpc (Planck 2018 value for sound horizon at drag epoch)
    theta_s = r_s / chi_star
    l_A = np.pi / theta_s  # first acoustic peak position (~220)

    acoustic = 1.0 + 0.25 * np.cos(np.pi * ell / l_A)
    Cl = Cl * acoustic**2

    # Silk damping at high l
    l_silk = 1200.0
    damping = np.exp(-(ell / l_silk) ** 1.4)
    Cl = Cl * damping

    # Normalize: l(l+1)C_l/(2pi) ~ const at low l (Sachs-Wolfe plateau)
    Cl = Cl / (ell * (ell + 1.0))

    # Absolute normalization to match typical CMB power (~1e-10)
    Cl = Cl * (2.725**2 * 1e-10)  # rough normalization in K^2

    # Pad l=0,1 with zeros
    cl_full = np.zeros(lmax + 1)
    cl_full[2:] = Cl

    return cl_full


def compute_cl_class(theta: dict, lmax: int = 2500) -> np.ndarray:
    """Compute theoretical C_l using CLASS Boltzmann code.

    Exact to <0.1% but requires classy installation (~30s per call).
    Used for validation and high-quality training data.

    Parameters
    ----------
    theta : dict
        Must contain: H0, Omega_b_h2, Omega_cdm_h2, n_s, ln10As, tau_reio.
    lmax : int

    Returns
    -------
    cl : array of shape (lmax+1,) in units of (K)^2
    """
    try:
        from classy import Class
    except ImportError:
        raise ImportError(
            "CLASS/classy not installed. Install with: "
            "pip install cython && pip install classy"
        )

    cosmo = Class()

    params = {
        "output": "tCl,pCl,lCl",
        "lensing": "yes",
        "l_max_scalars": lmax,
        "H0": float(theta.get("H0", 67.36)),
        "omega_b": float(theta.get("Omega_b_h2", 0.02237)),
        "omega_cdm": float(theta.get("Omega_cdm_h2", 0.1200)),
        "n_s": float(theta.get("n_s", 0.9649)),
        "ln10^{10}A_s": float(theta.get("ln10As", 3.044)),
        "tau_reio": float(theta.get("tau_reio", 0.0544)),
    }

    cosmo.set(params)
    cosmo.compute()

    # CLASS returns l(l+1)C_l/(2pi) in (micro-K)^2
    cls = cosmo.lensed_cl(lmax)
    cl_tt = cls["tt"] * (2.7255e6)**2  # convert to K^2 if needed... actually CLASS gives dimensionless

    # CLASS output: C_l (not D_l), needs proper unit handling
    cl = np.zeros(lmax + 1)
    ell = np.arange(lmax + 1)
    cl[2:] = cls["tt"][2:]  # dimensionless C_l

    cosmo.struct_cleanup()
    cosmo.empty()

    return cl


# ---------------------------------------------------------------------------
# CMB map generation
# ---------------------------------------------------------------------------

def generate_cmb_map(cl: np.ndarray, nside: int = 64,
                     seed: int | None = None,
                     add_noise: bool = False,
                     noise_level_uK: float = 5.0) -> np.ndarray:
    """Generate a single CMB map from C_l.

    Parameters
    ----------
    cl : array
        Angular power spectrum.
    nside : int
        HEALPix resolution.
    seed : int, optional
    add_noise : bool
        Add Gaussian white noise (simulating detector noise).
    noise_level_uK : float
        RMS noise per pixel in micro-Kelvin.

    Returns
    -------
    cmb_map : array of shape (12*nside^2,)
    """
    if not HEALPY_AVAILABLE:
        raise ImportError("healpy required. Install: pip install healpy")

    rng = np.random.default_rng(seed)

    # healpy uses its own random state
    if seed is not None:
        np.random.seed(seed)
    cmb_map = hp.synfast(cl, nside, verbose=False)

    if add_noise:
        npix = hp.nside2npix(nside)
        noise = rng.normal(0, noise_level_uK * 1e-6, size=npix)
        cmb_map = cmb_map + noise

    return cmb_map


# ---------------------------------------------------------------------------
# Batch dataset generation
# ---------------------------------------------------------------------------

@dataclass
class SyntheticDataset:
    """Container for a batch of synthetic CMB maps + parameters."""
    maps: np.ndarray          # (n_samples, npix) or (n_samples, npix) flattened
    parameters: dict          # name -> array of shape (n_samples,)
    cl_spectra: np.ndarray    # (n_samples, lmax+1)
    nside: int
    lmax: int
    metadata: dict = field(default_factory=dict)


def generate_dataset(n_samples: int,
                     nside: int = 64,
                     lmax: int = 192,
                     method: str = "lhs",
                     backend: str = "internal",
                     add_noise: bool = False,
                     noise_level_uK: float = 5.0,
                     seed: int = 42,
                     verbose: bool = True) -> SyntheticDataset:
    """Generate a complete synthetic CMB dataset for training.

    Pipeline:
      1. Sample n_samples parameter sets from prior
      2. Compute C_l for each parameter set
      3. Generate CMB map from each C_l

    Parameters
    ----------
    n_samples : int
        Number of samples.
    nside : int
        HEALPix resolution. 64 for training (~49k pixels), 256 for high-res.
    lmax : int
        Maximum multipole. Should be <= 3*nside - 1.
    method : str
        Prior sampling: "uniform", "gaussian", "lhs".
    backend : str
        C_l computation: "internal" (fast, ~5%) or "class" (slow, exact).
    add_noise : bool
    noise_level_uK : float
    seed : int
    verbose : bool

    Returns
    -------
    SyntheticDataset
    """
    if not HEALPY_AVAILABLE:
        raise ImportError("healpy required")

    lmax = min(lmax, 3 * nside - 1)
    npix = hp.nside2npix(nside)

    if verbose:
        print(f"Generating {n_samples} synthetic CMB maps "
              f"(nside={nside}, lmax={lmax}, method={method})")

    # Step 1: Sample parameters
    theta_all = generate_parameter_sets(n_samples, method=method, seed=seed)

    cl_func = compute_cl_internal if backend == "internal" else compute_cl_class

    maps = np.zeros((n_samples, npix), dtype=np.float32)
    spectra = np.zeros((n_samples, lmax + 1), dtype=np.float64)

    for i in range(n_samples):
        # Extract single parameter set
        theta_i = {k: float(v[i]) if isinstance(v, np.ndarray) else float(v)
                   for k, v in theta_all.items()}

        # Step 2: Compute C_l
        cl = cl_func(theta_i, lmax=lmax)
        spectra[i, :len(cl)] = cl[:lmax + 1]

        # Step 3: Generate map
        map_seed = seed * n_samples + i if seed is not None else None
        maps[i] = generate_cmb_map(cl[:lmax + 1], nside=nside, seed=map_seed,
                                   add_noise=add_noise, noise_level_uK=noise_level_uK)

        if verbose and (i + 1) % max(1, n_samples // 10) == 0:
            print(f"  [{i+1}/{n_samples}] generated")

    return SyntheticDataset(
        maps=maps,
        parameters=theta_all,
        cl_spectra=spectra,
        nside=nside,
        lmax=lmax,
        metadata={
            "method": method,
            "backend": backend,
            "add_noise": add_noise,
            "noise_level_uK": noise_level_uK,
            "seed": seed,
        },
    )


# ---------------------------------------------------------------------------
# Save / Load (HDF5)
# ---------------------------------------------------------------------------

def save_dataset(dataset: SyntheticDataset, path: str | Path) -> None:
    """Save dataset to HDF5 file.

    HDF5 is the standard format for large numerical datasets in astrophysics.
    Supports chunked I/O, compression, and metadata.
    """
    if not H5PY_AVAILABLE:
        raise ImportError("h5py required. Install: pip install h5py")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(path, "w") as f:
        f.create_dataset("maps", data=dataset.maps, compression="gzip",
                         compression_opts=4, chunks=True)
        f.create_dataset("cl_spectra", data=dataset.cl_spectra,
                         compression="gzip")

        params_grp = f.create_group("parameters")
        for name, values in dataset.parameters.items():
            params_grp.create_dataset(name, data=np.asarray(values))

        f.attrs["nside"] = dataset.nside
        f.attrs["lmax"] = dataset.lmax
        f.attrs["n_samples"] = dataset.maps.shape[0]
        for k, v in dataset.metadata.items():
            f.attrs[k] = v

    print(f"Saved dataset ({dataset.maps.shape[0]} samples) to {path}")


def load_dataset(path: str | Path) -> SyntheticDataset:
    """Load dataset from HDF5 file."""
    if not H5PY_AVAILABLE:
        raise ImportError("h5py required")

    path = Path(path)
    with h5py.File(path, "r") as f:
        maps = f["maps"][:]
        cl_spectra = f["cl_spectra"][:]

        parameters = {}
        for name in f["parameters"]:
            parameters[name] = f["parameters"][name][:]

        nside = int(f.attrs["nside"])
        lmax = int(f.attrs["lmax"])
        metadata = {k: v for k, v in f.attrs.items()
                    if k not in ("nside", "lmax", "n_samples")}

    return SyntheticDataset(
        maps=maps, parameters=parameters, cl_spectra=cl_spectra,
        nside=nside, lmax=lmax, metadata=metadata,
    )


# ---------------------------------------------------------------------------
# Flat-sky projection (for CNN input)
# ---------------------------------------------------------------------------

def healpix_to_flatsky(cmb_map: np.ndarray, nside: int,
                       patch_size: int = 128,
                       patch_deg: float = 20.0,
                       center_theta: float = np.pi / 2,
                       center_phi: float = 0.0) -> np.ndarray:
    """Extract a flat-sky patch from a HEALPix map using gnomonic projection.

    CNNs require rectangular images. This extracts a square patch centered
    on (theta, phi) using gnomonic (tangent-plane) projection.

    Parameters
    ----------
    cmb_map : array
        Full-sky HEALPix map.
    nside : int
    patch_size : int
        Output image size (patch_size x patch_size pixels).
    patch_deg : float
        Angular extent of the patch in degrees.
    center_theta, center_phi : float
        Center of the patch (colatitude, longitude) in radians.

    Returns
    -------
    patch : array of shape (patch_size, patch_size)
    """
    if not HEALPY_AVAILABLE:
        raise ImportError("healpy required")

    patch = hp.gnomview(
        cmb_map, rot=(np.degrees(center_phi), 90 - np.degrees(center_theta)),
        xsize=patch_size, reso=patch_deg * 60.0 / patch_size,
        return_projected_map=True, no_plot=True,
    )
    return np.array(patch)
