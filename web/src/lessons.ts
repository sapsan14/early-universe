/**
 * Course outline — eight chapters with bilingual metadata. The chapter
 * pages themselves live in `components/lessons/`, but storing the outline
 * here lets every part of the app (home page, navigation, progress ring)
 * use the same source of truth.
 */

import type { Phrase } from "./i18n";

export interface ChapterMeta {
  id: string;
  number: number;
  title: Phrase;
  subtitle: Phrase;
  glyph: string;
  duration: Phrase;
  difficulty: 1 | 2 | 3;
  color: string;
  /** Short list of "you'll learn" bullets shown on the home/index card. */
  highlights: Phrase[];
  /** Tags shown on the chapter card. */
  tags: Phrase[];
}

export const CHAPTERS: ChapterMeta[] = [
  {
    id: "intro",
    number: 1,
    title: { ru: "Что такое космология?", en: "What is cosmology?" },
    subtitle: {
      ru: "Знакомимся с языком Вселенной и инструментами учёных.",
      en: "Meet the language of the Universe and the tools cosmologists use.",
    },
    glyph: "✺",
    duration: { ru: "10 минут", en: "10 minutes" },
    difficulty: 1,
    color: "#9b8cff",
    highlights: [
      { ru: "Чем космология отличается от астрономии", en: "Cosmology vs. astronomy" },
      { ru: "Что мы можем измерить и что — нет", en: "What we can measure and what we can't" },
      { ru: "Шесть чисел, описывающих Вселенную", en: "Six numbers that describe the Universe" },
    ],
    tags: [{ ru: "Введение", en: "Intro" }],
  },
  {
    id: "big-bang",
    number: 2,
    title: { ru: "Большой Взрыв и Планковская эпоха", en: "The Big Bang & the Planck Epoch" },
    subtitle: {
      ru: "Самое начало — где наша физика впервые встречается с пределами знания.",
      en: "The very first instant — where physics first meets the edge of knowledge.",
    },
    glyph: "❂",
    duration: { ru: "12 минут", en: "12 minutes" },
    difficulty: 1,
    color: "#ff7ac6",
    highlights: [
      { ru: "Почему это не «взрыв в пустоте»", en: "Why it's not an 'explosion in space'" },
      { ru: "Что такое t_P, ℓ_P и почему меньше нельзя", en: "What t_P, ℓ_P are and why nothing is smaller" },
      { ru: "Объединение четырёх сил природы", en: "How the four fundamental forces merge" },
    ],
    tags: [{ ru: "Эпоха", en: "Epoch" }],
  },
  {
    id: "inflation",
    number: 3,
    title: { ru: "Инфляция — Великое Растяжение", en: "Inflation — the Great Stretch" },
    subtitle: {
      ru: "За 10⁻³² секунды Вселенная выросла больше, чем за все следующие миллиарды лет.",
      en: "In 10⁻³² s the Universe grew more than in all the billions of years that followed.",
    },
    glyph: "✸",
    duration: { ru: "14 минут", en: "14 minutes" },
    difficulty: 2,
    color: "#ff8b5e",
    highlights: [
      { ru: "Проблемы плоскости и горизонта", en: "Flatness & horizon problems" },
      { ru: "Квантовая рябь как зародыши галактик", en: "Quantum jitter as galactic seeds" },
      { ru: "Параметры n_s и A_s — наши «отпечатки инфляции»", en: "n_s and A_s — our fingerprints of inflation" },
    ],
    tags: [{ ru: "Эпоха", en: "Epoch" }, { ru: "Параметры", en: "Parameters" }],
  },
  {
    id: "bbn",
    number: 4,
    title: { ru: "Космическая кухня", en: "The Cosmic Kitchen" },
    subtitle: {
      ru: "За три минуты сваривается рецепт водорода и гелия — основа звёзд и нашего тела.",
      en: "In three minutes the cosmos cooks the recipe of hydrogen and helium — the stuff of stars and us.",
    },
    glyph: "✪",
    duration: { ru: "10 минут", en: "10 minutes" },
    difficulty: 2,
    color: "#7afcb1",
    highlights: [
      { ru: "Откуда берётся 75% водорода и 25% гелия", en: "Where 75% H and 25% He come from" },
      { ru: "Заморозка нейтрон-протонного отношения", en: "Neutron-to-proton freeze-out" },
      { ru: "Почему Ω_b h² нельзя двигать слишком сильно", en: "Why we cannot push Ω_b h² too far" },
    ],
    tags: [{ ru: "Эпоха", en: "Epoch" }],
  },
  {
    id: "cmb",
    number: 5,
    title: { ru: "Первый свет: реликтовое излучение", en: "First Light: the CMB" },
    subtitle: {
      ru: "380 000 лет — и Вселенная отпускает свет на свободу. Сегодня он рассказывает нам всё.",
      en: "After 380 000 years the Universe releases light. Today it tells us everything.",
    },
    glyph: "☀",
    duration: { ru: "16 минут", en: "16 minutes" },
    difficulty: 2,
    color: "#ffd56b",
    highlights: [
      { ru: "Что такое поверхность последнего рассеяния", en: "The last-scattering surface" },
      { ru: "Как читать спектр C_ℓ", en: "How to read the C_ℓ spectrum" },
      { ru: "Где прячутся барионы и тёмная материя", en: "Where baryons and dark matter hide in the sky" },
    ],
    tags: [{ ru: "Наблюдение", en: "Observable" }],
  },
  {
    id: "dawn",
    number: 6,
    title: { ru: "Тёмные века и Космический рассвет", en: "Dark Ages & Cosmic Dawn" },
    subtitle: {
      ru: "Зажигаются первые звёзды, и Вселенная вспыхивает заново.",
      en: "The first stars ignite and the Universe lights up all over again.",
    },
    glyph: "✶",
    duration: { ru: "12 минут", en: "12 minutes" },
    difficulty: 2,
    color: "#5ee2ff",
    highlights: [
      { ru: "Почему между CMB и звёздами было «пусто»", en: "Why it went 'dark' after the CMB" },
      { ru: "Звёзды Population III — первые во Вселенной", en: "Population III — the first stars ever" },
      { ru: "Реионизация и параметр τ_reio", en: "Reionization and τ_reio" },
    ],
    tags: [{ ru: "Эпоха", en: "Epoch" }],
  },
  {
    id: "ingredients",
    number: 7,
    title: { ru: "Шесть ингредиентов Вселенной", en: "Six Ingredients of the Universe" },
    subtitle: {
      ru: "Шесть чисел Planck — и из них вылепливается всё, что мы наблюдаем.",
      en: "Six Planck numbers — from them grows everything we see.",
    },
    glyph: "✦",
    duration: { ru: "18 минут", en: "18 minutes" },
    difficulty: 3,
    color: "#9b8cff",
    highlights: [
      { ru: "H₀, Ω_b h², Ω_cdm h², n_s, A_s, τ_reio — что они значат", en: "H₀, Ω_b h², Ω_cdm h², n_s, A_s, τ_reio — what they mean" },
      { ru: "Как Planck измерил их с точностью до долей процента", en: "How Planck measured them to a fraction of a percent" },
      { ru: "Загадка H₀: тенсия в современной космологии", en: "The H₀ tension mystery" },
    ],
    tags: [{ ru: "Параметры", en: "Parameters" }],
  },
  {
    id: "play",
    number: 8,
    title: { ru: "Игра в бога: меняем Вселенную", en: "Playing God: Tweaking the Universe" },
    subtitle: {
      ru: "Подвинь параметры — и посмотри, какая Вселенная получится. Будут ли в ней звёзды? Жизнь?",
      en: "Slide the parameters and watch a new Universe form. Will it host stars? Life?",
    },
    glyph: "✺",
    duration: { ru: "Без ограничений", en: "No limit" },
    difficulty: 3,
    color: "#ff7ac6",
    highlights: [
      { ru: "Запускай симуляции и наблюдай рост структур", en: "Run simulations and watch structure grow" },
      { ru: "Учись отличать «жилые» Вселенные от «мёртвых»", en: "Learn to tell habitable from sterile universes" },
      { ru: "Охоться на аномалии в CMB-картах", en: "Hunt for anomalies in CMB maps" },
    ],
    tags: [{ ru: "Лаборатория", en: "Lab" }],
  },
];

export function chapterById(id: string): ChapterMeta | undefined {
  return CHAPTERS.find((c) => c.id === id);
}
