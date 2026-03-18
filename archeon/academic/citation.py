"""Citation and BibTeX generation for simulations.

Each ARCHEON simulation run gets a unique identifier and
auto-generated BibTeX entry for reproducibility and attribution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class SimulationRecord:
    """Complete record of a simulation run."""
    title: str = "ARCHEON simulation"
    author: str = "ARCHEON Contributors"
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    model: str = "LCDM"
    parameters: dict[str, Any] = field(default_factory=dict)
    software_version: str = "0.1.0"
    method: str = ""
    notes: str = ""

    @property
    def uid(self) -> str:
        """Deterministic unique ID from parameters + model + date."""
        content = json.dumps({
            "model": self.model,
            "parameters": self.parameters,
            "method": self.method,
            "date": self.date[:10],
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    @property
    def citation_key(self) -> str:
        """BibTeX citation key: archeon_<model>_<uid>."""
        model_clean = self.model.lower().replace(" ", "_").replace("(", "").replace(")", "")
        return f"archeon_{model_clean}_{self.uid}"


def generate_bibtex(record: SimulationRecord) -> str:
    """Generate BibTeX entry for a simulation run."""
    year = record.date[:4]
    params_str = ", ".join(
        f"{k}={v}" for k, v in sorted(record.parameters.items())
    )

    return f"""@misc{{{record.citation_key},
  title     = {{{record.title}}},
  author    = {{{record.author}}},
  year      = {{{year}}},
  note      = {{ARCHEON v{record.software_version}, model={record.model}, {params_str}}},
  howpublished = {{ARCHEON Observatory, run ID: {record.uid}}},
}}"""


def generate_data_citation(record: SimulationRecord) -> str:
    """Generate a human-readable data citation string."""
    year = record.date[:4]
    return (
        f"{record.author} ({year}). {record.title}. "
        f"ARCHEON Observatory v{record.software_version}. "
        f"Model: {record.model}. Run ID: {record.uid}."
    )


def batch_bibtex(records: list[SimulationRecord]) -> str:
    """Generate BibTeX file content for multiple simulation runs."""
    entries = [generate_bibtex(r) for r in records]
    return "\n\n".join(entries)


def record_to_json(record: SimulationRecord) -> str:
    """Serialize simulation record to JSON."""
    d = asdict(record)
    d["uid"] = record.uid
    d["citation_key"] = record.citation_key
    return json.dumps(d, indent=2, default=str)
