const BASE = "";

/**
 * After we've confirmed the Python API is unreachable we stop attempting —
 * every subsequent `post` short-circuits with the fallback error so the
 * browser console (and Vite's dev-server proxy log) stays quiet. Any time
 * the app is reloaded the flag resets and we probe once again.
 */
let apiKnownDown = false;
let downSince = 0;
/** If the backend was down, retry at most once every 30 s. */
const RETRY_AFTER_MS = 30_000;

export function isApiKnownDown(): boolean { return apiKnownDown; }
export function resetApiStatus() { apiKnownDown = false; downSince = 0; }

export async function post<T>(path: string, body: unknown): Promise<T> {
  if (apiKnownDown && performance.now() - downSince < RETRY_AFTER_MS) {
    throw new Error("API offline (cached)");
  }
  try {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.status === 503) {
      apiKnownDown = true;
      downSince = performance.now();
      throw new Error("API offline");
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`API ${res.status}: ${text}`);
    }
    apiKnownDown = false;
    return res.json() as Promise<T>;
  } catch (e) {
    apiKnownDown = true;
    downSince = performance.now();
    throw e;
  }
}

export interface CosmoParams {
  H0: number;
  Omega_b_h2: number;
  Omega_cdm_h2: number;
  n_s: number;
  ln10As: number;
  tau_reio: number;
}

export const DEFAULT_PARAMS: CosmoParams = {
  H0: 67.36,
  Omega_b_h2: 0.02237,
  Omega_cdm_h2: 0.12,
  n_s: 0.9649,
  ln10As: 3.044,
  tau_reio: 0.0544,
};

export interface CosmicEpoch {
  name: string;
  time_seconds: number;
  redshift: number;
  temperature_K: number;
  scale_factor: number;
  hubble_parameter: number;
  dominant_component: string;
  description: string;
  key_processes: string[];
}

export interface TimelineResponse {
  epoch: CosmicEpoch;
}

export interface SpectrumResponse {
  ell: number[];
  cl: number[];
  inference_time_ms: number;
}

export interface PlayableResponse {
  snapshots: number[][][];
  redshifts: number[];
  scale_factors: number[];
  structure_formed: boolean;
  power_spectra: { k: number[]; pk: number[] }[];
}

export interface AnomalyResponse {
  global_score: number;
  n_anomalies: number;
  candidates: { x: number; y: number; radius: number; score: number; significance: number }[];
  non_gaussianity: {
    skewness: number;
    kurtosis: number;
    skew_pvalue: number;
    kurt_pvalue: number;
    is_gaussian: boolean;
  };
  inference_time_ms: number;
}
