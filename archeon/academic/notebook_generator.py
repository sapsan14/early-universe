"""Auto-generation of Jupyter notebooks for experiments.

Creates self-contained notebooks that reproduce a complete
ARCHEON experiment: data generation, model training, evaluation,
and visualization — all with a single "Run All".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class NotebookCell:
    """A single Jupyter notebook cell."""
    cell_type: str  # "code" or "markdown"
    source: str

    def to_dict(self) -> dict:
        return {
            "cell_type": self.cell_type,
            "metadata": {},
            "source": self.source.split("\n") if "\n" in self.source else [self.source],
            **({"outputs": [], "execution_count": None}
               if self.cell_type == "code" else {}),
        }


def _md(text: str) -> NotebookCell:
    return NotebookCell("markdown", text)


def _code(code: str) -> NotebookCell:
    return NotebookCell("code", code)


# ---------------------------------------------------------------------------
# Notebook templates
# ---------------------------------------------------------------------------

def generate_inference_notebook(
    model_name: str = "BayesianCNN",
    n_samples: int = 100,
    l_max: int = 2500,
    seed: int = 42,
) -> list[NotebookCell]:
    """Generate notebook for CMB parameter inference experiment."""
    cells = [
        _md(f"# ARCHEON: {model_name} Parameter Inference\n\n"
            "Auto-generated notebook. Run all cells to reproduce the experiment."),

        _md("## 1. Setup"),
        _code(
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "import torch\n"
            f"SEED = {seed}\n"
            f"N_SAMPLES = {n_samples}\n"
            f"L_MAX = {l_max}\n"
            "np.random.seed(SEED)\n"
            "torch.manual_seed(SEED)"
        ),

        _md("## 2. Generate Synthetic Data"),
        _code(
            "from archeon.ml.emulator import generate_training_data\n"
            "theta, cl = generate_training_data(n_samples=N_SAMPLES, l_max=L_MAX, seed=SEED)\n"
            f'print(f"Generated {{theta.shape[0]}} samples, {{theta.shape[1]}} params, '
            f'{{cl.shape[1]}} multipoles")'
        ),

        _md("## 3. Train Emulator"),
        _code(
            "from archeon.ml.emulator import ClEmulator, train_emulator\n"
            "model = ClEmulator(n_params=6, n_ell=cl.shape[1], hidden_dim=128, n_blocks=3)\n"
            "result = train_emulator(model, theta, cl, n_epochs=50, batch_size=32)\n"
            "print(f'Best epoch: {result[\"best_epoch\"]}')\n"
            "plt.figure(figsize=(8, 4))\n"
            "plt.plot(result['train_losses'], label='Train')\n"
            "plt.plot(result['val_losses'], label='Val')\n"
            "plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend()\n"
            "plt.title('Training History')\n"
            "plt.tight_layout(); plt.show()"
        ),

        _md("## 4. Evaluate"),
        _code(
            "from archeon.ml.emulator import benchmark_emulator\n"
            "ms = benchmark_emulator(model, batch_size=100, n_repeats=50)\n"
            "print(f'Inference: {ms:.3f} ms/sample')"
        ),

        _md("## 5. Visualize Predictions"),
        _code(
            "idx = 0\n"
            "pred_cl = model.predict_cl(theta[idx:idx+1])\n"
            "ell = np.arange(2, 2 + cl.shape[1])\n"
            "plt.figure(figsize=(10, 5))\n"
            "plt.loglog(ell, cl[idx], 'b-', label='True', alpha=0.7)\n"
            "plt.loglog(ell, pred_cl.ravel()[:len(ell)], 'r--', label='Predicted', alpha=0.7)\n"
            "plt.xlabel(r'$\\ell$'); plt.ylabel(r'$C_\\ell$')\n"
            "plt.legend(); plt.title('Spectrum Comparison')\n"
            "plt.tight_layout(); plt.show()"
        ),

        _md("## 6. Record Experiment"),
        _code(
            "from archeon.academic.citation import SimulationRecord, generate_bibtex\n"
            "record = SimulationRecord(\n"
            f"    title='{model_name} Inference Experiment',\n"
            f"    model='{model_name}',\n"
            f"    parameters={{'n_samples': N_SAMPLES, 'l_max': L_MAX, 'seed': SEED}},\n"
            ")\n"
            "print(generate_bibtex(record))"
        ),
    ]
    return cells


def generate_anomaly_notebook(
    n_maps: int = 50,
    threshold: float = 3.0,
    seed: int = 42,
) -> list[NotebookCell]:
    """Generate notebook for CMB anomaly detection experiment."""
    cells = [
        _md("# ARCHEON: CMB Anomaly Detection\n\n"
            "Auto-generated notebook."),

        _md("## 1. Setup"),
        _code(
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            f"SEED = {seed}\n"
            f"N_MAPS = {n_maps}\n"
            f"THRESHOLD = {threshold}\n"
            "rng = np.random.default_rng(SEED)"
        ),

        _md("## 2. Generate Synthetic CMB Maps"),
        _code(
            "maps = rng.standard_normal((N_MAPS, 64, 64)).astype(np.float32)\n"
            "print(f'Generated {maps.shape[0]} maps of size {maps.shape[1]}x{maps.shape[2]}')"
        ),

        _md("## 3. Train Autoencoder"),
        _code(
            "from archeon.anomaly.autoencoder import CMBAutoencoder, train_autoencoder\n"
            "ae = CMBAutoencoder(input_size=64, latent_dim=32)\n"
            "losses = train_autoencoder(ae, maps, n_epochs=20, batch_size=16)\n"
            "plt.plot(losses); plt.xlabel('Epoch'); plt.ylabel('Loss')\n"
            "plt.title('Autoencoder Training'); plt.show()"
        ),

        _md("## 4. Compute Anomaly Scores"),
        _code(
            "from archeon.anomaly.autoencoder import compute_anomaly_scores\n"
            "results = compute_anomaly_scores(ae, maps[:10], threshold_sigma=THRESHOLD)\n"
            "scores = [r.global_score for r in results]\n"
            "plt.bar(range(len(scores)), scores)\n"
            "plt.xlabel('Map index'); plt.ylabel('Anomaly score')\n"
            "plt.title('Per-map anomaly scores'); plt.show()"
        ),

        _md("## 5. Statistical Tests"),
        _code(
            "from archeon.anomaly.statistical_tests import check_non_gaussianity\n"
            "for i in range(3):\n"
            "    ng = check_non_gaussianity(maps[i])\n"
            "    print(f'Map {i}: skew={ng.skewness:.3f} (p={ng.skewness_p:.3f}), '\n"
            "          f'kurt={ng.kurtosis:.3f} (p={ng.kurtosis_p:.3f}), '\n"
            "          f'gaussian={ng.is_gaussian}')"
        ),

        _md("## 6. Visualize"),
        _code(
            "fig, axes = plt.subplots(2, 5, figsize=(15, 6))\n"
            "for i in range(5):\n"
            "    axes[0, i].imshow(maps[i], cmap='RdBu_r')\n"
            "    axes[0, i].set_title(f'Map {i}')\n"
            "    axes[0, i].axis('off')\n"
            "    axes[1, i].imshow(results[i].pixel_scores, cmap='hot')\n"
            "    axes[1, i].set_title(f'Score: {results[i].global_score:.4f}')\n"
            "    axes[1, i].axis('off')\n"
            "plt.tight_layout(); plt.show()"
        ),
    ]
    return cells


def generate_alternative_cosmo_notebook() -> list[NotebookCell]:
    """Generate notebook comparing alternative cosmological models."""
    cells = [
        _md("# ARCHEON: Alternative Cosmologies Comparison\n\n"
            "Comparing expansion histories of ΛCDM, f(R), MOND, and Cyclic models."),

        _md("## 1. Setup"),
        _code(
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n"
            "from archeon.physics.alternative import (\n"
            "    LCDMCosmology, FRGravity, MONDCosmology,\n"
            "    CyclicCosmology, BraneCosmology,\n"
            "    compare_models, compute_observables,\n"
            ")"
        ),

        _md("## 2. Define Models"),
        _code(
            "models = {\n"
            "    'ΛCDM': LCDMCosmology(),\n"
            "    'f(R) strong': FRGravity(f_R0=1e-4),\n"
            "    'f(R) weak': FRGravity(f_R0=1e-6),\n"
            "    'MOND': MONDCosmology(),\n"
            "    'Cyclic': CyclicCosmology(),\n"
            "    'Brane': BraneCosmology(lambda_brane=1e3),\n"
            "}"
        ),

        _md("## 3. Expansion History H(a)"),
        _code(
            "a = np.linspace(0.01, 1.0, 500)\n"
            "results = compare_models(models, a)\n"
            "\n"
            "fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))\n"
            "for name, r in results.items():\n"
            "    ax1.plot(r['a'], r['H'], label=name)\n"
            "    ax2.plot(r['a'], r['H_ratio'], label=name)\n"
            "\n"
            "ax1.set_xlabel('Scale factor a'); ax1.set_ylabel('H(a) [km/s/Mpc]')\n"
            "ax1.set_yscale('log'); ax1.legend(); ax1.set_title('Expansion History')\n"
            "ax2.set_xlabel('Scale factor a'); ax2.set_ylabel('H / H_ΛCDM')\n"
            "ax2.axhline(1.0, color='gray', ls='--', alpha=0.5)\n"
            "ax2.legend(); ax2.set_title('Ratio to ΛCDM')\n"
            "plt.tight_layout(); plt.show()"
        ),

        _md("## 4. Equation of State w(a)"),
        _code(
            "fig, ax = plt.subplots(figsize=(8, 5))\n"
            "for name, r in results.items():\n"
            "    ax.plot(r['a'], r['w_eff'], label=name)\n"
            "ax.axhline(-1/3, color='gray', ls=':', alpha=0.5, label='w=-1/3 (accel)')\n"
            "ax.set_xlabel('Scale factor a'); ax.set_ylabel(r'$w_{eff}(a)$')\n"
            "ax.legend(); ax.set_title('Effective Equation of State')\n"
            "plt.tight_layout(); plt.show()"
        ),

        _md("## 5. Observables: d_L(z)"),
        _code(
            "z = np.linspace(0.01, 3.0, 200)\n"
            "fig, ax = plt.subplots(figsize=(8, 5))\n"
            "for name, model in models.items():\n"
            "    obs = compute_observables(model, z)\n"
            "    ax.plot(obs['z'], obs['d_L_Mpc'], label=name)\n"
            "ax.set_xlabel('Redshift z'); ax.set_ylabel(r'$d_L$ [Mpc]')\n"
            "ax.legend(); ax.set_title('Luminosity Distance')\n"
            "plt.tight_layout(); plt.show()"
        ),
    ]
    return cells


# ---------------------------------------------------------------------------
# Notebook I/O
# ---------------------------------------------------------------------------

def cells_to_notebook(cells: list[NotebookCell]) -> dict:
    """Convert list of cells to Jupyter notebook dict (nbformat 4)."""
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
        },
        "cells": [c.to_dict() for c in cells],
    }


def save_notebook(cells: list[NotebookCell], path: str | Path) -> Path:
    """Save cells as a .ipynb file."""
    nb = cells_to_notebook(cells)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(nb, f, indent=1)
    return p
