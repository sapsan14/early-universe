/**
 * Pure-TS cosmology helpers.
 *
 * We hit the Python API when it's online and use these functions as a
 * fallback so the educational platform never goes blank. Numbers are
 * good enough to communicate the *shape* of the physics — they are not
 * meant for research use.
 */

import type { Phrase } from "./i18n";
import type {
  CosmoParams,
  CosmicEpoch,
  SpectrumResponse,
  PlayableResponse,
  AnomalyResponse,
} from "./api/client";

export interface EpochDef {
  id: string;
  log_t_min: number;
  log_t_max: number;
  name: Phrase;
  /** Very short tick label for the timeline ruler (3-8 chars). */
  short: Phrase;
  description: Phrase;
  key_processes: Phrase[];
  dominant: "quantum_fields" | "inflaton_field" | "radiation" | "matter" | "dark_energy";
  color: string;
  glyph: string;
}

export const EPOCH_DEFS: EpochDef[] = [
  {
    id: "planck",
    log_t_min: -43.5, log_t_max: -36,
    name: { ru: "Планковская эпоха", en: "Planck Epoch" },
    short: { ru: "Планк", en: "Planck" },
    description: {
      ru: "Все четыре фундаментальные силы — электромагнитная, слабая, сильная и гравитация — слиты в одну. Привычная физика молчит.",
      en: "All four fundamental forces — electromagnetism, weak, strong and gravity — are fused into one. Familiar physics falls silent.",
    },
    key_processes: [
      { ru: "Квантовая гравитация", en: "Quantum gravity" },
      { ru: "Великое объединение", en: "Grand unification" },
    ],
    dominant: "quantum_fields",
    color: "#9b8cff",
    glyph: "✺",
  },
  {
    id: "inflation",
    log_t_min: -36, log_t_max: -32,
    name: { ru: "Инфляция", en: "Inflation" },
    short: { ru: "Инфл.", en: "Inflation" },
    description: {
      ru: "Пространство мгновенно растягивается в e⁶⁰ ≈ 10²⁶ раз. Из квантовой ряби рождаются зародыши будущих галактик.",
      en: "Space is stretched by a factor of e⁶⁰ ≈ 10²⁶ in an instant. Quantum ripples seed every future galaxy.",
    },
    key_processes: [
      { ru: "Экспоненциальное расширение", en: "Exponential expansion" },
      { ru: "Засев квантовых флуктуаций", en: "Seeding of quantum fluctuations" },
      { ru: "Решение проблем плоскости и горизонта", en: "Solving the flatness & horizon problems" },
    ],
    dominant: "inflaton_field",
    color: "#ff7ac6",
    glyph: "✸",
  },
  {
    id: "reheating",
    log_t_min: -32, log_t_max: -10,
    name: { ru: "Подогрев и кварковая эпоха", en: "Reheating & Quark Epoch" },
    short: { ru: "Кварки", en: "Quarks" },
    description: {
      ru: "Энергия инфлатона переходит в фонтан частиц. Кварк-глюонная плазма раскалена до триллионов градусов.",
      en: "Inflaton energy converts into a fountain of particles. Quark–gluon plasma blazes at trillions of kelvin.",
    },
    key_processes: [
      { ru: "Подогрев", en: "Reheating" },
      { ru: "Бариогенез", en: "Baryogenesis" },
      { ru: "Кварк-глюонная плазма", en: "Quark-gluon plasma" },
    ],
    dominant: "radiation",
    color: "#ff8b5e",
    glyph: "✦",
  },
  {
    id: "qcd",
    log_t_min: -10, log_t_max: -4,
    name: { ru: "Кварк-глюонный переход", en: "QCD Phase Transition" },
    short: { ru: "QCD", en: "QCD" },
    description: {
      ru: "Кварки запираются в протоны и нейтроны. Температура около 1.7 × 10¹² K.",
      en: "Quarks become confined inside protons and neutrons. Temperature ≈ 1.7 × 10¹² K.",
    },
    key_processes: [
      { ru: "Конфайнмент кварков", en: "Quark confinement" },
      { ru: "Образование адронов", en: "Hadron formation" },
    ],
    dominant: "radiation",
    color: "#ffd56b",
    glyph: "✶",
  },
  {
    id: "bbn",
    log_t_min: -4, log_t_max: 3,
    name: { ru: "Первичный нуклеосинтез", en: "Big Bang Nucleosynthesis" },
    short: { ru: "BBN", en: "BBN" },
    description: {
      ru: "За три минуты сваривается кухня лёгких ядер: ~75% водорода, ~25% гелия-4, следы дейтерия и лития.",
      en: "In three minutes the cosmic kitchen forges ~75% hydrogen, ~25% helium-4, with trace deuterium and lithium.",
    },
    key_processes: [
      { ru: "Образование дейтерия", en: "Deuterium formation" },
      { ru: "Синтез гелия-4", en: "Helium-4 synthesis" },
      { ru: "Заморозка отношения n/p", en: "Neutron-to-proton freeze-out" },
    ],
    dominant: "radiation",
    color: "#7afcb1",
    glyph: "✪",
  },
  {
    id: "equality",
    log_t_min: 3, log_t_max: 11,
    name: { ru: "Равенство материи и излучения", en: "Matter–Radiation Equality" },
    short: { ru: "Mатер.=изл.", en: "M–R eq." },
    description: {
      ru: "Плотность вещества догоняет плотность излучения (z ≈ 3400). Гравитация наконец берёт верх над давлением света.",
      en: "Matter density catches up with radiation (z ≈ 3400). Gravity finally outmuscles light pressure.",
    },
    key_processes: [
      { ru: "Начало эпохи материи", en: "Onset of matter domination" },
      { ru: "Начало роста структур", en: "Structure growth begins" },
    ],
    dominant: "matter",
    color: "#5ee2ff",
    glyph: "✵",
  },
  {
    id: "cmb",
    log_t_min: 11, log_t_max: 13,
    name: { ru: "Рекомбинация / выпуск CMB", en: "Recombination / CMB Release" },
    short: { ru: "CMB", en: "CMB" },
    description: {
      ru: "Электроны соединяются с ядрами в нейтральный водород. Свет освобождается — мы наблюдаем его сегодня как реликтовое излучение.",
      en: "Electrons bind with nuclei into neutral hydrogen. Light breaks free — today we see it as the cosmic microwave background.",
    },
    key_processes: [
      { ru: "Образование нейтрального водорода", en: "Hydrogen recombination" },
      { ru: "Развязка фотонов и материи", en: "Photon decoupling" },
      { ru: "Поверхность последнего рассеяния", en: "Last-scattering surface" },
    ],
    dominant: "matter",
    color: "#9b8cff",
    glyph: "❂",
  },
  {
    id: "dark-ages",
    log_t_min: 13, log_t_max: 15.5,
    name: { ru: "Тёмные века", en: "Dark Ages" },
    short: { ru: "Тёмн. века", en: "Dark Ages" },
    description: {
      ru: "Звёзд ещё нет. Тёмная материя строит каркас гравитационных колодцев, в которые стекает водород.",
      en: "No stars yet. Dark matter builds the gravitational scaffolding into which hydrogen pours.",
    },
    key_processes: [
      { ru: "Формирование тёмных гало", en: "Dark matter halo formation" },
      { ru: "Аккреция газа", en: "Gas accretion" },
    ],
    dominant: "matter",
    color: "#6f7aa8",
    glyph: "☾",
  },
  {
    id: "dawn",
    log_t_min: 15.5, log_t_max: 16.3,
    name: { ru: "Космический рассвет", en: "Cosmic Dawn" },
    short: { ru: "Рассвет", en: "Dawn" },
    description: {
      ru: "Загораются первые звёзды (Population III). Ультрафиолетом они вновь ионизируют межгалактический водород.",
      en: "The very first stars (Population III) ignite. Their UV light reionizes the intergalactic hydrogen.",
    },
    key_processes: [
      { ru: "Первые звёзды", en: "First stars" },
      { ru: "Образование галактик", en: "Galaxy formation" },
      { ru: "Реионизация водорода", en: "Reionization of hydrogen" },
    ],
    dominant: "matter",
    color: "#ffd56b",
    glyph: "☀",
  },
  {
    id: "now",
    log_t_min: 16.3, log_t_max: 17.7,
    name: { ru: "Современная Вселенная", en: "Present-day Universe" },
    short: { ru: "Сейчас", en: "Now" },
    description: {
      ru: "Сложилась паутина галактик, скоплений и войдов. Тёмная энергия снова разгоняет расширение.",
      en: "The cosmic web of galaxies, clusters and voids is in place. Dark energy is once again accelerating expansion.",
    },
    key_processes: [
      { ru: "Скопления галактик", en: "Galaxy clusters" },
      { ru: "Крупномасштабная структура", en: "Large-scale structure" },
      { ru: "Доминирование тёмной энергии", en: "Dark energy domination" },
    ],
    dominant: "dark_energy",
    color: "#ff7ac6",
    glyph: "✴",
  },
];

export function findEpoch(log_t: number): EpochDef {
  for (const e of EPOCH_DEFS) {
    if (log_t >= e.log_t_min && log_t < e.log_t_max) return e;
  }
  if (log_t >= EPOCH_DEFS[EPOCH_DEFS.length - 1].log_t_max) {
    return EPOCH_DEFS[EPOCH_DEFS.length - 1];
  }
  return EPOCH_DEFS[0];
}

const T_CMB_0 = 2.7255;
const T_AGE = 13.8e9 * 3.156e7; // seconds

export function computeState(log_t: number, params: CosmoParams) {
  const t = Math.pow(10, log_t);
  const h = params.H0 / 100;
  const Omega_m = (params.Omega_b_h2 + params.Omega_cdm_h2) / (h * h);
  const Omega_r = 9.1e-5;
  const Omega_L = Math.max(0, 1 - Omega_m - Omega_r);

  let a: number;
  if (log_t < 13) a = Math.min(Math.pow(t / T_AGE, 0.5), 1);
  else if (log_t < 16.8) a = Math.min(Math.pow(t / T_AGE, 2 / 3), 1);
  else a = Math.min(Math.pow(t / T_AGE, 0.7), 1);
  a = Math.max(a, 1e-30);

  const z = 1 / a - 1;
  const T = T_CMB_0 / a;

  const H2 =
    params.H0 ** 2 *
    (Omega_r / a ** 4 + Omega_m / a ** 3 + Omega_L);
  const H = Math.sqrt(Math.max(H2, 0));

  let dominant: CosmicEpoch["dominant_component"] = "matter";
  const eR = Omega_r / a ** 4;
  const eM = Omega_m / a ** 3;
  if (eR > eM && eR > Omega_L) dominant = "radiation";
  else if (eM > Omega_L) dominant = "matter";
  else dominant = "dark_energy";

  return {
    redshift: z,
    temperature_K: T,
    scale_factor: a,
    hubble_parameter: H,
    dominant_component: dominant,
  };
}

export function buildLocalEpoch(log_t: number, params: CosmoParams, lang: "ru" | "en"): CosmicEpoch {
  const def = findEpoch(log_t);
  const s = computeState(log_t, params);
  return {
    name: def.name[lang],
    time_seconds: Math.pow(10, log_t),
    redshift: s.redshift,
    temperature_K: s.temperature_K,
    scale_factor: s.scale_factor,
    hubble_parameter: s.hubble_parameter,
    dominant_component: s.dominant_component,
    description: def.description[lang],
    key_processes: def.key_processes.map((p) => p[lang]),
  };
}

/** Toy CMB-like power spectrum that responds qualitatively to params. */
export function localSpectrum(params: CosmoParams, lMax = 2500): SpectrumResponse {
  const ell: number[] = [];
  const cl: number[] = [];

  const A = Math.exp(params.ln10As) * 1e-10;
  const ns = params.n_s;
  const h = params.H0 / 100;
  const omegaMh2 = params.Omega_b_h2 + params.Omega_cdm_h2;
  // Angular acoustic scale ℓ_A = π D_A / r_s. Both scales depend on cosmology;
  // we capture the two strongest effects: lower H0 pushes the peaks to smaller ℓ
  // (larger angular size), and larger Omega_m h² shrinks the sound horizon.
  const lA_ref = 301; // Planck 2018 ≈ 301
  const h_ref = 0.6736;
  const omh2_ref = 0.143;
  const lA = lA_ref * (h / h_ref) ** 0.4 * Math.sqrt(omh2_ref / Math.max(omegaMh2, 0.05));
  // Silk damping scale
  const lD = 1500 * Math.sqrt(0.022 / Math.max(params.Omega_b_h2, 0.005)) * (h / h_ref) ** 0.3;
  // Baryon drag boosts odd peaks (1st, 3rd) relative to even (2nd).
  const R = params.Omega_b_h2 / 0.0224;
  const oddBoost = Math.pow(R, 0.35);
  const evenBoost = Math.pow(R, -0.15);
  // Dark-matter driving lifts the first peak and suppresses very-low-ℓ plateau.
  const cdmBoost = Math.pow(params.Omega_cdm_h2 / 0.12, 0.25);
  // Low-ℓ suppression from reionization
  const supp = Math.exp(-2 * params.tau_reio);
  // Reionization bump at ℓ ~ 5–10
  const reioBump = params.tau_reio * 0.8;

  for (let l = 2; l <= lMax; l += Math.max(1, Math.floor(l / 60))) {
    const tilt = Math.pow(l / 200, ns - 1);
    const width = lA * 0.17;
    const p1 = oddBoost * cdmBoost *
      Math.exp(-((l - lA) ** 2) / (2 * width ** 2));
    const p2 = 0.55 * evenBoost *
      Math.exp(-((l - 2 * lA) ** 2) / (2 * width ** 2));
    const p3 = 0.32 * oddBoost *
      Math.exp(-((l - 3 * lA) ** 2) / (2 * width ** 2));
    const p4 = 0.18 * evenBoost *
      Math.exp(-((l - 4 * lA) ** 2) / (2 * width ** 2));
    const peaks = p1 + p2 + p3 + p4;
    const sw = 0.6 / (1 + l / 30) + reioBump / (1 + ((l - 6) / 4) ** 2);
    const damping = Math.exp(-((l / lD) ** 1.8));
    const dl = A * 5e10 * tilt * (sw + 1.6 * peaks) * damping * supp;
    const clVal = (2 * Math.PI * dl) / Math.max(l * (l + 1), 1);
    ell.push(l);
    cl.push(Math.max(clVal, 1e-30));
  }
  return { ell, cl, inference_time_ms: 0.6 };
}

/**
 * Toy density field that grows over "time" and reacts *visibly* to every
 * slider. This is not physics-accurate — it's a didactic illustration of
 * how cosmological parameters change the cosmic web.
 *
 * Pipeline:
 *   1. Build a multi-octave noise field (like a 2-D Perlin) — octave weights
 *      depend on n_s (tilt toward large or small scales).
 *   2. Apply linear growth D(t) × amp × ω_cdm-driven multiplier.
 *   3. Apply non-linear spherical-collapse squishing δ → δ (1 + αδ) so
 *      over-dense regions sharpen into filaments / nodes.
 *   4. Per-snapshot percentile-based normalisation so the colormap never
 *      collapses to a single shade.
 */
export function localPlayable(params: CosmoParams, gridSize = 96, nSteps = 12, seed0 = 1234): PlayableResponse {
  let seed = seed0 >>> 0;
  const rand = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0xffffffff;
  };
  const gauss = () => {
    const u1 = Math.max(rand(), 1e-9);
    const u2 = rand();
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  };

  const N = gridSize;

  // Build four octaves at decreasing resolution and upsample.
  // Each octave is an independently-seeded Gaussian field. By weighting them
  // differently we simulate "more large-scale power" vs "more small-scale".
  const octaveSizes = [8, 16, 32, 64];
  const octaves = octaveSizes.map((size) => {
    const f: number[][] = [];
    for (let y = 0; y < size; y++) {
      const row: number[] = [];
      for (let x = 0; x < size; x++) row.push(gauss());
      f.push(row);
    }
    return f;
  });

  // Weights: n_s controls tilt between large and small scales.
  // n_s = 1.0 → all octaves equal. n_s > 1 → small scales amplified.
  // n_s < 1 → large scales amplified.
  const tilt = params.n_s - 1.0;
  const weights = octaveSizes.map((size) => {
    const logSize = Math.log2(size);
    return Math.pow(2, tilt * (logSize - 3.5));
  });
  // Normalize weights
  const wSum = weights.reduce((a, b) => a + b, 0);
  const w = weights.map((x) => x / wSum);

  // Upsample each octave to N×N via bilinear interpolation and sum.
  // Indices clamp to [0, s-1] (no modulo wrap) so the right/bottom edges
  // don't jump back to the top-left — that jump was visible as a bright
  // 1-pixel ring around the canvas.
  const base: number[][] = Array.from({ length: N }, () => new Array(N).fill(0));
  for (let o = 0; o < octaves.length; o++) {
    const f = octaves[o];
    const s = octaveSizes[o];
    for (let y = 0; y < N; y++) {
      const fy = (y / (N - 1)) * (s - 1);
      const y0 = Math.min(Math.floor(fy), s - 1);
      const y1 = Math.min(y0 + 1, s - 1);
      const ty = fy - Math.floor(fy);
      for (let x = 0; x < N; x++) {
        const fx = (x / (N - 1)) * (s - 1);
        const x0 = Math.min(Math.floor(fx), s - 1);
        const x1 = Math.min(x0 + 1, s - 1);
        const tx = fx - Math.floor(fx);
        const a = f[y0][x0] * (1 - tx) + f[y0][x1] * tx;
        const b = f[y1][x0] * (1 - tx) + f[y1][x1] * tx;
        base[y][x] += (a * (1 - ty) + b * ty) * w[o];
      }
    }
  }

  // Normalize base field to zero mean, unit std
  let mean = 0;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) mean += base[y][x];
  mean /= N * N;
  let sq = 0;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) sq += (base[y][x] - mean) ** 2;
  const std = Math.sqrt(sq / (N * N)) || 1;
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) base[y][x] = (base[y][x] - mean) / std;

  // Physical growth factor.
  //   `asFactor`: linear in e^(ln10As − 3.044), so the slider's full 1.5 → 4.5
  //               range spans ~20×.
  //   `omFactor`: sub-linear in Ω_cdm h² — too-high CDM otherwise blows out.
  //   `expansionDrag`: lower H₀ means an older Universe and more time for
  //               structure to grow. Exponent 1.2 gives a ~3× swing across
  //               the 50–100 km/s/Mpc slider — visible, but not cartoonish.
  const asFactor = Math.exp(params.ln10As - 3.044);
  const omFactor = Math.pow(params.Omega_cdm_h2 / 0.12, 0.7);
  const expansionDrag = Math.pow(67.36 / Math.max(params.H0, 30), 1.2);

  const snapshots: number[][][] = [];
  const redshifts: number[] = [];
  const scaleFactors: number[] = [];

  const clampIdx = (v: number, n: number) => Math.max(0, Math.min(n - 1, v));

  for (let step = 0; step < nSteps; step++) {
    const t = (step + 1) / nSteps;
    // δ = amp × base field — amplitude grows through the simulation.
    // The factor 2.5 amplifies contrast so even modest parameters produce
    // a visibly non-Gaussian field.
    const linAmp = 2.5 * asFactor * omFactor * expansionDrag * t ** 1.3;
    // Non-linear factor — amplifies crests into filaments, flattens voids.
    const nlCoeff = 0.9 * Math.pow(params.Omega_cdm_h2 / 0.12, 0.3);

    // Raw δ
    const raw: number[][] = [];
    for (let y = 0; y < N; y++) {
      const row: number[] = [];
      for (let x = 0; x < N; x++) {
        const lin = base[y][x] * linAmp;
        const pos = Math.max(lin, 0);
        row.push(lin + nlCoeff * pos * pos);
      }
      raw.push(row);
    }
    // Post-smoothing pass: one clamped-boundary box blur so the sharp
    // peaks spread into connected filaments — "cosmic web" look instead
    // of "isolated dots on a dark background".
    const snap: number[][] = [];
    for (let y = 0; y < N; y++) {
      const row: number[] = new Array(N);
      for (let x = 0; x < N; x++) {
        let sum = 0;
        for (let dy = -1; dy <= 1; dy++)
          for (let dx = -1; dx <= 1; dx++)
            sum += raw[clampIdx(y + dy, N)][clampIdx(x + dx, N)];
        row[x] = sum / 9;
      }
      snap.push(row);
    }
    snapshots.push(snap);
    const z = Math.max(0, 30 / (1 + step) - 1);
    redshifts.push(z);
    scaleFactors.push(1 / (1 + z));
  }

  // Structure check: final snapshot has visible contrast above noise floor?
  const last = snapshots[snapshots.length - 1].flat();
  let lMean = 0; for (const v of last) lMean += v; lMean /= last.length;
  let lVar = 0; for (const v of last) lVar += (v - lMean) ** 2;
  const lStd = Math.sqrt(lVar / last.length);
  const structure_formed = lStd > 0.25 && asFactor * omFactor > 0.3;

  // Power spectrum (radial average, synthetic)
  const kArr: number[] = [];
  const pkArr: number[] = [];
  for (let k = 1; k <= N / 4; k++) {
    kArr.push(k);
    pkArr.push((asFactor * omFactor * Math.pow(k, params.n_s - 1)) / (1 + (k / 8) ** 2));
  }

  return {
    snapshots,
    redshifts,
    scale_factors: scaleFactors,
    structure_formed,
    power_spectra: [{ k: kArr, pk: pkArr }],
  };
}

/** Detect anomalies in a 2D map (sigma-thresholded, plus skew/kurtosis). */
export function localAnomaly(map: number[][], threshold = 3): AnomalyResponse {
  const flat = map.flat();
  const n = flat.length;
  let mean = 0;
  for (const v of flat) mean += v;
  mean /= n;
  let varSum = 0;
  for (const v of flat) varSum += (v - mean) ** 2;
  const std = Math.sqrt(varSum / n) || 1;
  let m3 = 0, m4 = 0;
  for (const v of flat) {
    const d = (v - mean) / std;
    m3 += d ** 3;
    m4 += d ** 4;
  }
  const skew = m3 / n;
  const kurt = m4 / n;

  // Approximate p-values using a normal approximation
  const skewPval = Math.exp(-(Math.abs(skew) ** 2) * (n / 6));
  const kurtPval = Math.exp(-(Math.abs(kurt - 3) ** 2) * (n / 24));
  const isGaussian = skewPval > 0.05 && kurtPval > 0.05;

  type Cand = { x: number; y: number; radius: number; score: number; significance: number };
  const candidates: Cand[] = [];
  const H = map.length;
  const W = map[0].length;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const z = Math.abs((map[y][x] - mean) / std);
      if (z >= threshold) {
        candidates.push({
          x, y,
          radius: 2 + Math.min(4, Math.floor(z - threshold)),
          score: z,
          significance: z,
        });
      }
    }
  }
  // Cap candidates to top-N to avoid clutter
  candidates.sort((a, b) => b.score - a.score);
  const top = candidates.slice(0, 12);

  return {
    global_score: skew ** 2 + (kurt - 3) ** 2,
    n_anomalies: top.length,
    candidates: top,
    non_gaussianity: {
      skewness: skew,
      kurtosis: kurt,
      skew_pvalue: skewPval,
      kurt_pvalue: kurtPval,
      is_gaussian: isGaussian,
    },
    inference_time_ms: 0.4,
  };
}
