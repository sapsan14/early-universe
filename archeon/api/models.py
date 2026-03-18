"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Cosmological parameters
# ---------------------------------------------------------------------------

class CosmoParams(BaseModel):
    """Standard 6-parameter ΛCDM cosmology."""
    H0: float = Field(67.36, ge=50, le=100, description="Hubble constant (km/s/Mpc)")
    Omega_b_h2: float = Field(0.02237, ge=0.015, le=0.030, description="Baryon density")
    Omega_cdm_h2: float = Field(0.1200, ge=0.08, le=0.20, description="CDM density")
    n_s: float = Field(0.9649, ge=0.85, le=1.10, description="Scalar spectral index")
    ln10As: float = Field(3.044, ge=2.0, le=4.0, description="ln(10^10 A_s)")
    tau_reio: float = Field(0.0544, ge=0.01, le=0.15, description="Reionization optical depth")


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

class InferenceRequest(BaseModel):
    """Request body for parameter inference from a CMB map."""
    map_data: list[list[float]] = Field(..., description="2D CMB map as nested list")
    method: str = Field("cnn", description="Inference method: cnn, mcmc, ensemble")
    n_samples: int = Field(1000, ge=10, le=100000, description="MCMC samples (if method=mcmc)")
    mc_dropout_samples: int = Field(50, ge=5, le=500, description="MC Dropout forward passes")


class ParameterEstimate(BaseModel):
    """Estimated value with uncertainty for one cosmological parameter."""
    name: str
    value: float
    uncertainty: float
    lower_68: float
    upper_68: float


class InferenceResponse(BaseModel):
    """Response for parameter inference."""
    parameters: list[ParameterEstimate]
    method: str
    inference_time_ms: float


# ---------------------------------------------------------------------------
# Spectrum emulator
# ---------------------------------------------------------------------------

class SpectrumRequest(BaseModel):
    """Request for C_l spectrum prediction."""
    params: CosmoParams = Field(default_factory=CosmoParams)
    l_max: int = Field(2500, ge=10, le=5000, description="Maximum multipole")


class SpectrumResponse(BaseModel):
    """Response with predicted power spectrum."""
    ell: list[int]
    cl: list[float]
    inference_time_ms: float


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

class AnomalyRequest(BaseModel):
    """Request for anomaly detection on a CMB map."""
    map_data: list[list[float]] = Field(..., description="2D CMB map")
    threshold: float = Field(3.0, ge=1.0, le=10.0, description="Sigma threshold for anomaly mask")


class AnomalyCandidate(BaseModel):
    """A detected anomaly region."""
    x: int
    y: int
    radius: float
    score: float
    significance: float


class AnomalyResponse(BaseModel):
    """Response for anomaly detection."""
    global_score: float
    n_anomalies: int
    candidates: list[AnomalyCandidate]
    non_gaussianity: dict
    inference_time_ms: float


# ---------------------------------------------------------------------------
# Simulations
# ---------------------------------------------------------------------------

class TimelineRequest(BaseModel):
    """Request for cosmic timeline at a specific epoch."""
    log_time_seconds: float = Field(
        17.14, ge=-36, le=17.64,
        description="log10(time in seconds). 17.14 ≈ today, -36 ≈ inflation")
    params: CosmoParams = Field(default_factory=CosmoParams)


class CosmicEpoch(BaseModel):
    """Description of the Universe at a given time."""
    name: str
    time_seconds: float
    redshift: float
    temperature_K: float
    scale_factor: float
    hubble_parameter: float
    dominant_component: str
    description: str
    key_processes: list[str]


class TimelineResponse(BaseModel):
    """Response with cosmic state at requested time."""
    epoch: CosmicEpoch
    density_field: list[list[float]] | None = None


class PlayableRequest(BaseModel):
    """Request for playable universe simulation."""
    params: CosmoParams = Field(default_factory=CosmoParams)
    grid_size: int = Field(64, ge=16, le=256, description="Simulation grid size")
    n_steps: int = Field(10, ge=1, le=100, description="Evolution steps")
    seed: int = Field(42, ge=0)


class PlayableResponse(BaseModel):
    """Response with simulation snapshots."""
    snapshots: list[list[list[float]]]
    redshifts: list[float]
    scale_factors: list[float]
    structure_formed: bool
    power_spectra: list[dict]


class ParameterExplorerRequest(BaseModel):
    """Request for parameter explorer: instant C_l + density field."""
    params: CosmoParams = Field(default_factory=CosmoParams)
    include_density: bool = Field(False, description="Also return density field snapshot")
    grid_size: int = Field(64, ge=16, le=256)


class ParameterExplorerResponse(BaseModel):
    """Response for parameter explorer."""
    ell: list[int]
    cl: list[float]
    density_field: list[list[float]] | None = None
    inference_time_ms: float
