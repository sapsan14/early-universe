"""Configuration loading for cosmological parameters."""

from pathlib import Path

import yaml

_CONFIG_DIR = Path(__file__).parent


def load_config(name: str = "planck2018") -> dict:
    """Load a cosmological parameter set by name.

    Parameters
    ----------
    name : str
        Config name without extension (e.g. "planck2018").

    Returns
    -------
    dict
        Nested dictionary with 'cosmology', 'physical_constants', 'units' keys.
    """
    path = _CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Config '{name}' not found at {path}")
    with open(path) as f:
        return yaml.safe_load(f)


def get_cosmology(name: str = "planck2018") -> dict:
    """Return only the cosmology section of a config."""
    return load_config(name)["cosmology"]


def get_constants(name: str = "planck2018") -> dict:
    """Return physical constants from a config."""
    return load_config(name)["physical_constants"]
