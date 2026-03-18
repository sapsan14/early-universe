"""Reproducibility engine: capture and restore full experiment state.

Records everything needed to reproduce a simulation:
- Code version (git hash)
- All parameters
- Random seeds
- Python/library versions
- Hardware info
- Output checksums
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EnvironmentInfo:
    """Captured compute environment."""
    python_version: str = ""
    platform: str = ""
    hostname: str = ""
    cpu_count: int = 0
    packages: dict[str, str] = field(default_factory=dict)
    git_hash: str = ""
    git_dirty: bool = False

    @classmethod
    def capture(cls) -> EnvironmentInfo:
        info = cls()
        info.python_version = sys.version
        info.platform = platform.platform()
        info.hostname = platform.node()
        info.cpu_count = os.cpu_count() or 0

        # Key packages
        for pkg in ["numpy", "scipy", "torch", "jax", "fastapi", "archeon"]:
            try:
                mod = __import__(pkg)
                info.packages[pkg] = getattr(mod, "__version__", "unknown")
            except ImportError:
                pass

        # Git info
        try:
            info.git_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL).decode().strip()
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                stderr=subprocess.DEVNULL).decode().strip()
            info.git_dirty = len(status) > 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            info.git_hash = "not_a_git_repo"

        return info


@dataclass
class ExperimentRecord:
    """Full experiment record for reproducibility."""
    name: str = ""
    description: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    environment: EnvironmentInfo = field(default_factory=EnvironmentInfo)
    parameters: dict[str, Any] = field(default_factory=dict)
    seeds: dict[str, int] = field(default_factory=dict)
    inputs: dict[str, str] = field(default_factory=dict)   # path → checksum
    outputs: dict[str, str] = field(default_factory=dict)  # path → checksum
    metrics: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    @property
    def uid(self) -> str:
        content = json.dumps({
            "name": self.name,
            "parameters": self.parameters,
            "seeds": self.seeds,
            "timestamp": self.timestamp[:10],
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


def checksum_file(path: str | Path) -> str:
    """Compute SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def create_experiment(
    name: str,
    parameters: dict[str, Any],
    seeds: dict[str, int] | None = None,
    description: str = "",
    tags: list[str] | None = None,
) -> ExperimentRecord:
    """Create a new experiment record with environment capture."""
    return ExperimentRecord(
        name=name,
        description=description,
        environment=EnvironmentInfo.capture(),
        parameters=parameters,
        seeds=seeds or {},
        tags=tags or [],
    )


def save_experiment(record: ExperimentRecord, directory: str | Path) -> Path:
    """Save experiment record to JSON file."""
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"experiment_{record.uid}.json"
    with open(path, "w") as f:
        json.dump(asdict(record), f, indent=2, default=str)
    return path


def load_experiment(path: str | Path) -> ExperimentRecord:
    """Load experiment record from JSON."""
    with open(path) as f:
        data = json.load(f)
    env_data = data.pop("environment", {})
    env = EnvironmentInfo(**env_data)
    return ExperimentRecord(environment=env, **data)


def verify_reproducibility(record: ExperimentRecord) -> dict[str, bool]:
    """Check if current environment matches the recorded one."""
    current = EnvironmentInfo.capture()
    checks = {
        "python_version": current.python_version.split()[0] == record.environment.python_version.split()[0],
        "git_hash": current.git_hash == record.environment.git_hash,
        "git_clean": not current.git_dirty,
    }
    for pkg, version in record.environment.packages.items():
        current_ver = current.packages.get(pkg, "missing")
        checks[f"pkg_{pkg}"] = current_ver == version

    return checks
