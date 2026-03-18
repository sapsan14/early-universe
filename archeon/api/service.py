"""FastAPI application: main service combining all ARCHEON endpoints.

Provides REST API for:
- Parameter inference from CMB maps (CNN / MCMC / Ensemble)
- C_l spectrum emulation (~1ms predictions)
- Anomaly detection on CMB maps
- Cosmic timeline (Time Machine)
- Playable Universe simulation
- Parameter Explorer (instant recalculation)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from time import perf_counter

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from archeon.api.models import (
    AnomalyRequest,
    AnomalyResponse,
    AnomalyCandidate,
    InferenceRequest,
    InferenceResponse,
    ParameterEstimate,
    SpectrumRequest,
    SpectrumResponse,
    ParameterExplorerRequest,
    ParameterExplorerResponse,
)


# ---------------------------------------------------------------------------
# Application state: lazy-loaded models
# ---------------------------------------------------------------------------

class AppState:
    """Holds loaded models and shared resources."""
    def __init__(self):
        self.emulator = None
        self.emulator_norm = None
        self.cnn = None
        self.autoencoder = None

    def ensure_emulator(self):
        if self.emulator is None:
            from archeon.ml.emulator import ClEmulator
            self.emulator = ClEmulator(n_params=6, n_ell=2499,
                                       hidden_dim=256, n_blocks=3)
            self.emulator.eval()

    def ensure_cnn(self):
        if self.cnn is None:
            from archeon.inverse.bayesian_cnn import BayesianCosmologyCNN
            self.cnn = BayesianCosmologyCNN(input_size=64)
            self.cnn.eval()

    def ensure_autoencoder(self):
        if self.autoencoder is None:
            from archeon.anomaly.autoencoder import CMBAutoencoder
            self.autoencoder = CMBAutoencoder(input_size=64)
            self.autoencoder.eval()


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # cleanup if needed


app = FastAPI(
    title="ARCHEON Observatory API",
    description="Neural cosmological inference, anomaly detection, and simulation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from archeon.api.simulations import router as sim_router
app.include_router(sim_router)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "archeon"}


# ---------------------------------------------------------------------------
# Spectrum emulation
# ---------------------------------------------------------------------------

@app.post("/api/v1/spectrum", response_model=SpectrumResponse)
async def predict_spectrum(req: SpectrumRequest):
    """Predict C_l power spectrum from cosmological parameters."""
    state.ensure_emulator()

    theta = np.array([
        req.params.H0,
        req.params.Omega_b_h2,
        req.params.Omega_cdm_h2,
        req.params.n_s,
        req.params.ln10As,
        req.params.tau_reio,
    ], dtype=np.float32).reshape(1, -1)

    t0 = perf_counter()
    cl = state.emulator.predict_cl(theta).ravel()
    elapsed_ms = (perf_counter() - t0) * 1000

    n_ell = min(len(cl), req.l_max - 1)
    ell = list(range(2, 2 + n_ell))

    return SpectrumResponse(
        ell=ell,
        cl=cl[:n_ell].tolist(),
        inference_time_ms=round(elapsed_ms, 3),
    )


# ---------------------------------------------------------------------------
# Parameter inference
# ---------------------------------------------------------------------------

@app.post("/api/v1/inference", response_model=InferenceResponse)
async def infer_parameters(req: InferenceRequest):
    """Infer cosmological parameters from a CMB map."""
    import torch

    map_arr = np.array(req.map_data, dtype=np.float32)
    if map_arr.ndim != 2:
        raise HTTPException(400, "map_data must be a 2D array")

    state.ensure_cnn()
    model = state.cnn
    img_size = map_arr.shape[0]

    tensor = torch.from_numpy(map_arr).unsqueeze(0).unsqueeze(0)
    if tensor.shape[-1] != 64 or tensor.shape[-2] != 64:
        tensor = torch.nn.functional.interpolate(tensor, size=(64, 64), mode="bilinear")

    t0 = perf_counter()

    if req.method == "cnn":
        model.eval()
        with torch.no_grad():
            mu, log_sigma = model(tensor)
        mu = mu.numpy().ravel()
        sigma = np.exp(log_sigma.numpy().ravel())
    elif req.method == "ensemble":
        from archeon.inverse.uncertainty import mc_dropout_predict
        mcd_result = mc_dropout_predict(model, tensor, n_samples=req.mc_dropout_samples)
        mu = mcd_result.mu_mean
        sigma = mcd_result.total_std
        mu = mu.ravel()
        sigma = sigma.ravel()
    else:
        raise HTTPException(400, f"Unsupported method: {req.method}. Use 'cnn' or 'ensemble'.")

    elapsed_ms = (perf_counter() - t0) * 1000

    from archeon.inverse.bayesian_cnn import PARAM_NAMES
    params = []
    for i, name in enumerate(PARAM_NAMES):
        params.append(ParameterEstimate(
            name=name,
            value=float(mu[i]),
            uncertainty=float(sigma[i]),
            lower_68=float(mu[i] - sigma[i]),
            upper_68=float(mu[i] + sigma[i]),
        ))

    return InferenceResponse(
        parameters=params,
        method=req.method,
        inference_time_ms=round(elapsed_ms, 3),
    )


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

@app.post("/api/v1/anomalies", response_model=AnomalyResponse)
async def detect_anomalies(req: AnomalyRequest):
    """Detect anomalies in a CMB map."""
    import torch
    from archeon.anomaly.autoencoder import compute_anomaly_scores
    from archeon.anomaly.statistical_tests import check_non_gaussianity

    map_arr = np.array(req.map_data, dtype=np.float32)
    if map_arr.ndim != 2:
        raise HTTPException(400, "map_data must be a 2D array")

    state.ensure_autoencoder()

    if map_arr.shape[0] != 64 or map_arr.shape[1] != 64:
        import torch
        tensor = torch.from_numpy(map_arr).unsqueeze(0).unsqueeze(0).float()
        tensor = torch.nn.functional.interpolate(tensor, size=(64, 64), mode="bilinear")
        map_arr = tensor.squeeze().numpy()

    maps_batch = map_arr[np.newaxis]  # (1, 64, 64)

    t0 = perf_counter()

    results = compute_anomaly_scores(state.autoencoder, maps_batch, threshold_sigma=req.threshold)
    amap = results[0]

    ng = check_non_gaussianity(map_arr)

    candidates = []
    if amap.anomalous_mask is not None and amap.anomalous_mask.any():
        from scipy import ndimage
        labeled, n_features = ndimage.label(amap.anomalous_mask)
        for j in range(1, min(n_features + 1, 20)):
            ys, xs = np.where(labeled == j)
            if len(xs) == 0:
                continue
            cx, cy = int(xs.mean()), int(ys.mean())
            radius = float(np.sqrt(len(xs) / np.pi))
            region_error = float(amap.pixel_scores[ys, xs].mean())
            candidates.append(AnomalyCandidate(
                x=cx, y=cy, radius=round(radius, 2),
                score=round(region_error, 4),
                significance=round(region_error / (amap.global_score + 1e-10), 2),
            ))

    elapsed_ms = (perf_counter() - t0) * 1000

    return AnomalyResponse(
        global_score=round(amap.global_score, 6),
        n_anomalies=len(candidates),
        candidates=candidates,
        non_gaussianity={
            "skewness": round(ng.skewness, 4),
            "kurtosis": round(ng.kurtosis, 4),
            "skew_pvalue": round(ng.skewness_p, 4),
            "kurt_pvalue": round(ng.kurtosis_p, 4),
            "is_gaussian": bool(ng.is_gaussian),
        },
        inference_time_ms=round(elapsed_ms, 3),
    )


# ---------------------------------------------------------------------------
# Parameter Explorer
# ---------------------------------------------------------------------------

@app.post("/api/v1/explorer", response_model=ParameterExplorerResponse)
async def parameter_explorer(req: ParameterExplorerRequest):
    """Instant C_l recalculation for parameter sliders."""
    state.ensure_emulator()

    theta = np.array([
        req.params.H0,
        req.params.Omega_b_h2,
        req.params.Omega_cdm_h2,
        req.params.n_s,
        req.params.ln10As,
        req.params.tau_reio,
    ], dtype=np.float32).reshape(1, -1)

    t0 = perf_counter()
    cl = state.emulator.predict_cl(theta).ravel()
    elapsed_ms = (perf_counter() - t0) * 1000

    n_ell = len(cl)
    ell = list(range(2, 2 + n_ell))

    density = None
    if req.include_density:
        from archeon.ml.fno_structure import generate_density_pair
        init, _ = generate_density_pair(
            size=req.grid_size, n_samples=1, seed=int(req.params.H0 * 100))
        density = init[0, 0].tolist()

    return ParameterExplorerResponse(
        ell=ell,
        cl=cl.tolist(),
        density_field=density,
        inference_time_ms=round(elapsed_ms, 3),
    )
