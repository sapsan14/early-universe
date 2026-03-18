# Шаг 4: Обратная космология — валидация (Inverse Cosmology Validation)

**Статус:** завершён  
**Тестов:** 16 новых (137 всего по проекту), все пройдены  
**Модуль:** `archeon/inverse/validation.py`

---

## Обзор

Фаза 4 — **экспериментальная валидация** всех компонентов обратной космологии (Фаза 3). Ключевые вопросы:

1. **Может ли CNN вообще восстановить параметры?** (Synthetic → Synthetic)
2. **Насколько устойчив CNN к шуму?** (Noise Robustness)
3. **CNN vs MCMC**: точность, калибровка, скорость — что лучше и когда?
4. **Согласуется ли с Planck?** (Planck Tension)
5. **Работает ли на реальных данных?** (Domain Gap Analysis)

Это **формирование главного результата для публикации**: CNN восстанавливает космологические параметры за миллисекунды с калиброванной неопределённостью.

---

## Реализованные эксперименты

### 1. Synthetic → Synthetic Validation (Proof of Concept)

**Цель:** убедиться, что Байесовский CNN может восстановить параметры $\theta$ из CMB карт, которые были сгенерированы с этими же параметрами.

**Пайплайн:**

```
Шаг 1: Сгенерировать N_train + N_test синтетических CMB карт
        theta_i ~ Prior(theta)  →  C_l(theta_i)  →  CMB_map_i
Шаг 2: Обучить BayesianCNN на train: (CMB_map → theta)
Шаг 3: Применить к test: MC Dropout → mu(theta), sigma(theta)
Шаг 4: Сравнить mu vs theta_true → RMSE, Coverage, ECE
```

**Ключевой API:**

```python
result = run_synthetic_validation(
    n_train=500, n_test=100,
    map_size=64, n_epochs=30,
    base_channels=16, mc_samples=50,
)
print(result.eval_report.summary())
```

**Что это доказывает:** если CNN не может восстановить параметры из собственных синтетических данных, он не будет работать на реальных данных. Это — нулевой чекпоинт.

---

### 2. Noise Robustness Analysis

**Цель:** измерить деградацию точности при росте шума детектора.

Реальные данные Planck содержат инструментальный шум (~1–5% от сигнала CMB). Если CNN обучен на «чистых» картах, он должен быть устойчив к умеренному шуму.

**Подход:**

1. Обучить CNN на чистых синтетических данных
2. Добавить шум возрастающей амплитуды к тестовым картам: $\text{map}_{noisy} = \text{map}_{clean} + \sigma_{noise} \cdot \mathcal{N}(0, 1)$
3. Измерить RMSE, ECE, Coverage на каждом уровне шума

**Уровни шума:** [0%, 1%, 5%, 10%, 20%, 50%, 100%] от стандартного отклонения карты

**Ключевой API:**

```python
result = run_noise_robustness(
    model, train_dataset, test_params,
    noise_levels=[0.0, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
)
```

**Ожидания:**
- RMSE должна монотонно расти с шумом
- При шуме <5% деградация минимальна
- При шуме >50% модель теряет информацию
- Калиброванная модель должна увеличивать $\sigma$ вместе с шумом

---

### 3. CNN vs MCMC Comparison

**Цель:** прямое сравнение двух подходов на одних и тех же данных.

| Метрика | CNN | MCMC |
|---|---|---|
| **Скорость** | ~мс | ~часы |
| **Точность** | RMSE | RMSE |
| **Калибровка** | MC Dropout | Posterior samples |
| **Масштабируемость** | Батчами, GPU | Последовательно |

**Подход:**

1. Выбрать N тестовых CMB карт (N ≤ 5 из-за скорости MCMC)
2. **CNN**: MC Dropout → $\mu(\theta), \sigma(\theta)$ за миллисекунды
3. **MCMC**: emcee с тем же likelihood → posterior → медианы и стандартные отклонения за секунды/минуты
4. Сравнить: RMSE, согласованность (sigma-distance), speedup

**Ключевой API:**

```python
result = run_cnn_vs_mcmc_comparison(
    model, test_maps, test_params,
    train_dataset, mc_samples=50,
    mcmc_steps=2000, mcmc_walkers=32,
)
print(f"Speedup: {result.speedup:.0f}x")
print(f"Agreement: {result.agreement}")
```

**Метрика согласованности:**

$$\Delta_i = \frac{|\mu_i^{CNN} - \mu_i^{MCMC}|}{\sqrt{\sigma_i^{CNN,2} + \sigma_i^{MCMC,2}}}$$

$\Delta < 1\sigma$ — отличное согласование. $\Delta < 2\sigma$ — приемлемое. $\Delta > 3\sigma$ — проблема.

---

### 4. Planck Comparison

**Цель:** сравнить агрегированные предсказания модели с опубликованными значениями Planck 2018.

Референсные значения (TT,TE,EE+lowE+lensing):

| Параметр | Planck 2018 | $\sigma$ |
|---|---|---|
| $H_0$ | 67.36 | 0.54 |
| $\Omega_b h^2$ | 0.02237 | 0.00015 |
| $\Omega_{cdm} h^2$ | 0.1200 | 0.0012 |
| $n_s$ | 0.9649 | 0.0042 |
| $\ln(10^{10} A_s)$ | 3.044 | 0.014 |
| $\tau_{reio}$ | 0.0544 | 0.0073 |

**Метрика tension:**

$$\text{Tension} = \frac{|\bar{\theta}_{our} - \theta_{Planck}|}{\sqrt{\sigma_{our}^2 + \sigma_{Planck}^2}}$$

$< 2\sigma$ — **consistent**, $> 3\sigma$ — **tension** (интересный результат!), $> 5\sigma$ — **exclusion**

**Ключевой API:**

```python
results = compare_with_planck(mu_pred, sigma_pred)
for r in results:
    print(f"{r.param_name}: {r.tension_sigma:.2f}σ {'✓' if r.consistent else '✗'}")
```

---

### 5. Domain Gap Analysis (Synthetic → Real)

**Цель:** количественно оценить разрыв между синтетическими и реальными CMB данными.

**Проблема:** CNN обучен на упрощённых синтетических картах. Реальные данные Planck содержат:
- Foreground contamination (пыль, синхротронное излучение, свободно-свободное)
- Маскирование галактической плоскости
- Инструментальные артефакты
- Beam convolution
- Точечные источники

**Подход:**

1. Извлечь признаки из encoder CNN (feature vectors)
2. Сравнить распределения признаков для синтетических и реальных карт
3. Метрики: feature distance (Mahalanobis-like), feature overlap fraction

**Ключевой API:**

```python
result = analyze_domain_gap(model, synthetic_maps, real_maps)
print(f"Feature distance: {result.real_feature_distance:.2f}")
print(f"Overlap: {result.feature_overlap_fraction:.1%}")
print(f"→ {result.recommendation}")
```

**Рекомендации на основе distance:**
- LOW gap (<1.0, overlap >80%): синтетика переносится на реальность
- MODERATE (1.0–3.0): нужен fine-tuning на малой выборке реальных данных
- HIGH (>3.0): необходима domain adaptation или моделирование шума

---

## Терминология

| Термин | Определение |
|---|---|
| **Synthetic → Synthetic** | Обучение и тестирование на синтетических данных. Proof of concept: если не работает здесь, не будет работать нигде |
| **Synthetic → Real** | Обучение на синтетике, тестирование на реальных данных. Главный вызов из-за domain gap |
| **Domain gap** | Разрыв между распределением обучающих (синтетических) и тестовых (реальных) данных. Причины: foregrounds, шум, beam |
| **Noise robustness** | Устойчивость модели к инструментальному шуму. Измеряется как деградация RMSE при росте $\sigma_{noise}$ |
| **Planck tension** | Количественная мера разногласия между нашим измерением и Planck. В единицах $\sigma$ |
| **Speedup** | Отношение времени MCMC / времени CNN. Ожидается $10^3$–$10^6$ |
| **Feature distance** | Расстояние между распределениями внутренних представлений CNN для двух наборов данных |
| **Feature overlap** | Доля реальных данных, попадающих в $\pm 2\sigma$ от распределения синтетических признаков |
| **Proof of concept** | Первая демонстрация работоспособности подхода в контролируемых условиях |
| **Degradation analysis** | Систематическое изучение того, как ухудшается качество при ухудшении условий |
| **Burn-in** | Начальные шаги MCMC, отбрасываемые до сходимости к стационарному распределению |
| **Weighted mean** | Среднее, взвешенное обратными дисперсиями: $\bar{\theta} = \sum w_i \theta_i / \sum w_i$, $w_i = 1/\sigma_i^2$ |
| **Mahalanobis distance** | Расстояние с учётом ковариации: $d = \sqrt{(\mu_1 - \mu_2)^T \Sigma^{-1} (\mu_1 - \mu_2)}$ |
| **Domain adaptation** | Методы снижения domain gap: fine-tuning, adversarial training, data augmentation |
| **Foregrounds** | Астрофизические фоны, загрязняющие CMB: пыль, синхротрон, свободно-свободное излучение |
| **Beam convolution** | Сглаживание CMB карты из-за конечного размера телескопа |
| **Cosmic variance** | Фундаментальная неустранимая неопределённость: мы наблюдаем только одну реализацию Вселенной. $\Delta C_\ell / C_\ell \sim \sqrt{2/(2\ell+1)}$ |

---

## Результаты тестирования

### Новые тесты (16)

#### `test_validation.py`

| Тест | Что проверяет |
|---|---|
| `test_shapes` | Размерности train/test maps и params |
| `test_different_seeds_differ` | Разные seed дают разные данные |
| `test_noise_adds_variance` | Шум увеличивает дисперсию карт |
| `test_params_in_physical_range` | Параметры в физическом диапазоне |
| `test_runs_end_to_end` | Полный пайплайн: generate→train→evaluate |
| `test_results_saved` | JSON с результатами сохраняется |
| `test_to_dict` | Сериализация ValidationResult |
| `test_rmse_increases_with_noise` | Noise robustness pipeline |
| `test_to_dict` (Noise) | Сериализация NoiseRobustnessResult |
| `test_perfect_planck_predictions` | Planck значения → tension ≈ 0 |
| `test_discrepant_H0` | H0=73 → tension > 2σ с Planck |
| `test_all_planck_params_covered` | Все 6 параметров покрыты |
| `test_same_distribution_low_gap` | Одинаковые распределения → малый gap |
| `test_different_distribution_higher_gap` | Разные распределения → больший gap |
| `test_recommendation_present` | Рекомендация заполнена |
| `test_comparison_runs` (slow) | CNN vs MCMC пайплайн запускается |

### Полный набор

```
137 passed, 8 warnings in 15.44s
```

---

## Архитектура

```
archeon/inverse/validation.py
├── generate_validation_data()     ← генерация train/test CMB карт
├── run_synthetic_validation()     ← Synthetic → Synthetic эксперимент
├── run_noise_robustness()         ← деградация при росте шума
├── run_cnn_vs_mcmc_comparison()   ← CNN vs MCMC на одних данных
├── compare_with_planck()          ← сравнение с Planck 2018
├── analyze_domain_gap()           ← оценка domain gap Syn→Real
│
├── ValidationResult               ← контейнер результатов
├── NoiseRobustnessResult          ← результаты шумового анализа
├── CNNvsMCMCResult                ← сравнение CNN/MCMC
├── PlanckComparisonResult         ← tension с Planck
└── DomainGapResult                ← domain gap метрики
```

### Зависимости

```
validation.py
  └── bayesian_cnn.py (модель)
  └── training.py (CMBDataset, TrainConfig, train_model)
  └── uncertainty.py (mc_dropout_predict, calibrate_uncertainties)
  └── evaluation.py (evaluate_predictions, PLANCK_2018)
  └── mcmc_baseline.py (run_mcmc, log_likelihood_cl)
  └── data/priors.py (generate_parameter_sets)
  └── data/synthetic.py (compute_cl_internal)
```

---

## Ограничения и следующие шаги

### Текущие ограничения

- **Приближённая C_l**: используется Eisenstein-Hu (~5% точность), не CLASS (<0.1%)
- **Flat-sky approximation**: проекция CMB сферы на плоскость теряет информацию на больших масштабах ($\ell < 30$)
- **CPU only**: обучение на CPU, GPU ускорит в 10-100×
- **Маленькие выборки**: тестовые эксперименты на 100-500 картах, для публикации нужно 10k-100k
- **Нет real foregrounds**: domain gap анализ пока только на уровне feature distance

### Что нужно для публикации

1. **Масштабирование**: обучить CNN на 50k+ синтетических карт (GPU)
2. **CLASS backend**: генерировать C_l через CLASS для <0.1% точности
3. **Реальные данные Planck**: загрузить карту, применить маску, вырезать патчи
4. **Fine-tuning**: адаптировать CNN к реальным данным через transfer learning
5. **Сравнение**: CNN vs emcee MCMC на полном Planck likelihood
6. **Публикация**: arXiv preprint с фигурами (corner plots, noise degradation, speedup)

### Следующие шаги (Фаза 5)

- **CMB Autoencoder**: детектор аномалий для Cold Spot, негауссовости
- **Anomaly detection**: статистические тесты на реальных данных Planck
- **VAE compression**: latent space космологических полей
