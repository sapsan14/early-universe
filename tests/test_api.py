"""Tests for Phase 7: FastAPI service endpoints.

Uses FastAPI TestClient — no real HTTP server needed.
"""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from archeon.api.service import app

client = TestClient(app)


# ===================================================================
# Health
# ===================================================================

class TestHealth:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ===================================================================
# Spectrum endpoint
# ===================================================================

class TestSpectrum:
    def test_spectrum_default_params(self):
        resp = client.post("/api/v1/spectrum", json={
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
            "l_max": 100,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "ell" in data
        assert "cl" in data
        assert len(data["ell"]) > 0
        assert len(data["cl"]) == len(data["ell"])
        assert data["inference_time_ms"] >= 0

    def test_spectrum_custom_params(self):
        resp = client.post("/api/v1/spectrum", json={
            "params": {
                "H0": 70.0, "Omega_b_h2": 0.023,
                "Omega_cdm_h2": 0.11, "n_s": 0.97,
                "ln10As": 3.1, "tau_reio": 0.06,
            },
            "l_max": 50,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert all(c > 0 for c in data["cl"])

    def test_spectrum_validation_error(self):
        resp = client.post("/api/v1/spectrum", json={
            "params": {"H0": 200},  # out of range
        })
        assert resp.status_code == 422


# ===================================================================
# Inference endpoint
# ===================================================================

class TestInference:
    def _make_map(self, size=64):
        rng = np.random.default_rng(42)
        return rng.standard_normal((size, size)).tolist()

    def test_inference_cnn(self):
        resp = client.post("/api/v1/inference", json={
            "map_data": self._make_map(),
            "method": "cnn",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["parameters"]) > 0
        assert data["method"] == "cnn"
        assert data["inference_time_ms"] >= 0
        for p in data["parameters"]:
            assert "name" in p
            assert "value" in p
            assert "uncertainty" in p

    def test_inference_ensemble(self):
        resp = client.post("/api/v1/inference", json={
            "map_data": self._make_map(),
            "method": "ensemble",
            "mc_dropout_samples": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["method"] == "ensemble"

    def test_inference_bad_method(self):
        resp = client.post("/api/v1/inference", json={
            "map_data": self._make_map(),
            "method": "nonexistent",
        })
        assert resp.status_code == 400

    def test_inference_resizes_non64_map(self):
        rng = np.random.default_rng(42)
        small_map = rng.standard_normal((32, 32)).tolist()
        resp = client.post("/api/v1/inference", json={
            "map_data": small_map,
            "method": "cnn",
        })
        assert resp.status_code == 200


# ===================================================================
# Anomaly detection endpoint
# ===================================================================

class TestAnomalies:
    def _make_map(self, size=64):
        rng = np.random.default_rng(42)
        return rng.standard_normal((size, size)).tolist()

    def test_anomalies_basic(self):
        resp = client.post("/api/v1/anomalies", json={
            "map_data": self._make_map(),
            "threshold": 3.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "global_score" in data
        assert "n_anomalies" in data
        assert "non_gaussianity" in data
        assert "skewness" in data["non_gaussianity"]
        assert "kurtosis" in data["non_gaussianity"]

    def test_anomalies_different_thresholds(self):
        map_data = self._make_map()
        r1 = client.post("/api/v1/anomalies", json={"map_data": map_data, "threshold": 2.0})
        r2 = client.post("/api/v1/anomalies", json={"map_data": map_data, "threshold": 5.0})
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d1["n_anomalies"] >= d2["n_anomalies"]


# ===================================================================
# Timeline (Cosmic Time Machine)
# ===================================================================

class TestTimeline:
    def test_timeline_present(self):
        resp = client.post("/api/v1/simulations/timeline", json={
            "log_time_seconds": 17.14,
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        ep = data["epoch"]
        assert "name" in ep
        assert "temperature_K" in ep
        assert ep["temperature_K"] > 0
        assert "key_processes" in ep
        assert len(ep["key_processes"]) > 0

    def test_timeline_bbn(self):
        resp = client.post("/api/v1/simulations/timeline", json={
            "log_time_seconds": 2.0,
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
        })
        assert resp.status_code == 200
        ep = resp.json()["epoch"]
        assert ep["name"] == "Big Bang Nucleosynthesis"

    def test_timeline_inflation(self):
        resp = client.post("/api/v1/simulations/timeline", json={
            "log_time_seconds": -35.0,
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
        })
        assert resp.status_code == 200
        ep = resp.json()["epoch"]
        assert ep["name"] == "Inflation"

    def test_timeline_temperature_decreases(self):
        early = client.post("/api/v1/simulations/timeline", json={
            "log_time_seconds": 2.0,
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
        }).json()
        late = client.post("/api/v1/simulations/timeline", json={
            "log_time_seconds": 17.0,
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
        }).json()
        assert early["epoch"]["temperature_K"] > late["epoch"]["temperature_K"]


# ===================================================================
# Playable Universe
# ===================================================================

class TestPlayable:
    def test_playable_basic(self):
        resp = client.post("/api/v1/simulations/playable", json={
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
            "grid_size": 16,
            "n_steps": 3,
            "seed": 42,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["snapshots"]) == 3
        assert len(data["redshifts"]) == 3
        assert len(data["power_spectra"]) == 3
        assert isinstance(data["structure_formed"], bool)

    def test_playable_reproducible(self):
        payload = {
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
            "grid_size": 16, "n_steps": 2, "seed": 123,
        }
        r1 = client.post("/api/v1/simulations/playable", json=payload).json()
        r2 = client.post("/api/v1/simulations/playable", json=payload).json()
        assert r1["snapshots"] == r2["snapshots"]


# ===================================================================
# Parameter Explorer
# ===================================================================

class TestExplorer:
    def test_explorer_basic(self):
        resp = client.post("/api/v1/explorer", json={
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
            "include_density": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["ell"]) > 0
        assert data["density_field"] is None

    def test_explorer_with_density(self):
        resp = client.post("/api/v1/explorer", json={
            "params": {
                "H0": 67.36, "Omega_b_h2": 0.02237,
                "Omega_cdm_h2": 0.12, "n_s": 0.9649,
                "ln10As": 3.044, "tau_reio": 0.0544,
            },
            "include_density": True,
            "grid_size": 16,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["density_field"] is not None
        assert len(data["density_field"]) == 16


# ===================================================================
# Pydantic models
# ===================================================================

class TestModels:
    def test_cosmo_params_defaults(self):
        from archeon.api.models import CosmoParams
        p = CosmoParams()
        assert p.H0 == 67.36
        assert 0 < p.tau_reio < 1

    def test_cosmo_params_validation(self):
        from archeon.api.models import CosmoParams
        with pytest.raises(Exception):
            CosmoParams(H0=200)

    def test_timeline_request(self):
        from archeon.api.models import TimelineRequest
        req = TimelineRequest(log_time_seconds=12.0)
        assert req.log_time_seconds == 12.0

    def test_playable_request_defaults(self):
        from archeon.api.models import PlayableRequest
        req = PlayableRequest()
        assert req.grid_size == 64
        assert req.n_steps == 10


# ===================================================================
# Simulations module (unit tests)
# ===================================================================

class TestSimulationsUnit:
    def test_find_epoch(self):
        from archeon.api.simulations import _find_epoch
        assert _find_epoch(-35.0)["name"] == "Inflation"
        assert _find_epoch(2.0)["name"] == "Big Bang Nucleosynthesis"
        assert _find_epoch(17.0)["name"] == "Galaxy Evolution / Present"

    def test_compute_state_today(self):
        from archeon.api.simulations import _compute_state
        state = _compute_state(17.14)
        assert state["scale_factor"] > 0
        assert state["temperature_K"] > 0
        assert state["hubble_parameter"] > 0

    def test_compute_state_early(self):
        from archeon.api.simulations import _compute_state
        early = _compute_state(2.0)
        late = _compute_state(17.0)
        assert early["temperature_K"] > late["temperature_K"]
        assert early["redshift"] > late["redshift"]
