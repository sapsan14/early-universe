/**
 * Glossary of cosmology terms used across Cosmic Academy.
 *
 * Each entry gives a bilingual short label, a one-line definition, an
 * everyday-language analogy, and (optionally) a notation symbol. The Term
 * component looks terms up by id and renders an interactive tooltip card.
 */

import type { Phrase } from "./i18n";

export interface GlossaryEntry {
  id: string;
  short: Phrase;
  symbol?: string;
  unit?: string;
  category: "epoch" | "physics" | "math" | "ml" | "observable" | "parameter";
  definition: Phrase;
  analogy?: Phrase;
  formula?: string;
  links?: string[];
}

const G = (e: GlossaryEntry): [string, GlossaryEntry] => [e.id, e];

export const GLOSSARY: Record<string, GlossaryEntry> = Object.fromEntries([
  G({
    id: "big-bang",
    short: { ru: "Большой Взрыв", en: "Big Bang" },
    category: "epoch",
    definition: {
      ru: "Не «взрыв» в пустоте, а начало расширения самого пространства из горячего, плотного состояния около 13,8 миллиардов лет назад.",
      en: "Not an explosion into empty space — the beginning of the expansion of space itself from a hot, dense state about 13.8 billion years ago.",
    },
    analogy: {
      ru: "Представь воздушный шарик: точки на нём — это галактики, а раздувание шарика — расширение пространства.",
      en: "Imagine an inflating balloon — dots on the surface (galaxies) move apart because the balloon (space) is stretching.",
    },
  }),
  G({
    id: "planck-time",
    short: { ru: "Планковское время", en: "Planck time" },
    symbol: "t_P",
    unit: "≈ 5.39 × 10⁻⁴⁴ s",
    category: "physics",
    definition: {
      ru: "Самый короткий промежуток времени, имеющий физический смысл: меньше — и наша теория уже не работает.",
      en: "The shortest physically meaningful time interval — below it our current theory of gravity breaks down.",
    },
    formula: "t_P = √(ħG/c⁵)",
    analogy: {
      ru: "Это как минимальное «деление линейки» у времени.",
      en: "Think of it as the smallest tick mark on the cosmic ruler of time.",
    },
  }),
  G({
    id: "inflation",
    short: { ru: "Инфляция", en: "Inflation" },
    category: "epoch",
    definition: {
      ru: "Краткая эпоха невероятно быстрого расширения: за 10⁻³² с пространство выросло в e⁶⁰ ≈ 10²⁶ раз.",
      en: "A brief epoch of extraordinarily rapid expansion: in 10⁻³² s space stretched by a factor of e⁶⁰ ≈ 10²⁶.",
    },
    analogy: {
      ru: "Как если бы маковое зёрнышко за миг раздулось до размера галактики.",
      en: "Like a poppy seed ballooning to galaxy size in a heartbeat.",
    },
  }),
  G({
    id: "quantum-fluctuation",
    short: { ru: "Квантовая флуктуация", en: "Quantum fluctuation" },
    category: "physics",
    definition: {
      ru: "Случайное «дрожание» вакуума: в нём всё время рождаются и исчезают пары частиц.",
      en: "Random jitter of the vacuum: pairs of particles continually appear and vanish.",
    },
    analogy: {
      ru: "Как мелкая рябь на воде, даже когда нет ветра.",
      en: "Like tiny ripples on the surface of a still pond.",
    },
  }),
  G({
    id: "bbn",
    short: { ru: "Нуклеосинтез (BBN)", en: "Nucleosynthesis (BBN)" },
    category: "epoch",
    definition: {
      ru: "Первые три минуты Вселенной: из протонов и нейтронов образовались ядра водорода (≈75%), гелия-4 (≈25%) и следы дейтерия и лития.",
      en: "The Universe's first three minutes: protons and neutrons fused into hydrogen (~75%), helium-4 (~25%), with trace deuterium and lithium.",
    },
  }),
  G({
    id: "cmb",
    short: { ru: "Реликтовое излучение (CMB)", en: "Cosmic Microwave Background (CMB)" },
    symbol: "T₀ = 2.725 K",
    category: "observable",
    definition: {
      ru: "Древнейший свет во Вселенной — фотоны, освободившиеся в момент рекомбинации. Сегодня заполняют небо при температуре 2,7 K.",
      en: "The oldest light in the Universe — photons released at recombination. Today they fill the sky at 2.7 K.",
    },
    analogy: {
      ru: "Это как сделанная 380 000 лет после рождения «детская фотография» Вселенной.",
      en: "It's a baby photo of the Universe, snapped 380 000 years after the Big Bang.",
    },
  }),
  G({
    id: "recombination",
    short: { ru: "Рекомбинация", en: "Recombination" },
    category: "epoch",
    definition: {
      ru: "Вселенная остыла настолько, что электроны соединились с протонами и образовали нейтральный водород. Свет получил возможность лететь свободно.",
      en: "The Universe cooled enough for electrons to bind with protons into neutral hydrogen. Light could finally travel freely.",
    },
    analogy: {
      ru: "Как туман, рассеявшийся в одно мгновение — и вдруг видно бесконечно далеко.",
      en: "Like fog clearing in an instant — suddenly the view stretches forever.",
    },
  }),
  G({
    id: "redshift",
    short: { ru: "Красное смещение", en: "Redshift" },
    symbol: "z",
    category: "observable",
    definition: {
      ru: "Растяжение длины волны света по мере расширения Вселенной. Чем больше z, тем дальше и древнее объект.",
      en: "The stretching of light's wavelength as the Universe expands. The bigger z, the farther and older the source.",
    },
    formula: "1 + z = λ_obs / λ_emit = 1 / a",
    analogy: {
      ru: "Как свисток уезжающего поезда звучит ниже, у уходящих от нас галактик свет «краснеет».",
      en: "Just as a receding train's whistle drops in pitch, light from receding galaxies shifts toward red.",
    },
  }),
  G({
    id: "scale-factor",
    short: { ru: "Масштабный фактор", en: "Scale factor" },
    symbol: "a",
    category: "physics",
    definition: {
      ru: "Безразмерное число, описывающее «во сколько раз сейчас Вселенная больше, чем когда-то». Сегодня a = 1.",
      en: "A dimensionless number telling us how much bigger the Universe is now compared to some earlier time. Today a = 1.",
    },
    formula: "L(t) = a(t) · L₀",
  }),
  G({
    id: "hubble",
    short: { ru: "Параметр Хаббла", en: "Hubble parameter" },
    symbol: "H",
    unit: "km/s/Mpc",
    category: "parameter",
    definition: {
      ru: "Скорость, с которой расширяется Вселенная сегодня (на единицу расстояния). H₀ ≈ 67–73 км/с на каждый Мпк.",
      en: "The current expansion rate of the Universe per unit distance. H₀ ≈ 67–73 km/s per megaparsec.",
    },
    formula: "v = H · d",
    analogy: {
      ru: "На каждый мегапарсек дальше — добавь ~70 км/с скорости разбегания.",
      en: "For every megaparsec farther away, add about 70 km/s to the recession speed.",
    },
  }),
  G({
    id: "friedmann",
    short: { ru: "Уравнение Фридмана", en: "Friedmann equation" },
    category: "math",
    definition: {
      ru: "Главное уравнение космологии: связывает скорость расширения H с плотностью энергии.",
      en: "Cosmology's master equation: it ties the expansion rate H to the energy density.",
    },
    formula: "H² = (8πG/3) ρ − k c²/a²",
  }),
  G({
    id: "dark-matter",
    short: { ru: "Тёмная материя", en: "Dark matter" },
    symbol: "Ω_cdm",
    category: "physics",
    definition: {
      ru: "Невидимое вещество, которое не светится и не поглощает свет, но создаёт гравитацию. Около 27% массы-энергии Вселенной.",
      en: "Invisible matter that doesn't shine or absorb light but does gravitate. About 27% of the Universe's mass-energy.",
    },
    analogy: {
      ru: "Как невидимый каркас, на котором держится вся световая часть Вселенной.",
      en: "Like an invisible scaffolding holding up the luminous Universe.",
    },
  }),
  G({
    id: "dark-energy",
    short: { ru: "Тёмная энергия", en: "Dark energy" },
    symbol: "Ω_Λ",
    category: "physics",
    definition: {
      ru: "Загадочная составляющая, ускоряющая расширение Вселенной. Около 68% всего бюджета.",
      en: "A mysterious component that accelerates the Universe's expansion. About 68% of the cosmic budget.",
    },
    analogy: {
      ru: "Как пружина, заложенная в самой ткани пространства.",
      en: "Like a spring built into the fabric of space itself.",
    },
  }),
  G({
    id: "baryon",
    short: { ru: "Барионы", en: "Baryons" },
    symbol: "Ω_b",
    category: "physics",
    definition: {
      ru: "Обычное вещество — протоны и нейтроны, из которых сделаны звёзды, планеты и мы. Всего ~5%.",
      en: "Ordinary matter — protons and neutrons that build stars, planets, and us. Just ~5%.",
    },
  }),
  G({
    id: "n-s",
    short: { ru: "Спектральный индекс", en: "Spectral index" },
    symbol: "n_s",
    category: "parameter",
    definition: {
      ru: "Описывает наклон первичного спектра флуктуаций. n_s = 1 — все масштабы равны (Хариссон-Зельдович), n_s ≈ 0.965 — наблюдаемое значение.",
      en: "Describes the tilt of the primordial fluctuation spectrum. n_s = 1 means all scales equal (Harrison-Zel'dovich); n_s ≈ 0.965 is observed.",
    },
  }),
  G({
    id: "a-s",
    short: { ru: "Амплитуда A_s", en: "Amplitude A_s" },
    symbol: "A_s",
    category: "parameter",
    definition: {
      ru: "Сила первичных флуктуаций — насколько «громким» был квантовый шёпот инфляции.",
      en: "Strength of primordial fluctuations — how loud the quantum whisper of inflation was.",
    },
  }),
  G({
    id: "tau",
    short: { ru: "Оптическая глубина τ", en: "Optical depth τ" },
    symbol: "τ_reio",
    category: "parameter",
    definition: {
      ru: "Сколько фотонов CMB рассеялось обратно после того, как первые звёзды реионизировали Вселенную.",
      en: "Fraction of CMB photons re-scattered after the first stars reionized the Universe.",
    },
  }),
  G({
    id: "omega-b-h2",
    short: { ru: "Ω_b h²", en: "Ω_b h²" },
    symbol: "Ω_b h²",
    category: "parameter",
    definition: {
      ru: "Плотность барионной материи в безразмерных «космологических единицах», умноженная на квадрат масштабированного Хаббла. Управляет балансом водорода и гелия.",
      en: "Baryon density in dimensionless cosmological units times the rescaled Hubble parameter squared. Controls the H/He balance.",
    },
  }),
  G({
    id: "omega-cdm-h2",
    short: { ru: "Ω_cdm h²", en: "Ω_cdm h²" },
    symbol: "Ω_cdm h²",
    category: "parameter",
    definition: {
      ru: "Плотность тёмной материи в тех же единицах. Управляет ростом структур.",
      en: "Cold dark matter density in the same units. Governs how structures grow.",
    },
  }),
  G({
    id: "multipole",
    short: { ru: "Мультиполь", en: "Multipole" },
    symbol: "ℓ",
    category: "math",
    definition: {
      ru: "Угловой масштаб на сфере: малое ℓ — большие пятна, большое ℓ — мелкая «рябь». ℓ ≈ 180° / угол.",
      en: "Angular scale on a sphere: small ℓ = big patches, large ℓ = fine ripples. ℓ ≈ 180° / angle.",
    },
  }),
  G({
    id: "power-spectrum",
    short: { ru: "Спектр мощности", en: "Power spectrum" },
    symbol: "C_ℓ",
    category: "math",
    definition: {
      ru: "Сколько «силы» содержат флуктуации на каждом угловом масштабе. Главный язык, на котором космологи разговаривают с CMB.",
      en: "How much power is in fluctuations at each angular scale — the language cosmologists use to read the CMB.",
    },
    formula: "D_ℓ = ℓ(ℓ+1) C_ℓ / (2π)",
  }),
  G({
    id: "gaussian",
    short: { ru: "Гауссово поле", en: "Gaussian field" },
    category: "math",
    definition: {
      ru: "Случайные флуктуации с нормальным распределением — описываются только средним и дисперсией.",
      en: "Random fluctuations with a normal distribution — described entirely by mean and variance.",
    },
  }),
  G({
    id: "skewness",
    short: { ru: "Асимметрия", en: "Skewness" },
    category: "math",
    definition: {
      ru: "Мера асимметрии распределения. Если флуктуации идеально гауссовы — асимметрия равна 0.",
      en: "Measures asymmetry of a distribution. Perfectly Gaussian fluctuations have skewness = 0.",
    },
  }),
  G({
    id: "kurtosis",
    short: { ru: "Эксцесс", en: "Kurtosis" },
    category: "math",
    definition: {
      ru: "Мера «тяжёлости хвостов» распределения. У гауссова — 3.",
      en: "Measures how heavy a distribution's tails are. Gaussian = 3.",
    },
  }),
  G({
    id: "autoencoder",
    short: { ru: "Автокодировщик", en: "Autoencoder" },
    category: "ml",
    definition: {
      ru: "Нейросеть, которая учится сжимать данные и восстанавливать их обратно. Если что-то восстановить плохо — это «аномалия».",
      en: "A neural network that compresses data and reconstructs it. Anything it can't reconstruct well is an 'anomaly'.",
    },
  }),
  G({
    id: "anomaly",
    short: { ru: "Аномалия", en: "Anomaly" },
    category: "ml",
    definition: {
      ru: "Что-то выбивающееся из ожидания — нестандартный сигнал, странное пятно, новая физика?",
      en: "Something that defies expectations — an unusual signal, a strange spot, possibly new physics.",
    },
  }),
  G({
    id: "qcd",
    short: { ru: "Кварк-глюонный переход", en: "QCD transition" },
    category: "epoch",
    definition: {
      ru: "При t ≈ 10⁻⁵ с кварки заперлись в протоны и нейтроны.",
      en: "Around t ≈ 10⁻⁵ s quarks became confined inside protons and neutrons.",
    },
  }),
  G({
    id: "dark-ages",
    short: { ru: "Тёмные века", en: "Dark Ages" },
    category: "epoch",
    definition: {
      ru: "Период между рекомбинацией и зажиганием первых звёзд — Вселенная была наполнена нейтральным газом без источников света.",
      en: "The era between recombination and the first stars — the Universe was filled with neutral gas and no light sources.",
    },
  }),
  G({
    id: "cosmic-dawn",
    short: { ru: "Космический рассвет", en: "Cosmic Dawn" },
    category: "epoch",
    definition: {
      ru: "Зажглись первые звёзды (Population III). Их ультрафиолет начал реионизировать Вселенную.",
      en: "The first stars (Population III) ignited. Their UV light began reionizing the Universe.",
    },
  }),
  G({
    id: "matter-radiation-equality",
    short: { ru: "Равенство материи и излучения", en: "Matter-radiation equality" },
    category: "epoch",
    definition: {
      ru: "Момент, когда плотность материи догнала плотность излучения. После этого структура начала расти быстрее.",
      en: "The moment matter density caught up to radiation density. Structure growth then accelerated.",
    },
  }),
  G({
    id: "planck-2018",
    short: { ru: "Planck 2018", en: "Planck 2018" },
    category: "observable",
    definition: {
      ru: "Эталонный набор космологических параметров от космического телескопа Planck (ESA), опубликованный в 2018 г.",
      en: "Reference cosmological parameters from ESA's Planck satellite, published in 2018.",
    },
  }),
]);

export function term(id: string): GlossaryEntry | undefined {
  return GLOSSARY[id];
}
