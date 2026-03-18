# Шаг 3: Обратная космология — ядро (Inverse Cosmology Engine)

**Статус:** завершён  
**Тестов:** 55 новых (121 всего по проекту), все пройдены  
**Зависимости:** PyTorch 2.10+, emcee 3.1+, corner 2.2+, scipy

---

## Обзор

Фаза 3 — **ключевая научная новизна проекта**. Классический подход в космологии: задаём параметры $\theta$, запускаем симуляцию, получаем наблюдаемые данные $x$. Мы делаем наоборот: по наблюдаемым данным $x$ восстанавливаем параметры $\theta$ — это **обратная космология**.

Формально: аппроксимируем апостериорное распределение $p(\theta | x)$, где:
- $x$ — карта температурной анизотропии CMB (или её спектр мощности $C_\ell$)
- $\theta = \{H_0, \Omega_b h^2, \Omega_{cdm} h^2, n_s, \ln(10^{10} A_s), \tau_{reio}\}$ — 6 базовых параметров $\Lambda$CDM

Реализованы два подхода:
1. **Байесовский CNN** — предсказание за миллисекунды с оценкой неопределённости
2. **MCMC (emcee)** — золотой стандарт, но медленный (~часы)

---

## Реализованные модули

### 1. `archeon/inverse/bayesian_cnn.py`

**Назначение:** нейронная сеть для мгновенного восстановления космологических параметров из CMB карты.

#### Архитектура

```
Input (1, H, W)
  └── Stem: Conv2d(1→32, 5×5) + BN + ReLU
  └── Encoder: 4× DownBlock (пространство /16, каналы ×16)
       └── DownBlock: Conv2d(stride=2) + BN + ReLU + ResidualBlock
       └── ResidualBlock: Conv→BN→ReLU→Conv→BN + skip connection
  └── GlobalAvgPool → (batch, 512)
  └── Dropout
  └── SharedFC: Linear(512→256→128) + ReLU + Dropout
  └── mu_head: Linear(128→6)       ← предсказанные параметры
  └── log_sigma_head: Linear(128→6) ← логарифм неопределённости
```

#### Ключевые классы и функции

| Класс/функция | Описание |
|---|---|
| `BayesianCosmologyCNN` | Основная модель. Вход: CMB патч (1, H, W). Выход: $\mu(\theta), \log\sigma(\theta)$ |
| `ResidualBlock` | Остаточный блок: два свёрточных слоя + skip connection |
| `DownBlock` | Блок уменьшения: stride-2 свёртка + ResidualBlock |
| `HeteroscedasticGaussianNLL` | Функция потерь (гетероскедастический NLL) |
| `CosmologyMLP` | Лёгкий MLP baseline для инференса из $C_\ell$ вектора |
| `predict_with_uncertainty()` | MC Dropout: N проходов с dropout → среднее + разброс |

#### Функция потерь

Гетероскедастический гауссовский NLL:

$$L = \sum_i \left[\frac{(\theta_i^{true} - \mu_i)^2}{2\sigma_i^2} + \log\sigma_i\right]$$

- **Первый член** штрафует за неточность предсказания, взвешенную уверенностью
- **Второй член** штрафует за чрезмерную неопределённость (нельзя просто сказать «я не знаю»)
- Модель учится выдавать бо́льшую $\sigma$ для сложных примеров

---

### 2. `archeon/inverse/mcmc_baseline.py`

**Назначение:** классический MCMC сэмплер для прямого исследования апостериорного распределения. Золотой стандарт в астрофизике для сравнения с CNN.

#### Метод

Используется **emcee** (Foreman-Mackey et al. 2013) — affine-invariant ensemble sampler:
- N «уокеров» (walkers) параллельно исследуют пространство параметров
- Affine-инвариантность: не чувствителен к корреляциям между параметрами
- De facto стандарт в космологии

#### Байесовская формула

$$p(\theta | x) \propto p(x | \theta) \cdot p(\theta)$$

где:
- $p(x | \theta)$ — **правдоподобие** (likelihood): насколько хорошо параметры $\theta$ объясняют данные $x$
- $p(\theta)$ — **априорное распределение** (prior): что мы знали до наблюдений
- $p(\theta | x)$ — **апостериорное распределение** (posterior): что мы знаем после

#### Ключевые функции

| Функция | Описание |
|---|---|
| `log_prior()` | Плоский (uniform) prior внутри физически допустимого диапазона |
| `log_likelihood_pk()` | Гауссовское правдоподобие по спектру мощности $P(k)$ |
| `log_likelihood_cl()` | Гауссовское правдоподобие по угловому спектру $C_\ell$ |
| `log_posterior()` | Prior + Likelihood = Posterior |
| `run_mcmc()` | Запуск emcee с burn-in, checkpointing, summary statistics |
| `MCMCResult` | Контейнер: цепочки, flat samples, медианы, квантили 16/84% |
| `plot_corner()` | Corner plot (треугольная матрица маргинальных распределений) |
| `plot_chains()` | Trace plots (диагностика сходимости цепочек) |

#### Параметры и диапазоны

| Параметр | Диапазон | Физический смысл |
|---|---|---|
| $H_0$ | [60, 80] km/s/Mpc | Постоянная Хаббла |
| $\Omega_b h^2$ | [0.019, 0.025] | Плотность барионов |
| $\Omega_{cdm} h^2$ | [0.10, 0.14] | Плотность тёмной материи |
| $n_s$ | [0.92, 1.02] | Скалярный спектральный индекс |
| $\ln(10^{10} A_s)$ | [2.5, 3.5] | Амплитуда примордиальных возмущений |
| $\tau_{reio}$ | [0.01, 0.12] | Оптическая глубина реионизации |

---

### 3. `archeon/inverse/uncertainty.py`

**Назначение:** три метода калибровки неопределённости + метрики качества.

#### MC Dropout

Идея: dropout при обучении — это приближённый вариационный вывод. Если оставить dropout включённым при предсказании и сделать $N$ прямых проходов:
- **Среднее** проходов → лучшее предсказание
- **Дисперсия** проходов → **эпистемическая неопределённость** (незнание модели)
- **Средняя предсказанная $\sigma$** → **алеаторическая неопределённость** (шум данных)

$$\text{Var}_{total} = \underbrace{\text{Var}[\mu_i]}_{\text{epistemic}} + \underbrace{\mathbb{E}[\sigma_i^2]}_{\text{aleatoric}}$$

#### Deep Ensembles

Ансамбль из $M$ независимо обученных моделей (Lakshminarayanan et al. 2017):
- Каждая модель получает свой random seed для инициализации и шаффлинга данных
- Разногласие между моделями = эпистемическая неопределённость
- На практике даёт лучшую калибровку, чем MC Dropout

#### Метрики калибровки

| Метрика | Формула / описание |
|---|---|
| **ECE** (Expected Calibration Error) | $\text{ECE} = \frac{1}{B} \sum_b \|\text{freq}_b - \text{conf}_b\|$ — средняя разница между заявленной и реальной вероятностью |
| **Coverage probability** | Доля истинных значений, попавших в доверительный интервал |
| **Sharpness** | Средняя ширина доверительных интервалов (меньше = точнее) |
| **Temperature scaling** | Посткалибровка: $\sigma_{cal} = T \cdot \sigma_{pred}$, $T > 1$ → модель overconfident |

#### Ключевые функции

| Функция | Описание |
|---|---|
| `mc_dropout_predict()` | N стохастических проходов → MCDropoutResult |
| `DeepEnsemble` | Класс ансамбля: predict(), save(), load() |
| `expected_calibration_error()` | ECE для регрессии |
| `coverage_probability()` | Покрытие на уровнях 50%, 68%, 90%, 95%, 99% |
| `calibrate_uncertainties()` | Полный калибровочный отчёт |
| `temperature_scale()` | Оптимальный T для пост-калибровки |

---

### 4. `archeon/inverse/evaluation.py`

**Назначение:** всесторонняя оценка моделей и сравнение CNN vs MCMC vs Planck.

#### Метрики по каждому параметру

| Метрика | Формула |
|---|---|
| **RMSE** | $\sqrt{\frac{1}{N}\sum(\hat{\theta}_i - \theta_i^{true})^2}$ |
| **Bias** | $\frac{1}{N}\sum(\hat{\theta}_i - \theta_i^{true})$ |
| **Mean $\sigma$** | Средняя предсказанная неопределённость |
| **Planck tension** | $\|\bar{\hat{\theta}} - \theta^{Planck}\| / \sigma^{Planck}$ в единицах $\sigma$ |
| **Coverage 68%** | Доля $\|\hat{\theta} - \theta^{true}\| \leq 1\sigma$ |
| **Coverage 95%** | Доля $\|\hat{\theta} - \theta^{true}\| \leq 1.96\sigma$ |

#### Референсные значения Planck 2018

| Параметр | Значение | Ошибка |
|---|---|---|
| $H_0$ | 67.36 | 0.54 |
| $\Omega_b h^2$ | 0.02237 | 0.00015 |
| $\Omega_{cdm} h^2$ | 0.1200 | 0.0012 |
| $n_s$ | 0.9649 | 0.0042 |
| $\ln(10^{10} A_s)$ | 3.044 | 0.014 |
| $\tau_{reio}$ | 0.0544 | 0.0073 |

#### Ключевые функции

| Функция | Описание |
|---|---|
| `evaluate_predictions()` | Полный отчёт по всем метрикам |
| `compare_cnn_vs_mcmc()` | Сравнение двух подходов: точность, калибровка, скорость |
| `benchmark_inference()` | Замер времени инференса в мс |
| `EvaluationReport.summary()` | Текстовый отчёт с таблицей |

---

### 5. `archeon/inverse/training.py`

**Назначение:** тренировочный цикл с логированием, нормализацией, early stopping, чекпоинтами.

#### Компоненты

| Класс/функция | Описание |
|---|---|
| `CMBDataset` | PyTorch Dataset: загрузка карт и параметров, нормализация, денормализация |
| `TrainConfig` | Dataclass гиперпараметров: batch_size, lr, epochs, patience и др. |
| `train_model()` | Полный цикл: AdamW + ReduceLROnPlateau + gradient clipping + early stopping |
| `train_ensemble()` | Обучение N независимых моделей для Deep Ensembles |
| `load_best_model()` | Загрузка лучшего чекпоинта |
| `TrainHistory` | Контейнер: train/val loss, learning rates, best epoch |

#### Нормализация (критически важна!)

CMB карты: значения ~[-300, +300] μK. Параметры: $H_0 \sim 67$, $\Omega_b h^2 \sim 0.022$, $\tau \sim 0.05$ — разные масштабы.

Без нормализации сеть будет доминироваться параметрами с большими значениями.

```
maps_norm = (maps - mean) / std
params_norm = (params - mean_per_param) / std_per_param
```

#### Тренировочный цикл

1. **Разбиение** train/val (85/15%)
2. **Оптимизатор** AdamW с weight decay
3. **Scheduler** ReduceLROnPlateau: уменьшение lr при стагнации val loss
4. **Gradient clipping**: предотвращение взрыва градиентов
5. **Early stopping**: остановка при patience эпох без улучшения
6. **Checkpointing**: сохранение лучшей модели и истории

---

## Терминология

| Термин | Определение |
|---|---|
| **Байесовский CNN** | CNN, который выдаёт не только предсказание, но и оценку неопределённости каждого предсказания |
| **Гетероскедастический NLL** | Функция потерь, где модель учится предсказывать разную дисперсию для разных входов |
| **Алеаторическая неопределённость** | Неустранимая: связана с шумом данных (шум детектора, cosmic variance). Не уменьшается с ростом данных |
| **Эпистемическая неопределённость** | Устранимая: связана с незнанием модели. Уменьшается с ростом обучающей выборки |
| **MC Dropout** | Monte Carlo Dropout: N стохастических проходов с dropout → дисперсия предсказаний ≈ эпистемическая неопределённость |
| **Deep Ensembles** | Ансамбль из M независимо обученных моделей. Разногласие = неопределённость |
| **MCMC** | Markov Chain Monte Carlo: метод сэмплирования из апостериорного распределения. Точен, но медленен |
| **emcee** | Affine-invariant ensemble sampler (Foreman-Mackey et al. 2013). Стандарт в астрофизике |
| **Posterior** $p(\theta \| x)$ | Апостериорное распределение: распределение параметров с учётом наблюдений |
| **Likelihood** $p(x \| \theta)$ | Правдоподобие: вероятность наблюдений при данных параметрах |
| **Prior** $p(\theta)$ | Априорное распределение: знание о параметрах до наблюдений |
| **ECE** | Expected Calibration Error: средняя разница между заявленной и реальной уверенностью |
| **Coverage probability** | Доля истинных значений, попавших в заявленный доверительный интервал |
| **Temperature scaling** | Постобработка для калибровки: $\sigma_{cal} = T \cdot \sigma_{raw}$ |
| **Corner plot** | Треугольная матрица 1D и 2D маргинальных распределений всех пар параметров |
| **Burn-in** | Начальные шаги MCMC, которые отбрасываются (цепочка ещё не сошлась к стационарному распределению) |
| **Affine-invariant** | Свойство сэмплера: производительность не зависит от корреляций между параметрами |
| **ResidualBlock** | Блок с skip connection: $y = F(x) + x$. Помогает обучать глубокие сети |
| **AdamW** | Оптимизатор Adam с decoupled weight decay (лучше обобщение) |
| **ReduceLROnPlateau** | Scheduler: уменьшает lr когда val loss перестаёт улучшаться |
| **Early stopping** | Остановка обучения когда val loss не улучшается $P$ эпох подряд |
| **Gradient clipping** | Ограничение нормы градиентов для стабильности обучения |

---

## Результаты тестирования

### Новые тесты (55)

#### `test_bayesian_cnn.py` (15 тестов)
- Формы выходов (mu, log_sigma)
- Clamping log_sigma в [-10, 5]
- MC Dropout даёт ненулевую эпистемическую дисперсию
- Batch independence: предсказания не зависят от состава батча
- Heteroscedastic loss: штрафует overconfidence, градиенты текут
- MLP baseline работает

#### `test_mcmc_baseline.py` (11 тестов)
- Prior: корректная поддержка, -inf вне границ
- params_to_cosmology: H0 сохраняется, Omega_m согласован, плоскость
- A_s конверсия из ln(10^10 A_s)
- Все параметры имеют корректные диапазоны

#### `test_uncertainty.py` (11 тестов)
- MC Dropout: формы, ненулевая эпистемическая дисперсия, total = epistemic + aleatoric
- Deep Ensemble: предсказания, разные модели расходятся
- ECE < 0.05 для идеально калиброванных предсказаний
- ECE > 0.3 для overconfident предсказаний
- Coverage монотонна по уровню уверенности
- Temperature scaling: T > 1 для overconfident, T ≈ 1 для калиброванных

#### `test_evaluation.py` (8 тестов)
- RMSE ≈ 0 для perfect predictions
- Report summary содержит все параметры
- Coverage: ~68% для идеальной неопределённости
- Planck значения: все присутствуют, ошибки > 0
- Benchmark: время > 0
- Comparison: speedup > 1000x

#### `test_training.py` (10 тестов)
- CMBDataset: длина, формы, нормализация, roundtrip денормализации
- 1D карты автоматически reshape в 2D
- Training: 3 эпохи без ошибок, loss уменьшается
- Checkpoint и history сохраняются
- load_best_model восстанавливает рабочую модель

### Полный набор тестов проекта

```
121 passed, 6 warnings in 14.98s
```

---

## Архитектура и зависимости

```
archeon/inverse/
├── __init__.py
├── bayesian_cnn.py    ← BayesianCosmologyCNN, HeteroscedasticGaussianNLL, CosmologyMLP
├── mcmc_baseline.py   ← run_mcmc(), MCMCResult, log_likelihood_pk/cl, plot_corner
├── uncertainty.py     ← mc_dropout_predict(), DeepEnsemble, ECE, coverage, temperature_scale
├── evaluation.py      ← evaluate_predictions(), compare_cnn_vs_mcmc(), benchmark_inference
└── training.py        ← CMBDataset, train_model(), train_ensemble(), load_best_model()
```

### Граф зависимостей

```
training.py
  └── bayesian_cnn.py (модели, loss)
  
uncertainty.py
  └── bayesian_cnn.py (модель для MC Dropout / Ensemble)
  └── scipy.stats (z-scores для coverage)
  
evaluation.py
  └── uncertainty.py (ECE)
  └── bayesian_cnn.py (PARAM_NAMES)
  
mcmc_baseline.py
  └── emcee (сэмплер)
  └── archeon.config (Planck параметры)
  └── archeon.physics.perturbations (P(k) для likelihood)
  └── archeon.data.synthetic (C_l для likelihood)
```

---

## Ограничения и следующие шаги

### Текущие ограничения

- **Нет реального обучения на данных Planck**: CNN обучается на синтетике, переход на реальные данные — задача Фазы 4
- **Приближённая likelihood**: MCMC использует упрощённый C_l (не CLASS), chi-squared может быть завышен
- **CPU only**: PyTorch CPU, GPU ускорит обучение в 10-100x
- **Нет domain adaptation**: синтетика ≠ реальность (foregrounds, маскирование, систематики)

### Следующие шаги (Фаза 4)

1. **Synthetic → Synthetic валидация**: обучить CNN на синтетике, проверить на отложенной синтетике
2. **Synthetic → Real**: применить CNN к данным Planck (domain gap — главный вызов)
3. **Noise robustness**: деградация точности при росте шума
4. **Сравнение с MCMC**: точность, калибровка, покрытие, скорость
5. **Формирование главного результата для публикации**
