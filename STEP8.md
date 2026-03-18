# Фаза 8: Альтернативные Космологии + Академический Движок

## Обзор

Фаза 8 состоит из двух частей:
1. **Альтернативные космологии** — 5 моделей за пределами стандартной ΛCDM
2. **Академический движок** — инструменты для генерации публикационных материалов

---

## Часть 1: Альтернативные Космологии (`archeon/physics/alternative.py`)

### Иерархия моделей

```
BaseCosmology (ABC)
├── hubble(a) → float
├── w_eff(a) → float
├── state(a) → CosmoState
├── expansion_history(a_arr) → dict
└── growth_factor(a_arr) → np.ndarray
    │
    ├── LCDMCosmology        ← стандартная модель (референс)
    ├── FRGravity             ← f(R) модифицированная гравитация
    ├── MONDCosmology         ← MOND без тёмной материи
    ├── VaryingConstantsCosmology ← изменение α, G, c
    ├── CyclicCosmology       ← циклическая Вселенная
    └── BraneCosmology        ← бранная космология (Randall-Sundrum)
```

### Модель 1: ΛCDM (LCDMCosmology)

Стандартная плоская модель. Служит эталоном для сравнения.

$$H^2(a) = H_0^2 \left[\frac{\Omega_r}{a^4} + \frac{\Omega_m}{a^3} + \Omega_\Lambda\right]$$

### Модель 2: f(R) Модифицированная Гравитация (FRGravity)

**Идея**: заменить скалярную кривизну R в действии Эйнштейна-Гильберта на произвольную функцию f(R).

**Реализация**: модель Ху-Савицкого (Hu-Sawicki):
$$f(R) = R - 2\Lambda + f_{R0} \cdot \frac{R_0^2}{R}$$

Модифицированное уравнение Фридмана:
$$H^2 = H_0^2 \left[\frac{\Omega_m}{a^3} + \Omega_\Lambda (1 + \delta_{fR}(a))\right]$$

где $\delta_{fR} = |f_{R0}| \cdot \left(\frac{\Omega_\Lambda}{\Omega_m/a^3 + \Omega_\Lambda}\right)^{n+1}$

| Параметр | Описание | Ограничение |
|----------|----------|-------------|
| f_R0 | Отклонение от ОТО сегодня | |f_R0| < 10⁻⁴ (наблюдения) |
| n_fR | Степенной индекс | обычно n=1 |

f_R0 = 0 точно воспроизводит ΛCDM.

**Скалярон**: f(R) эквивалентна скалярному полю (скалярону) с массой m² ∝ 1/(3|f_R|).

### Модель 3: MOND-Космология (MONDCosmology)

**Идея**: Modified Newtonian Dynamics — при ускорениях a < a₀ = 1.2×10⁻¹⁰ м/с² гравитация усиливается. Объясняет кривые вращения галактик без тёмной материи.

**Космологическая версия** (TeVeS/AQUAL-вдохновлённая):
$$H^2 = H_0^2 \left[\frac{\Omega_b}{a^3 \cdot \mu(x)} + \Omega_\Lambda\right]$$

где μ(x) — интерполирующая функция:
- "simple": μ(x) = x/(1+x)
- "standard": μ(x) = x/√(1+x²)

Ω_b ≈ 0.049 — только барионы (нет CDM).

### Модель 4: Вариация Фундаментальных Констант (VaryingConstantsCosmology)

**Идея**: что если "константы" не постоянны? Линейный дрейф:
$$X(a) = X_0 \cdot (1 + \delta_X \cdot (1 - a))$$

| Константа | Параметр | Физические последствия |
|-----------|----------|----------------------|
| α (постоянная тонкой структуры) | delta_alpha | Сдвиг температуры рекомбинации: ΔT/T ≈ 2·Δα/α |
| G (гравитационная) | delta_G | Сдвиг содержания He-4: ΔY_p ≈ 0.012·ΔG/G |
| c (скорость света) | delta_c | Теоретически: изменение горизонта |

Модифицированный Фридман: H² ∝ G(a) · ρ.

### Модель 5: Циклическая Космология (CyclicCosmology)

**Идея**: Вселенная проходит через повторяющиеся циклы расширения и сжатия (Steinhardt-Turok, Penrose CCC).

- `cycle_period`: длительность одного цикла
- `bounce_scale`: минимальный a при баунсе
- `turnaround_scale`: максимальный a перед контракцией

Вблизи turnaround: H → 0 (замедление), w пересекает "фантомный предел" w < -1.

### Модель 6: Бранная Космология (BraneCosmology)

**Идея**: наша 4D Вселенная — брана в 5D "bulk" (Randall-Sundrum II).

Модифицированный Фридман:
$$H^2 = H_0^2 \left[\frac{\Omega_m}{a^3} + \Omega_\Lambda + \frac{\Omega_m^2}{2\lambda \cdot a^6}\right]$$

Член ρ² / λ — коррекция от дополнительного измерения. Значим только при высоких плотностях (ранняя Вселенная).

При λ → ∞ восстанавливается стандартная ΛCDM.

### Утилиты

| Функция | Описание |
|---------|----------|
| `compare_models()` | Сравнение H(a) и w(a) нескольких моделей; H_ratio относительно первой |
| `compute_observables()` | Расчёт d_L(z), d_A(z), χ(z) из H(z) |

---

## Часть 2: Академический Движок (`archeon/academic/`)

### Модуль 1: LaTeX Экспорт (`latex_export.py`)

Генерация публикационных фигур и таблиц.

**Стили журналов:**

| Журнал | Ширина колонки | Шрифт |
|--------|---------------|-------|
| ApJ | 3.5" / 7.1" | 10pt serif |
| MNRAS | 3.32" / 6.97" | 9pt serif |
| A&A | 3.54" / 7.09" | 9pt serif |

**Функции:**

| Функция | Описание |
|---------|----------|
| `apply_journal_style()` | Применить rcParams matplotlib для конкретного журнала |
| `plot_power_spectrum()` | D_l = l(l+1)C_l/2π — стандартный CMB-спектр |
| `plot_parameter_comparison()` | Whisker plot для сравнения методов |
| `parameters_to_latex()` | LaTeX-таблица параметров с tension σ |
| `comparison_to_latex()` | Мульти-метод LaTeX-таблица |

### Модуль 2: Цитирование (`citation.py`)

Каждый запуск симуляции получает уникальный идентификатор и BibTeX-запись.

| Класс / функция | Описание |
|------------------|----------|
| `SimulationRecord` | Запись о симуляции: модель, параметры, дата |
| `uid` | SHA256[:12] от (model, params, date) — детерминированный ID |
| `citation_key` | BibTeX-ключ: `archeon_<model>_<uid>` |
| `generate_bibtex()` | Полная BibTeX-запись (@misc) |
| `generate_data_citation()` | Человекочитаемая строка цитирования |
| `batch_bibtex()` | .bib файл для множества запусков |
| `record_to_json()` | Сериализация в JSON с uid и citation_key |

### Модуль 3: Воспроизводимость (`reproducibility.py`)

Полная фиксация состояния эксперимента.

**EnvironmentInfo** захватывает:
- Python version, platform, hostname
- Версии ключевых пакетов (numpy, torch, jax, ...)
- Git hash + dirty status

**ExperimentRecord**:
- Имя, описание, timestamp
- Все параметры и seeds
- Контрольные суммы входных/выходных файлов (SHA256)
- Метрики
- UID (SHA256[:16])

| Функция | Описание |
|---------|----------|
| `create_experiment()` | Создать запись с auto-capture окружения |
| `save_experiment()` | Сохранить в JSON |
| `load_experiment()` | Загрузить из JSON |
| `verify_reproducibility()` | Проверить совпадение окружения |
| `checksum_file()` | SHA256 контрольная сумма файла |

### Модуль 4: Генератор Ноутбуков (`notebook_generator.py`)

Автоматическая генерация self-contained Jupyter-ноутбуков.

**Шаблоны:**

| Шаблон | Содержание |
|--------|------------|
| `generate_inference_notebook()` | Генерация данных → обучение эмулятора → оценка → визуализация → BibTeX |
| `generate_anomaly_notebook()` | Карты → автоэнкодер → anomaly scores → статистика → визуализация |
| `generate_alternative_cosmo_notebook()` | Все 5 моделей → H(a) → w(a) → d_L(z) сравнение |

Каждый ноутбук — полный pipeline от данных до результатов, воспроизводимый одним "Run All".

---

## Результаты валидации

### Тесты

| Группа | Тестов | Статус |
|--------|--------|--------|
| TestLCDM | 6 | ✅ |
| TestFRGravity | 4 | ✅ |
| TestMOND | 3 | ✅ |
| TestVaryingConstants | 4 | ✅ |
| TestCyclic | 2 | ✅ |
| TestBrane | 3 | ✅ |
| TestModelComparison | 2 | ✅ |
| TestLatexExport | 5 | ✅ |
| TestCitation | 7 | ✅ |
| TestReproducibility | 5 | ✅ |
| TestNotebookGenerator | 4 | ✅ |
| **Итого Фаза 8** | **45** | **✅** |
| **Весь проект** | **280** | **✅** |

### Что проверяют тесты

- **ΛCDM**: H(1) ≈ 67.36, H monotonically increases toward a→0, w→1/3 early, w→−1 late
- **f(R)**: f_R0=0 восстанавливает GR, сильнее f_R0 → большее отличие от ΛCDM
- **MOND**: H > 0, без CDM (Ω_b < 0.1)
- **Varying constants**: ΔG→0 → ΛCDM, recombination shift = 2·Δα/α
- **Cyclic**: H > 0 на всех фазах, turnaround time > 0
- **Brane**: λ→∞ → ΛCDM, ρ² коррекция при малых a
- **LaTeX**: корректные \begin{table}, параметры и tension σ
- **Citation**: UID детерминированный, зависит от параметров, BibTeX формат
- **Reproducibility**: capture/save/load/verify, checksum
- **Notebooks**: nbformat 4, содержат code cells, сохраняются на диск

---

## Структура файлов

```
archeon/physics/
└── alternative.py       ← 5 космологических моделей + BaseCosmology + утилиты

archeon/academic/
├── __init__.py
├── latex_export.py      ← LaTeX-фигуры, таблицы, стили журналов
├── citation.py          ← BibTeX, уникальные ID симуляций
├── reproducibility.py   ← Захват окружения, save/load экспериментов
└── notebook_generator.py ← Автогенерация .ipynb (3 шаблона)

tests/
└── test_phase8.py       ← 45 тестов
```

---

## Глоссарий

| Термин | Определение |
|--------|-------------|
| **f(R) gravity** | Модификация ОТО: действие ∫f(R)√-g d⁴x вместо ∫R√-g d⁴x. Эквивалентна скалярно-тензорной теории |
| **Hu-Sawicki model** | Конкретная форма f(R) = R − 2Λ + f_R0·R₀²/R. Проходит тесты Солнечной системы при |f_R0| < 10⁻⁴ |
| **Scalaron** | Скалярное поле, возникающее из f(R). Его масса определяет радиус действия "пятой силы" |
| **MOND** | Modified Newtonian Dynamics. При a < a₀ ≈ 1.2×10⁻¹⁰ м/с² гравитация усиливается: F = m·√(a_N·a₀) |
| **Interpolating function μ(x)** | Плавный переход между ньютоновским (μ→1) и MONDовским (μ→x) режимами |
| **Fine structure constant α** | α = e²/(4πε₀ℏc) ≈ 1/137. Определяет силу электромагнитного взаимодействия |
| **BBN** | Big Bang Nucleosynthesis. Синтез лёгких элементов в первые 3 минуты. Чувствителен к G, α |
| **Cyclic cosmology** | Вселенная проходит бесконечные циклы расширения/сжатия. Penrose CCC: конец одного эона = начало следующего |
| **Phantom divide** | w = −1. Модели с w < −1 ("фантомная" тёмная энергия) нарушают слабое энергетическое условие |
| **Brane** | (p+1)-мерная гиперповерхность в высшем пространстве. Наша Вселенная = 3-брана в 5D bulk |
| **Randall-Sundrum** | Модель с одной или двумя бранами в AdS₅ bulk. Решает проблему иерархии масс |
| **Brane tension λ** | Энергия на единицу объёма браны. λ → ∞ восстанавливает 4D ОТО |
| **BibTeX** | Формат библиографических записей LaTeX. Каждая запись имеет тип (@article, @misc) и ключ |
| **nbformat** | Формат файлов Jupyter Notebook (.ipynb). Версия 4 — текущий стандарт |

---

## Ограничения

1. **f(R)**: упрощённая формула Hu-Sawicki. Для точных расчётов нужно решение полного уравнения скалярона
2. **MOND**: феноменологическая космологическая адаптация, не строгая TeVeS/AQUAL
3. **Cyclic**: параметрическая модель, не выведена из конкретной теории струн
4. **Growth factor**: общий ODE-солвер, для f(R) нужна модификация (scale-dependent growth)
5. **LaTeX**: usetex=False по умолчанию (не требует полного LaTeX)

---

## Следующий шаг

→ **Фаза 9**: Финализация — arXiv preprint каркас, Docker/CI/CD, документация, README, tutorial notebooks.
