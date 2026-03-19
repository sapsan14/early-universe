# ARCHEON

**A**rchaeology of the **R**adiation-dominated **C**osmos via **H**ybrid **E**mulation and **O**bservational **N**eural Inference

*from Greek ἀρχή — origin, first cause*

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![JAX](https://img.shields.io/badge/JAX-accelerated-A855F7?logo=google&logoColor=white)](https://github.com/google/jax)
[![PyTorch](https://img.shields.io/badge/PyTorch-inference-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-server-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React_19-frontend-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](https://github.com/sapsan14/early-universe/blob/main/LICENSE)

[Overview](#overview) · [Architecture](#architecture) · [Modules](#modules) · [Quickstart](#quickstart) · [Data Sources](#data-sources) · [Testing](#testing) · [Docs](#project-documentation) · [Roadmap](#roadmap) · [License](#license)

---

## Overview

ARCHEON is an open computational platform that bridges rigorous early-universe physics, neural network-based cosmological inference, CMB anomaly detection, and an interactive browser observatory — all in a single, reproducible framework.

**What it does:**

- Solves Friedmann equations, Boltzmann hierarchy, and perturbation theory with **JIT-compiled, differentiable JAX** solvers
- Recovers cosmological parameters from CMB maps in **milliseconds** via a Bayesian CNN (vs hours for traditional MCMC)
- Detects anomalies in CMB data — Cold Spot, non-Gaussianity, hemispherical asymmetry
- Compresses the Universe into interpretable **latent spaces** with a disentangled VAE
- Serves everything through a **FastAPI** backend and **React/TypeScript** interactive observatory

**Goal:** Become a new standard at the intersection of cosmology, machine learning, and interactive scientific tools — with a direct path to an arXiv publication, a PyPI package, and a live demo.

---

## Architecture

```
                        ┌──────────────────────────────────────────────┐
                        │           Interactive Observatory            │
                        │       React 19 · TypeScript · WebGPU         │
                        │  TimeTraveler · AnomalyMap · ParamExplorer   │
                        └──────────────────┬───────────────────────────┘
                                           │ REST API
                        ┌──────────────────┴───────────────────────────┐
                        │            API Layer — FastAPI                │
                        │     Simulation runner · Inference endpoint    │
                        └──┬──────────┬──────────┬──────────┬──────────┘
                           │          │          │          │
              ┌────────────┴┐  ┌──────┴───────┐ ┌┴────────┐ ┌┴───────────┐
              │ Physics Core│  │ Inverse Cosmo│ │   ML    │ │  Anomaly   │
              │    (JAX)    │  │              │ │  Layer  │ │ Detection  │
              │             │  │ Bayesian CNN │ │         │ │            │
              │ Friedmann   │  │ MCMC Baseline│ │ PINN    │ │ Autoencoder│
              │ Boltzmann   │  │ Uncertainty  │ │ FNO     │ │ Cold Spot  │
              │ Perturbation│  │ Calibration  │ │ Emulator│ │ Statistics │
              │ Recombine   │  │ Evaluation   │ │Training │ │ Latent     │
              │ Inflation   │  │ Validation   │ │         │ │ Analysis   │
              │ Sph. Harm.  │  │              │ │         │ │            │
              └──────┬──────┘  └──────┬───────┘ └────┬────┘ └─────┬─────┘
                     │               │              │             │
              ┌──────┴───────────────┴──────────────┴─────────────┴─────┐
              │                    Data Pipeline                         │
              │  Planck CMB · SDSS · DESI · Gaia DR3 · IllustrisTNG     │
              │  Synthetic map generator · DVC versioning · HDF5/Zarr    │
              └─────────────────────────────────────────────────────────┘
```

---

## Modules

### `archeon/physics/` — Physics Core (JAX)

| Module | Description |
|--------|-------------|
| [`friedmann.py`](archeon/physics/friedmann.py) | Friedmann equation solver — evolution of the scale factor a(t) |
| [`boltzmann.py`](archeon/physics/boltzmann.py) | Boltzmann hierarchy for photon, neutrino, and baryon multipoles |
| [`perturbations.py`](archeon/physics/perturbations.py) | Cosmological perturbation theory in synchronous gauge |
| [`recombination.py`](archeon/physics/recombination.py) | Hydrogen recombination — ionization fraction Xe(z) |
| [`inflation.py`](archeon/physics/inflation.py) | Inflation models — slow-roll, Starobinsky, natural inflation |
| [`spherical_harmonics.py`](archeon/physics/spherical_harmonics.py) | Spherical harmonic transforms for CMB sky maps |
| [`alternative.py`](archeon/physics/alternative.py) | Alternative/modified gravity and dark energy models |

All solvers are **JIT-compiled**, **auto-differentiable**, and **GPU-compatible**.

### `archeon/inverse/` — Inverse Cosmology

| Module | Description |
|--------|-------------|
| [`bayesian_cnn.py`](archeon/inverse/bayesian_cnn.py) | Bayesian CNN for parameter inference from CMB maps |
| [`mcmc_baseline.py`](archeon/inverse/mcmc_baseline.py) | MCMC baseline (emcee) for comparison |
| [`uncertainty.py`](archeon/inverse/uncertainty.py) | Uncertainty quantification and calibration |
| [`evaluation.py`](archeon/inverse/evaluation.py) | Model evaluation metrics and diagnostic plots |
| [`training.py`](archeon/inverse/training.py) | Training pipeline with checkpointing |
| [`validation.py`](archeon/inverse/validation.py) | Cross-validation against CLASS/CAMB references |

### `archeon/ml/` — Neural Emulators

| Module | Description |
|--------|-------------|
| [`pinn_friedmann.py`](archeon/ml/pinn_friedmann.py) | Physics-Informed Neural Network for Friedmann equations |
| [`fno_structure.py`](archeon/ml/fno_structure.py) | Fourier Neural Operator for structure formation |
| [`emulator.py`](archeon/ml/emulator.py) | Fast neural emulator for CMB power spectra |
| [`training.py`](archeon/ml/training.py) | Unified training loop with early stopping and scheduling |

### `archeon/anomaly/` — CMB Anomaly Detection

| Module | Description |
|--------|-------------|
| [`autoencoder.py`](archeon/anomaly/autoencoder.py) | Autoencoder for anomaly detection via reconstruction error |
| [`cold_spot.py`](archeon/anomaly/cold_spot.py) | Cold Spot detection and characterization |
| [`statistical_tests.py`](archeon/anomaly/statistical_tests.py) | Non-Gaussianity tests, hemispherical asymmetry |
| [`latent_analysis.py`](archeon/anomaly/latent_analysis.py) | Latent-space anomaly clustering and visualization |

### `archeon/compression/` — Universe Compression

| Module | Description |
|--------|-------------|
| [`vae.py`](archeon/compression/vae.py) | Variational Autoencoder for CMB map compression |
| [`disentanglement.py`](archeon/compression/disentanglement.py) | Disentanglement metrics (DCI, MIG, SAP) |
| [`interpretability.py`](archeon/compression/interpretability.py) | Latent dimension interpretability analysis |

### `archeon/data/` — Data Ingest & Synthesis

| Module | Description |
|--------|-------------|
| [`planck.py`](archeon/data/planck.py) | Planck CMB data loader |
| [`sdss.py`](archeon/data/sdss.py) | SDSS spectroscopic catalog loader |
| [`desi.py`](archeon/data/desi.py) | DESI BAO data loader |
| [`gaia.py`](archeon/data/gaia.py) | Gaia DR3 stellar catalog loader |
| [`illustris.py`](archeon/data/illustris.py) | IllustrisTNG simulation data loader |
| [`synthetic.py`](archeon/data/synthetic.py) | Synthetic CMB map generator with Latin Hypercube Sampling |
| [`priors.py`](archeon/data/priors.py) | Cosmological parameter priors |

### `archeon/api/` — Simulation API

| Module | Description |
|--------|-------------|
| [`service.py`](archeon/api/service.py) | FastAPI application with CORS, lifecycle hooks |
| [`models.py`](archeon/api/models.py) | Pydantic request/response models |
| [`simulations.py`](archeon/api/simulations.py) | Simulation runner endpoints |

### `archeon/academic/` — Publication Toolkit

| Module | Description |
|--------|-------------|
| [`citation.py`](archeon/academic/citation.py) | Citation manager (BibTeX generation) |
| [`latex_export.py`](archeon/academic/latex_export.py) | LaTeX figure and table export |
| [`notebook_generator.py`](archeon/academic/notebook_generator.py) | Reproducible Jupyter notebook generation |
| [`reproducibility.py`](archeon/academic/reproducibility.py) | Environment snapshots and reproducibility reports |

### `web/` — Interactive Observatory

React 19 + TypeScript + Vite frontend with:

| Component | Description |
|-----------|-------------|
| [`TimeTraveler.tsx`](web/src/components/TimeTraveler.tsx) | Navigate through cosmic epochs from inflation to today |
| [`AnomalyMap.tsx`](web/src/components/AnomalyMap.tsx) | Interactive CMB anomaly sky map |
| [`ParameterExplorer.tsx`](web/src/components/ParameterExplorer.tsx) | Real-time cosmological parameter adjustment |
| [`PlayableUniverse.tsx`](web/src/components/PlayableUniverse.tsx) | Particle-based universe simulation |
| [`particles.ts`](web/src/engine/particles.ts) | WebGPU particle physics engine |

---

## Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the web observatory)

### Installation

```bash
# Clone the repository
git clone https://github.com/sapsan14/early-universe.git
cd early-universe

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package with all optional dependencies
pip install -e ".[all]"
```

### Run the physics core

```python
from archeon.physics.friedmann import FriedmannSolver

solver = FriedmannSolver()
solution = solver.solve()
# solution contains scale factor a(t), Hubble parameter H(t), age of the universe
```

### Run the API server

```bash
pip install -e ".[api]"
uvicorn archeon.api.service:app --reload
# API docs at http://localhost:8000/docs
```

### Launch the web observatory

```bash
cd web
npm install
npm run dev
# Open http://localhost:5173
```

### Reproduce the data pipeline

```bash
pip install dvc
dvc repro      # generates synthetic training & validation datasets
```

---

## Data Sources

| Source | What | Link |
|--------|------|------|
| **Planck** | CMB temperature & polarization maps | [pla.esac.esa.int](https://pla.esac.esa.int) |
| **SDSS** | Galaxy spectroscopic catalog | [sdss.org](https://www.sdss.org) |
| **DESI** | BAO measurements | [desi.lbl.gov](https://www.desi.lbl.gov) |
| **Gaia DR3** | Stellar positions and parallaxes | [gea.esac.esa.int](https://gea.esac.esa.int/archive/) |
| **IllustrisTNG** | Cosmological hydrodynamic simulations | [tng-project.org](https://www.tng-project.org/data/) |

---

## Testing

```bash
# Run the full test suite
pytest

# Run with coverage
pytest --cov=archeon

# Run a specific module's tests
pytest tests/test_friedmann.py -v
```

Test suite covers: physics solvers, ML training smoke tests, inverse problem pipeline, anomaly detection, API endpoints, data loaders, and compression metrics.

---

## Project Documentation

| Document | Purpose |
|----------|---------|
| [`PLAN.md`](PLAN.md) | Master plan — architecture, phases, task tracking |
| [`KNOWLEDGE.md`](KNOWLEDGE.md) | Knowledge base — all terms, formulas, concepts |
| [`INSTRUCTIONS.md`](INSTRUCTIONS.md) | Standards and conventions for contributors |
| [`STEP1.md`](STEP1.md) | Phase 1 report: Physics Core |
| [`STEP2.md`](STEP2.md) | Phase 2 report: Data Pipeline & Inverse Cosmology |
| [`STEP3.md`](STEP3.md) | Phase 3 report: Anomaly Detection |
| [`STEP4.md`](STEP4.md) | Phase 4 report: ML Emulators |
| [`STEP5.md`](STEP5.md) | Phase 5 report: Universe Compression |
| [`STEP6.md`](STEP6.md) | Phase 6 report: API & Web Observatory |
| [`STEP7.md`](STEP7.md) | Phase 7 report: Alternative Physics |
| [`STEP8.md`](STEP8.md) | Phase 8 report: Academic Toolkit |
| [`dvc.yaml`](dvc.yaml) | DVC pipeline definition |
| [`params.yaml`](params.yaml) | Pipeline parameters |

---

## Roadmap

- [x] **Phase 1** — Physics Core: Friedmann, Boltzmann, recombination, perturbations, inflation
- [x] **Phase 2** — Data Pipeline: Planck/SDSS/DESI/Gaia loaders, synthetic generation, DVC
- [x] **Phase 3** — Inverse Cosmology: Bayesian CNN, MCMC baseline, uncertainty calibration
- [x] **Phase 4** — Anomaly Detection: autoencoder, Cold Spot, non-Gaussianity tests
- [x] **Phase 5** — ML Emulators: PINN, FNO, neural emulator
- [x] **Phase 6** — Compression: VAE latent space, disentanglement, interpretability
- [x] **Phase 7** — API & Web: FastAPI server, React observatory
- [x] **Phase 8** — Academic: citation manager, LaTeX export, reproducibility
- [ ] **Phase 9** — Validation against CLASS/CAMB, arXiv preprint, PyPI release

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Physics** | JAX, NumPy, SciPy, HEALPy, Astropy |
| **ML** | PyTorch, emcee, corner |
| **API** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | React 19, TypeScript, Vite, WebGPU |
| **Data** | HDF5, Zarr, DVC |
| **Testing** | pytest, ruff |

---

## License

This project is licensed under the [MIT License](LICENSE).

---

**Author:** Anton Sokolovas

*Built with JAX, curiosity, and a desire to understand the first moments of the Universe.*
