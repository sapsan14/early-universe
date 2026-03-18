const BASE = "";

export async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
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
