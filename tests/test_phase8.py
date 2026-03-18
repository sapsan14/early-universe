"""Tests for Phase 8: Alternative Cosmologies + Academic Engine."""

from __future__ import annotations

import json
import numpy as np
import pytest


# ===================================================================
# Alternative Cosmologies
# ===================================================================

class TestLCDM:
    def test_hubble_today(self):
        from archeon.physics.alternative import LCDMCosmology
        m = LCDMCosmology()
        H0 = m.hubble(1.0)
        assert abs(H0 - 67.36) < 1.0

    def test_hubble_increases_at_early_times(self):
        from archeon.physics.alternative import LCDMCosmology
        m = LCDMCosmology()
        assert m.hubble(0.01) > m.hubble(1.0)

    def test_w_eff_today_near_minus1(self):
        from archeon.physics.alternative import LCDMCosmology
        m = LCDMCosmology()
        w = m.w_eff(1.0)
        assert w < -0.5, "Should be dark energy dominated"

    def test_w_eff_early_radiation(self):
        from archeon.physics.alternative import LCDMCosmology
        m = LCDMCosmology()
        w = m.w_eff(1e-4)
        assert w > 0.2, "Radiation dominated: w → 1/3"

    def test_state(self):
        from archeon.physics.alternative import LCDMCosmology
        m = LCDMCosmology()
        s = m.state(0.5)
        assert s.a == 0.5
        assert s.H > 0

    def test_expansion_history(self):
        from archeon.physics.alternative import LCDMCosmology
        m = LCDMCosmology()
        a = np.linspace(0.01, 1.0, 100)
        hist = m.expansion_history(a)
        assert len(hist["H"]) == 100
        assert all(hist["H"] > 0)


class TestFRGravity:
    def test_recovers_gr_when_f_R0_zero(self):
        from archeon.physics.alternative import LCDMCosmology, FRGravity
        lcdm = LCDMCosmology()
        fr = FRGravity(f_R0=0.0)
        assert abs(fr.hubble(0.5) - lcdm.hubble(0.5)) < 1.0

    def test_differs_from_lcdm(self):
        from archeon.physics.alternative import LCDMCosmology, FRGravity
        lcdm = LCDMCosmology()
        fr = FRGravity(f_R0=1e-3)
        H_fr = fr.hubble(0.5)
        H_lcdm = lcdm.hubble(0.5)
        assert H_fr != H_lcdm

    def test_scalar_field_mass(self):
        from archeon.physics.alternative import FRGravity
        fr = FRGravity(f_R0=1e-5)
        mass = fr.scalar_field_mass(1.0)
        assert mass > 0

    def test_stronger_f_R0_bigger_difference(self):
        from archeon.physics.alternative import FRGravity, LCDMCosmology
        fr_weak = FRGravity(f_R0=1e-6)
        fr_strong = FRGravity(f_R0=0.1)
        lcdm = LCDMCosmology()
        diff_weak = abs(fr_weak.hubble(1.0) - lcdm.hubble(1.0))
        diff_strong = abs(fr_strong.hubble(1.0) - lcdm.hubble(1.0))
        assert diff_strong > diff_weak


class TestMOND:
    def test_hubble_positive(self):
        from archeon.physics.alternative import MONDCosmology
        m = MONDCosmology()
        assert m.hubble(0.5) > 0

    def test_w_eff_reasonable(self):
        from archeon.physics.alternative import MONDCosmology
        m = MONDCosmology()
        w = m.w_eff(1.0)
        assert -1.5 < w < 0

    def test_no_cdm(self):
        from archeon.physics.alternative import MONDCosmology
        m = MONDCosmology()
        assert m.Omega_b < 0.1


class TestVaryingConstants:
    def test_no_variation_matches_lcdm(self):
        from archeon.physics.alternative import VaryingConstantsCosmology, LCDMCosmology
        vc = VaryingConstantsCosmology()
        lcdm = LCDMCosmology()
        assert abs(vc.hubble(0.5) - lcdm.hubble(0.5)) < 1.0

    def test_varying_G_affects_hubble(self):
        from archeon.physics.alternative import VaryingConstantsCosmology
        vc = VaryingConstantsCosmology(delta_G=0.1)
        vc0 = VaryingConstantsCosmology(delta_G=0.0)
        assert vc.hubble(0.5) != vc0.hubble(0.5)

    def test_recombination_shift(self):
        from archeon.physics.alternative import VaryingConstantsCosmology
        vc = VaryingConstantsCosmology(delta_alpha=1e-5)
        shift = vc.recombination_shift()
        assert abs(shift - 2e-5) < 1e-10

    def test_bbn_helium_shift(self):
        from archeon.physics.alternative import VaryingConstantsCosmology
        vc = VaryingConstantsCosmology(delta_G=0.01)
        shift = vc.bbn_helium_shift()
        assert abs(shift) > 0


class TestCyclic:
    def test_hubble_positive(self):
        from archeon.physics.alternative import CyclicCosmology
        m = CyclicCosmology()
        for a in [0.01, 0.1, 0.5, 1.0]:
            assert m.hubble(a) > 0

    def test_time_to_turnaround(self):
        from archeon.physics.alternative import CyclicCosmology
        m = CyclicCosmology(cycle_period=3.0)
        t = m.time_to_turnaround()
        assert t > 0


class TestBrane:
    def test_recovers_lcdm_large_tension(self):
        from archeon.physics.alternative import BraneCosmology, LCDMCosmology
        brane = BraneCosmology(lambda_brane=1e10)
        lcdm = LCDMCosmology()
        assert abs(brane.hubble(0.5) - lcdm.hubble(0.5)) < 0.5

    def test_high_energy_correction(self):
        from archeon.physics.alternative import BraneCosmology
        brane = BraneCosmology(lambda_brane=1e2)
        lcdm_H = 67.36 * np.sqrt(0.3153 / 0.01**3 + 0.6847)
        brane_H = brane.hubble(0.01)
        assert brane_H > lcdm_H

    def test_extra_dimension_scale(self):
        from archeon.physics.alternative import BraneCosmology
        brane = BraneCosmology()
        scale = brane.extra_dimension_scale(0.5)
        assert scale > 0


class TestModelComparison:
    def test_compare_models(self):
        from archeon.physics.alternative import (
            LCDMCosmology, FRGravity, compare_models)
        models = {"LCDM": LCDMCosmology(), "f(R)": FRGravity(f_R0=1e-4)}
        a = np.linspace(0.01, 1.0, 50)
        results = compare_models(models, a)
        assert "LCDM" in results
        assert "f(R)" in results
        np.testing.assert_allclose(results["LCDM"]["H_ratio"], 1.0)

    def test_compute_observables(self):
        from archeon.physics.alternative import LCDMCosmology, compute_observables
        m = LCDMCosmology()
        z = np.linspace(0.01, 2.0, 50)
        obs = compute_observables(m, z)
        assert len(obs["d_L_Mpc"]) == 50
        assert all(obs["d_L_Mpc"] >= 0)
        assert obs["d_L_Mpc"][-1] > obs["d_L_Mpc"][0]


# ===================================================================
# Academic Engine: LaTeX
# ===================================================================

class TestLatexExport:
    def test_parameters_to_latex(self):
        from archeon.academic.latex_export import parameters_to_latex
        tex = parameters_to_latex(
            ["H0", "Omega_m"], np.array([67.36, 0.315]),
            np.array([0.5, 0.007]), method="CNN")
        assert r"\begin{table}" in tex
        assert "67.3600" in tex

    def test_parameters_to_latex_with_method_in_header(self):
        from archeon.academic.latex_export import parameters_to_latex
        tex = parameters_to_latex(
            ["H0"], np.array([67.36]), np.array([0.5]),
            method="CNN", reference={"H0": 67.36})
        assert "CNN" in tex

    def test_parameters_with_reference(self):
        from archeon.academic.latex_export import parameters_to_latex
        tex = parameters_to_latex(
            ["H0"], np.array([67.5]), np.array([0.5]),
            reference={"H0": 67.36})
        assert r"\sigma" in tex

    def test_comparison_to_latex(self):
        from archeon.academic.latex_export import comparison_to_latex
        methods = {
            "CNN": (np.array([67.0, 0.31]), np.array([0.5, 0.01])),
            "MCMC": (np.array([67.3, 0.315]), np.array([0.3, 0.005])),
        }
        tex = comparison_to_latex(methods, ["H0", "Omega_m"])
        assert r"\begin{table*}" in tex
        assert "CNN" in tex
        assert "MCMC" in tex

    def test_journal_styles_exist(self):
        from archeon.academic.latex_export import JOURNAL_STYLES
        assert "apj" in JOURNAL_STYLES
        assert "mnras" in JOURNAL_STYLES
        assert "aa" in JOURNAL_STYLES


# ===================================================================
# Academic Engine: Citation
# ===================================================================

class TestCitation:
    def test_simulation_record_uid(self):
        from archeon.academic.citation import SimulationRecord
        r = SimulationRecord(model="LCDM", parameters={"H0": 67.36})
        assert len(r.uid) == 12

    def test_uid_deterministic(self):
        from archeon.academic.citation import SimulationRecord
        r1 = SimulationRecord(model="LCDM", parameters={"H0": 67.36}, date="2025-01-01")
        r2 = SimulationRecord(model="LCDM", parameters={"H0": 67.36}, date="2025-01-01")
        assert r1.uid == r2.uid

    def test_uid_changes_with_params(self):
        from archeon.academic.citation import SimulationRecord
        r1 = SimulationRecord(model="LCDM", parameters={"H0": 67.36}, date="2025-01-01")
        r2 = SimulationRecord(model="LCDM", parameters={"H0": 70.0}, date="2025-01-01")
        assert r1.uid != r2.uid

    def test_generate_bibtex(self):
        from archeon.academic.citation import SimulationRecord, generate_bibtex
        r = SimulationRecord(model="f(R)", parameters={"f_R0": 1e-5})
        bib = generate_bibtex(r)
        assert "@misc{" in bib
        assert "archeon" in bib
        assert "f_R0" in bib

    def test_data_citation(self):
        from archeon.academic.citation import SimulationRecord, generate_data_citation
        r = SimulationRecord(title="Test Run", model="LCDM")
        cite = generate_data_citation(r)
        assert "ARCHEON" in cite
        assert "Test Run" in cite

    def test_batch_bibtex(self):
        from archeon.academic.citation import SimulationRecord, batch_bibtex
        records = [
            SimulationRecord(model="A", parameters={"x": 1}, date="2025-01-01"),
            SimulationRecord(model="B", parameters={"y": 2}, date="2025-01-01"),
        ]
        bib = batch_bibtex(records)
        assert bib.count("@misc{") == 2

    def test_record_to_json(self):
        from archeon.academic.citation import SimulationRecord, record_to_json
        r = SimulationRecord(model="LCDM")
        j = json.loads(record_to_json(r))
        assert "uid" in j
        assert "citation_key" in j


# ===================================================================
# Academic Engine: Reproducibility
# ===================================================================

class TestReproducibility:
    def test_environment_capture(self):
        from archeon.academic.reproducibility import EnvironmentInfo
        env = EnvironmentInfo.capture()
        assert len(env.python_version) > 0
        assert env.cpu_count > 0
        assert "numpy" in env.packages

    def test_create_experiment(self):
        from archeon.academic.reproducibility import create_experiment
        exp = create_experiment("test", {"lr": 0.001}, seeds={"main": 42})
        assert exp.name == "test"
        assert exp.seeds["main"] == 42
        assert len(exp.uid) == 16

    def test_save_load_experiment(self, tmp_path):
        from archeon.academic.reproducibility import (
            create_experiment, save_experiment, load_experiment)
        exp = create_experiment("test", {"lr": 0.001})
        path = save_experiment(exp, tmp_path)
        assert path.exists()
        loaded = load_experiment(path)
        assert loaded.name == "test"
        assert loaded.parameters["lr"] == 0.001

    def test_verify_reproducibility(self):
        from archeon.academic.reproducibility import (
            create_experiment, verify_reproducibility)
        exp = create_experiment("test", {})
        exp.environment.python_version = "fake"
        checks = verify_reproducibility(exp)
        assert checks["python_version"] is False

    def test_checksum_file(self, tmp_path):
        from archeon.academic.reproducibility import checksum_file
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        cs = checksum_file(f)
        assert len(cs) == 64  # SHA256


# ===================================================================
# Academic Engine: Notebook Generator
# ===================================================================

class TestNotebookGenerator:
    def test_inference_notebook(self):
        from archeon.academic.notebook_generator import (
            generate_inference_notebook, cells_to_notebook)
        cells = generate_inference_notebook(n_samples=10)
        nb = cells_to_notebook(cells)
        assert nb["nbformat"] == 4
        assert len(nb["cells"]) > 0
        code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        assert len(code_cells) >= 4

    def test_anomaly_notebook(self):
        from archeon.academic.notebook_generator import generate_anomaly_notebook
        cells = generate_anomaly_notebook(n_maps=5)
        assert any("autoencoder" in c.source.lower() for c in cells)

    def test_alternative_cosmo_notebook(self):
        from archeon.academic.notebook_generator import generate_alternative_cosmo_notebook
        cells = generate_alternative_cosmo_notebook()
        assert any("FRGravity" in c.source for c in cells)

    def test_save_notebook(self, tmp_path):
        from archeon.academic.notebook_generator import (
            generate_inference_notebook, save_notebook)
        cells = generate_inference_notebook(n_samples=5)
        path = save_notebook(cells, tmp_path / "test.ipynb")
        assert path.exists()
        nb = json.loads(path.read_text())
        assert "cells" in nb
