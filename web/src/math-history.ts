/**
 * Author / year / history metadata for every formula used in the textbook.
 *
 * Keyed by a short stable id. The MathBlock component looks the id up and
 * shows a little "i" button; clicking it pops a card with the backstory.
 * All strings are bilingual.
 */

import type { Phrase } from "./i18n";

export interface MathHistory {
  id: string;
  title: Phrase;
  author: Phrase;
  year: string;
  origin?: Phrase;
  story: Phrase;
  fun?: Phrase;
}

const H = (m: MathHistory): [string, MathHistory] => [m.id, m];

export const MATH_HISTORY: Record<string, MathHistory> = Object.fromEntries([
  H({
    id: "hubble-law",
    title: { ru: "Закон Хаббла", en: "Hubble's law" },
    author: { ru: "Эдвин Хаббл (при серьёзном вкладе Жоржа Леметра)", en: "Edwin Hubble (with a big assist from Georges Lemaître)" },
    year: "1929",
    origin: {
      ru: "Обсерватория Маунт-Вилсон, Калифорния",
      en: "Mount Wilson Observatory, California",
    },
    story: {
      ru: "Хаббл заметил, что спектры далёких галактик «покраснели» тем сильнее, чем они дальше. Это означает, что они убегают от нас — Вселенная расширяется. Поразительно, что бельгийский священник Жорж Леметр предсказал это двумя годами раньше из уравнений Эйнштейна.",
      en: "Hubble noticed that distant galaxies' spectra were redshifted in proportion to their distance. That meant they were receding — the Universe is expanding. Remarkably, the Belgian priest Georges Lemaître had predicted exactly this from Einstein's equations two years earlier.",
    },
    fun: {
      ru: "В 2018 году МАС переименовал закон в «закон Хаббла–Леметра», чтобы восстановить историческую справедливость.",
      en: "In 2018 the IAU officially renamed it the 'Hubble–Lemaître law' to restore historical fairness.",
    },
  }),
  H({
    id: "friedmann",
    title: { ru: "Уравнение Фридмана", en: "The Friedmann equation" },
    author: { ru: "Александр Фридман", en: "Alexander Friedmann" },
    year: "1922",
    origin: {
      ru: "Петроград (Санкт-Петербург), статья в Zeitschrift für Physik",
      en: "Petrograd (St Petersburg), paper in Zeitschrift für Physik",
    },
    story: {
      ru: "Русский математик-метеоролог Фридман решил уравнения Эйнштейна для однородной Вселенной и обнаружил: она обязана расширяться или сжиматься — статичной быть не может. Эйнштейн назвал это ошибкой, но позже признал, что Фридман был прав. Через семь лет Хаббл увидел расширение в телескопе.",
      en: "The Russian mathematician-meteorologist Friedmann solved Einstein's equations for a homogeneous Universe and found it must either expand or contract — it cannot be static. Einstein first called this a mistake, then conceded Friedmann was right. Seven years later Hubble saw the expansion through a telescope.",
    },
    fun: {
      ru: "Фридман погиб от брюшного тифа в 1925 году, в 37 лет — за три года до подтверждения своей теории.",
      en: "Friedmann died of typhoid in 1925 at age 37, three years before his theory was confirmed.",
    },
  }),
  H({
    id: "planck-time",
    title: { ru: "Планковское время", en: "Planck time" },
    author: { ru: "Макс Планк", en: "Max Planck" },
    year: "1899",
    origin: { ru: "Берлин, Прусская академия наук", en: "Berlin, Prussian Academy of Sciences" },
    story: {
      ru: "Планк составил комбинации из фундаментальных постоянных (ℏ, G, c), чтобы получить «естественные единицы», не зависящие от человеческого произвола (метров, секунд, килограммов). Это было задолго до рождения квантовой гравитации — и только в XX веке физики поняли, что ниже планковских масштабов наша физика просто не работает.",
      en: "Planck combined the fundamental constants (ℏ, G, c) to get 'natural units' free of human convention (metres, seconds, kilograms). This was long before quantum gravity existed — only in the 20th century did physicists realise that below the Planck scales our physics simply breaks down.",
    },
    fun: {
      ru: "Планк считал квантовую гипотезу «математическим трюком»; то, что свет действительно состоит из квантов, доказал Эйнштейн — и получил за это Нобелевскую премию (не за теорию относительности!).",
      en: "Planck thought his quantum hypothesis was a 'mathematical trick'; that light really is made of quanta was proven by Einstein — who won his Nobel Prize for that, not for relativity!",
    },
  }),
  H({
    id: "redshift",
    title: { ru: "Красное смещение", en: "Redshift" },
    author: { ru: "Кристиан Доплер (звук) → Весто Слайфер (свет галактик)", en: "Christian Doppler (sound) → Vesto Slipher (galaxy light)" },
    year: "1842 / 1912",
    story: {
      ru: "Эффект Доплера предсказал австриец Кристиан Доплер в 1842 году для звука («уезжающий поезд гудит ниже»). Через 70 лет Весто Слайфер впервые увидел, что линии в спектрах спиральных туманностей смещены в красную сторону. Это и было первое свидетельство расширения Вселенной — за 17 лет до Хаббла.",
      en: "The Doppler effect was predicted by the Austrian Christian Doppler in 1842 for sound ('a receding train has a lower pitch'). Seventy years later Vesto Slipher first saw that spectral lines from spiral nebulae were shifted toward the red. That was the first evidence of cosmic expansion — 17 years before Hubble.",
    },
  }),
  H({
    id: "scale-factor-radiation",
    title: { ru: "Рост Вселенной в разных эпохах", en: "Scale-factor growth in each era" },
    author: { ru: "Александр Фридман, Жорж Леметр, Говард Робертсон, Артур Уокер", en: "Friedmann, Lemaître, Robertson, Walker" },
    year: "1922–1936",
    story: {
      ru: "Эти две степенные формулы — a ∝ t^½ и a ∝ t^⅔ — это решения уравнения Фридмана в двух частных случаях: когда во Вселенной доминирует излучение (ранняя эпоха) и когда доминирует материя (после рекомбинации). Получить их можно школьной алгеброй при условии Ω_Λ = 0, Ω_k = 0.",
      en: "These two power laws — a ∝ t^½ and a ∝ t^⅔ — are solutions of the Friedmann equation in two special cases: when the Universe is dominated by radiation (early era) and when it is dominated by matter (after recombination). You can derive them with high-school algebra if you set Ω_Λ = 0 and Ω_k = 0.",
    },
  }),
  H({
    id: "inflation",
    title: { ru: "Экспоненциальная инфляция", en: "Exponential inflation" },
    author: { ru: "Алан Гут, Андрей Линде, Андреас Альбрехт, Пол Стейнхардт", en: "Alan Guth, Andrei Linde, Andreas Albrecht, Paul Steinhardt" },
    year: "1980–1982",
    origin: { ru: "SLAC / ФИАН / Пенсильвания", en: "SLAC / Lebedev Institute / Pennsylvania" },
    story: {
      ru: "Гут предложил идею инфляции в 1980 году в Стэнфорде (SLAC). У него была «старая» модель с проблемами, которые независимо исправили Линде (в Москве) и Альбрехт со Стейнхардтом (в США) — так возникла «новая инфляция». Сегодня инфляция — стандартная часть космологии, хотя её конкретный механизм всё ещё не установлен.",
      en: "Guth proposed inflation in 1980 at Stanford's SLAC. His 'old' version had problems, fixed independently by Linde (in Moscow) and Albrecht & Steinhardt (in the US) — giving birth to 'new inflation'. Today inflation is standard cosmology, though the precise mechanism is still debated.",
    },
    fun: {
      ru: "Алан Гут был поражён, когда Андрей Линде на международной конференции встал и сказал: «я решил ту же проблему на год раньше». Гут отвечает: «Я был бы расстроен, но он говорил так очаровательно».",
      en: "Guth was shocked when Andrei Linde stood up at an international conference and said: 'I solved the same problem a year earlier.' Guth replied: 'I would've been upset, but he said it so charmingly.'",
    },
  }),
  H({
    id: "primordial-spectrum",
    title: { ru: "Спектр первичных флуктуаций", en: "Primordial fluctuation spectrum" },
    author: { ru: "Эдуард Хариссон, Яков Зельдович, Питер Пиблс", en: "Edward Harrison, Yakov Zel'dovich, P. J. E. Peebles" },
    year: "1970",
    story: {
      ru: "Британец Хариссон и советский физик Зельдович независимо предложили «бесшкальный» спектр (n_s = 1) в 1970 году. Инфляционные модели позднее предсказали чуть меньше единицы — и наблюдения Planck это блестяще подтвердили (n_s ≈ 0.965). Это один из сильнейших аргументов в пользу инфляции.",
      en: "The British Harrison and the Soviet Zel'dovich independently proposed a 'scale-invariant' spectrum (n_s = 1) in 1970. Inflation models later predicted slightly less than one — and Planck's observations brilliantly confirmed it (n_s ≈ 0.965). One of the strongest arguments for inflation.",
    },
  }),
  H({
    id: "helium-fraction",
    title: { ru: "Первичный нуклеосинтез: доля гелия", en: "BBN: helium fraction" },
    author: { ru: "Ральф Альфер, Ганс Бете, Георгий Гамов", en: "Ralph Alpher, Hans Bethe, George Gamow" },
    year: "1948",
    origin: { ru: "Статья «αβγ» (Alpher-Bethe-Gamow)", en: "The 'αβγ' paper" },
    story: {
      ru: "Гамов предложил идею первичного нуклеосинтеза, а его ученик Альфер рассчитал детали. Чтобы шутить про греческий алфавит, Гамов вписал Ганса Бете соавтором: фамилии дали знаменитое «альфа-бета-гамма». Бете, узнав об этом после публикации, только посмеялся.",
      en: "Gamow proposed primordial nucleosynthesis; his student Alpher worked out the details. Just to joke about the Greek alphabet, Gamow added Hans Bethe as a co-author: α-β-γ. Bethe only learned about it after publication — and laughed.",
    },
    fun: {
      ru: "Альфер и его друг Роберт Герман в 1948 году предсказали существование реликтового излучения при ~5 K. Их предсказание забыли, и лишь в 1965-м Пензиас и Вильсон случайно открыли его заново — и получили Нобелевскую премию.",
      en: "Alpher and his friend Robert Herman predicted the cosmic microwave background at ~5 K in 1948. The prediction was forgotten, and in 1965 Penzias and Wilson accidentally rediscovered it — winning the Nobel Prize.",
    },
  }),
  H({
    id: "cmb-power-spectrum",
    title: { ru: "Спектр мощности CMB", en: "CMB power spectrum" },
    author: { ru: "Первый точный расчёт — Дж. Силк, 1968; первое измерение — COBE / WMAP / Planck", en: "First detailed prediction — J. Silk 1968; measurement — COBE / WMAP / Planck" },
    year: "1968 / 1992–2018",
    story: {
      ru: "Джо Силк предсказал, что в спектре CMB будут «акустические пики» — следы звуковых волн в первичной плазме. Три поколения спутников (COBE в 1992, WMAP в 2003, Planck в 2013 и 2018) раз за разом измерили их всё точнее. Сегодня спектр — это «ДНК Вселенной»: по его форме мы знаем, сколько в ней барионов, тёмной материи, тёмной энергии.",
      en: "Joe Silk predicted that the CMB spectrum would contain 'acoustic peaks' — the fingerprint of sound waves in the primordial plasma. Three generations of satellites (COBE in 1992, WMAP in 2003, Planck in 2013 and 2018) measured them with ever-increasing precision. Today the spectrum is the 'Universe's DNA': its shape tells us how many baryons, how much dark matter, how much dark energy.",
    },
    fun: {
      ru: "Нобелевская премия 2006 года досталась Джону Мазеру и Джорджу Смуту за карту CMB от COBE. Мазер продемонстрировал, что спектр — почти идеальное чёрное тело: самое точное подтверждение Большого Взрыва.",
      en: "The 2006 Nobel Prize went to John Mather and George Smoot for COBE's CMB map. Mather showed the spectrum is an almost perfect black body — the sharpest confirmation of the Big Bang.",
    },
  }),
  H({
    id: "reionization-tau",
    title: { ru: "Оптическая глубина реионизации", en: "Reionization optical depth" },
    author: { ru: "Первые оценки — WMAP, 2003; точные — Planck, 2018", en: "First estimates — WMAP 2003; precise — Planck 2018" },
    year: "2003–2018",
    story: {
      ru: "Параметр τ говорит, сколько фотонов CMB рассеялось после того, как первые звёзды реионизировали Вселенную. Измерения WMAP (τ ≈ 0.17) создали сенсацию: они указывали на очень ранние звёзды. Planck позже уточнил τ до 0.054 — звёзды зажглись позже, около z ≈ 8.",
      en: "The τ parameter tells us how many CMB photons re-scattered after the first stars reionized the Universe. WMAP's first measurement (τ ≈ 0.17) made headlines: it suggested very early stars. Planck later revised τ down to 0.054 — stars lit up later, around z ≈ 8.",
    },
  }),
  H({
    id: "dl-rescaling",
    title: { ru: "Масштабирование D_ℓ = ℓ(ℓ+1) C_ℓ / 2π", en: "D_ℓ = ℓ(ℓ+1) C_ℓ / 2π rescaling" },
    author: { ru: "Техническая нормировка, принятая в сообществе", en: "Community-standard technical normalisation" },
    year: "~1990s",
    story: {
      ru: "Спектр C_ℓ сам по себе круто падает с ростом ℓ. Умножение на ℓ(ℓ+1)/(2π) «распрямляет» его: акустические пики становятся видны глазу, а плато Сакса-Вольфа выглядит плоским. Удобная условность, которой космологи пользуются 30+ лет.",
      en: "C_ℓ by itself drops steeply with ℓ. Multiplying by ℓ(ℓ+1)/(2π) 'flattens' the curve: the acoustic peaks become visually obvious, and the Sachs-Wolfe plateau is flat. A convention cosmologists have used for 30+ years.",
    },
  }),
]);

export function historyFor(id: string): MathHistory | undefined {
  return MATH_HISTORY[id];
}
