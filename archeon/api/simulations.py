"""Simulation endpoints: Cosmic Time Machine, Playable Universe.

Provides physical state of the Universe at any epoch and sandbox-mode
simulations where users can modify fundamental constants.
"""

from __future__ import annotations

from time import perf_counter

import numpy as np
from fastapi import APIRouter

from archeon.api.models import (
    CosmicEpoch,
    TimelineRequest,
    TimelineResponse,
    PlayableRequest,
    PlayableResponse,
)

router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])


# ---------------------------------------------------------------------------
# Cosmic epochs database
# ---------------------------------------------------------------------------

EPOCHS = [
    {
        "name": "Planck Epoch",
        "log_t_min": -43.5, "log_t_max": -36,
        "description": "Все четыре фундаментальные силы объединены. "
                       "Квантовая гравитация доминирует. Общая теория относительности неприменима.",
        "key_processes": ["Quantum gravity", "Grand unification"],
        "dominant": "quantum_fields",
    },
    {
        "name": "Inflation",
        "log_t_min": -36, "log_t_max": -32,
        "description": "Экспоненциальное расширение пространства: объём увеличивается в ~e^60 раз. "
                       "Генерируются первичные квантовые флуктуации — зародыши галактик.",
        "key_processes": ["Exponential expansion", "Quantum fluctuation generation",
                          "Flatness and horizon problem resolution"],
        "dominant": "inflaton_field",
    },
    {
        "name": "Reheating / Quark Epoch",
        "log_t_min": -32, "log_t_max": -10,
        "description": "Энергия инфлатона переходит в частицы. Кварк-глюонная плазма. "
                       "Барионная асимметрия формируется.",
        "key_processes": ["Reheating", "Baryogenesis", "Quark-gluon plasma"],
        "dominant": "radiation",
    },
    {
        "name": "QCD Phase Transition",
        "log_t_min": -10, "log_t_max": -4,
        "description": "Кварки конфайнируются в протоны и нейтроны. "
                       "Температура: ~150 МэВ ≈ 1.7 × 10^12 K.",
        "key_processes": ["Quark confinement", "Hadron formation"],
        "dominant": "radiation",
    },
    {
        "name": "Big Bang Nucleosynthesis",
        "log_t_min": -4, "log_t_max": 3,
        "description": "Синтез лёгких ядер: ~75% H, ~25% He-4, следы D, Li-7. "
                       "Длится ~3 минуты. Предсказания BBN точно совпадают с наблюдениями.",
        "key_processes": ["Deuterium formation", "Helium-4 synthesis",
                          "Neutron-to-proton freeze-out"],
        "dominant": "radiation",
    },
    {
        "name": "Matter-Radiation Equality",
        "log_t_min": 3, "log_t_max": 11,
        "description": "Плотность энергии материи сравнивается с излучением. "
                       "z ≈ 3400. Начинается гравитационный рост структур.",
        "key_processes": ["Matter domination onset", "Structure growth begins"],
        "dominant": "matter",
    },
    {
        "name": "Recombination / CMB Release",
        "log_t_min": 11, "log_t_max": 13,
        "description": "Электроны рекомбинируют с протонами → нейтральный водород. "
                       "Фотоны свободно распространяются = CMB. z ≈ 1100, T ≈ 3000 K.",
        "key_processes": ["Hydrogen recombination", "Photon decoupling",
                          "CMB last scattering surface"],
        "dominant": "matter",
    },
    {
        "name": "Dark Ages",
        "log_t_min": 13, "log_t_max": 15.5,
        "description": "Нет источников света. Тёмная материя формирует гравитационные потенциалы. "
                       "Барионы падают в эти потенциалы.",
        "key_processes": ["Dark matter halo formation", "Gas accretion"],
        "dominant": "matter",
    },
    {
        "name": "Cosmic Dawn / Reionization",
        "log_t_min": 15.5, "log_t_max": 16.3,
        "description": "Первые звёзды и галактики. Ультрафиолет реионизирует межгалактический водород. "
                       "z ≈ 6–20.",
        "key_processes": ["First stars (Population III)", "Galaxy formation",
                          "Reionization of hydrogen"],
        "dominant": "matter",
    },
    {
        "name": "Galaxy Evolution / Present",
        "log_t_min": 16.3, "log_t_max": 17.64,
        "description": "Формирование крупномасштабной структуры: скопления, филаменты, войды. "
                       "Тёмная энергия ускоряет расширение (z < 0.7).",
        "key_processes": ["Galaxy clusters", "Large-scale structure",
                          "Dark energy domination", "Accelerated expansion"],
        "dominant": "dark_energy",
    },
]


def _find_epoch(log_t: float) -> dict:
    for ep in EPOCHS:
        if ep["log_t_min"] <= log_t < ep["log_t_max"]:
            return ep
    if log_t >= EPOCHS[-1]["log_t_max"]:
        return EPOCHS[-1]
    return EPOCHS[0]


def _compute_state(log_t: float, H0: float = 67.36,
                   Omega_m: float = 0.315, Omega_r: float = 9.1e-5,
                   Omega_Lambda: float = 0.685) -> dict:
    """Compute physical state of the Universe at log10(t/seconds)."""
    t_sec = 10.0 ** log_t

    T_CMB_0 = 2.7255  # K today
    t_age_universe = 13.8e9 * 3.156e7  # seconds

    if log_t < 13:
        # Radiation-dominated: a ∝ t^(1/2), T ∝ 1/a
        a = min((t_sec / t_age_universe) ** 0.5, 1.0)
    elif log_t < 16.8:
        # Matter-dominated: a ∝ t^(2/3)
        a = min((t_sec / t_age_universe) ** (2.0 / 3.0), 1.0)
    else:
        a = min((t_sec / t_age_universe) ** 0.7, 1.0)

    a = max(a, 1e-30)
    z = 1.0 / a - 1.0
    T = T_CMB_0 / a

    H2 = H0**2 * (Omega_r / a**4 + Omega_m / a**3 + Omega_Lambda)
    H = np.sqrt(max(H2, 0))

    if Omega_r / a**4 > Omega_m / a**3 and Omega_r / a**4 > Omega_Lambda:
        dominant = "radiation"
    elif Omega_m / a**3 > Omega_Lambda:
        dominant = "matter"
    else:
        dominant = "dark_energy"

    return {
        "redshift": float(z),
        "temperature_K": float(T),
        "scale_factor": float(a),
        "hubble_parameter": float(H),
        "dominant_component": dominant,
    }


# ---------------------------------------------------------------------------
# Cosmic Time Machine
# ---------------------------------------------------------------------------

@router.post("/timeline", response_model=TimelineResponse)
async def cosmic_timeline(req: TimelineRequest):
    """Get physical state of the Universe at a given time."""
    epoch_info = _find_epoch(req.log_time_seconds)

    h = req.params.H0 / 100.0
    Omega_m = (req.params.Omega_b_h2 + req.params.Omega_cdm_h2) / h**2

    physical = _compute_state(
        req.log_time_seconds,
        H0=req.params.H0,
        Omega_m=Omega_m,
        Omega_Lambda=1.0 - Omega_m - 9.1e-5,
    )

    return TimelineResponse(
        epoch=CosmicEpoch(
            name=epoch_info["name"],
            time_seconds=10.0 ** req.log_time_seconds,
            redshift=physical["redshift"],
            temperature_K=physical["temperature_K"],
            scale_factor=physical["scale_factor"],
            hubble_parameter=physical["hubble_parameter"],
            dominant_component=physical["dominant_component"],
            description=epoch_info["description"],
            key_processes=epoch_info["key_processes"],
        ),
        density_field=None,
    )


# ---------------------------------------------------------------------------
# Playable Universe
# ---------------------------------------------------------------------------

@router.post("/playable", response_model=PlayableResponse)
async def playable_universe(req: PlayableRequest):
    """Sandbox simulation: modify constants and see structure formation."""
    rng = np.random.default_rng(req.seed)
    size = req.grid_size
    n_steps = req.n_steps

    h = req.params.H0 / 100.0
    Omega_m = (req.params.Omega_b_h2 + req.params.Omega_cdm_h2) / h**2
    n_s = req.params.n_s
    A_s = np.exp(req.params.ln10As) * 1e-10

    kx = np.fft.fftfreq(size, d=1.0 / size)
    ky = np.fft.fftfreq(size, d=1.0 / size)
    KX, KY = np.meshgrid(kx, ky)
    k2 = KX**2 + KY**2
    k2[0, 0] = 1.0
    k_abs = np.sqrt(k2)
    k_abs[0, 0] = 1.0

    pk_init = A_s * 1e9 * k_abs ** (n_s - 1.0)
    pk_init[0, 0] = 0.0

    noise = rng.standard_normal((size, size)) + 1j * rng.standard_normal((size, size))
    delta_k = noise * np.sqrt(pk_init)
    delta_init = np.real(np.fft.ifft2(delta_k)).astype(np.float32)
    delta_init /= (delta_init.std() + 1e-10)

    # Evolve through n_steps from z_start to z=0
    z_start = 1100.0
    z_end = 0.0
    redshifts = np.geomspace(z_start, max(z_end, 0.01), n_steps + 1)[1:]
    scale_factors = 1.0 / (1.0 + redshifts)

    # Growth factor ~ integral depending on Omega_m
    snapshots = []
    power_spectra = []

    for i, z_i in enumerate(redshifts):
        a_i = 1.0 / (1.0 + z_i)
        # Linear growth factor approximation (Carroll+ 1992)
        Omega_m_z = Omega_m / (Omega_m + (1 - Omega_m) * a_i**3)
        D = a_i * (5 * Omega_m_z / 2.0) / (
            Omega_m_z**(4.0/7.0) - (1 - Omega_m_z) + (1 + Omega_m_z / 2.0) * (1 + (1 - Omega_m_z) / 70.0)
        )
        D_norm = D / (5 * Omega_m / 2.0)

        # Lognormal for nonlinear
        growth = max(D_norm * 5.0, 0.01)
        delta_evolved = np.exp(growth * delta_init - 0.5 * growth**2) - 1.0
        delta_evolved = delta_evolved / (delta_evolved.std() + 1e-10)

        snapshots.append(delta_evolved.tolist())

        # Power spectrum
        fk = np.fft.fft2(delta_evolved)
        pk2d = np.abs(fk)**2 / delta_evolved.size
        k_mag = np.sqrt(KX**2 + KY**2).ravel()
        pk_flat = pk2d.ravel()
        k_max = int(min(size, size) // 2)
        k_bins = np.arange(1, k_max + 1, dtype=float)
        pk_avg = np.zeros(k_max)
        for ki in range(k_max):
            mask = (k_mag >= k_bins[ki] - 0.5) & (k_mag < k_bins[ki] + 0.5)
            if mask.any():
                pk_avg[ki] = float(pk_flat[mask].mean())
        power_spectra.append({"k": k_bins.tolist(), "pk": pk_avg.tolist()})

    # Did structure form? Check if final field has high contrast
    final_field = np.array(snapshots[-1])
    structure_formed = bool(final_field.std() > 0.5)

    return PlayableResponse(
        snapshots=snapshots,
        redshifts=redshifts.tolist(),
        scale_factors=scale_factors.tolist(),
        structure_formed=structure_formed,
        power_spectra=power_spectra,
    )
