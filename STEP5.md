# Шаг 5: Детектор аномалий CMB + Сжатие Вселенной

**Статус:** завершён
**Тестов:** 34 новых (171 всего по проекту), все пройдены
**Модули:** `archeon/anomaly/` (4 файла), `archeon/compression/` (3 файла)

---

## Обзор

Фаза 5 объединяет два связанных направления:

1. **Детектор аномалий CMB** — поиск отклонений от стандартной $\Lambda$CDM модели в данных CMB. Ключевой вопрос: есть ли в данных Planck что-то, чего не предсказывает стандартная космология?

2. **Сжатие Вселенной** — VAE для обнаружения скрытых связей между космологическими параметрами через анализ латентного пространства.

---

## Модуль 1: Детектор аномалий CMB

### `archeon/anomaly/autoencoder.py`

**Идея:** обучить автоэнкодер реконструировать «нормальные» CMB-карты ($\Lambda$CDM). Высокая ошибка реконструкции = аномалия.

| Класс/функция | Описание |
|---|---|
| `CMBAutoencoder` | Conv autoencoder: encoder (4 блока conv+BN+ReLU+pool) $\to$ latent vector $\to$ decoder (4 блока upsample+conv) |
| `EncoderBlock` | Conv $\to$ BN $\to$ ReLU $\to$ Conv $\to$ BN $\to$ ReLU $\to$ MaxPool |
| `DecoderBlock` | Upsample $\to$ Conv $\to$ BN $\to$ ReLU (опционально skip connections) |
| `AnomalyMap` | Результат: pixel_scores, global_score, threshold, anomalous_fraction, anomalous_mask |
| `compute_anomaly_scores()` | Вычислить per-pixel anomaly scores для батча карт |
| `train_autoencoder()` | Обучить autoencoder на чистых $\Lambda$CDM картах |

**Аномальный скор:** $S_{pixel} = (x_{pixel} - \hat{x}_{pixel})^2$ — квадрат ошибки реконструкции.

---

### `archeon/anomaly/latent_analysis.py`

**Идея:** анализ скрытого пространства автоэнкодера выявляет кластеры, выбросы и размерность.

| Функция | Описание |
|---|---|
| `extract_latent_vectors()` | Encode батч карт $\to$ латентные векторы |
| `detect_outliers()` | Mahalanobis distance в latent space, порог через $\sigma$ |
| `analyze_dimensionality()` | PCA латентного пространства: сколько эффективных измерений? |
| `reduce_to_2d()` | Проекция в 2D: PCA, t-SNE или UMAP для визуализации |
| `latent_parameter_correlation()` | Корреляция латентных измерений с физическими параметрами |

**Расстояние Махаланобиса:** $d_M = \sqrt{(\mathbf{z} - \boldsymbol{\mu})^T \Sigma^{-1} (\mathbf{z} - \boldsymbol{\mu})}$ — учитывает корреляции между латентными измерениями.

---

### `archeon/anomaly/statistical_tests.py`

**Идея:** количественная оценка значимости аномалий.

| Функция | Описание |
|---|---|
| `ks_test_pixels()` | Kolmogorov-Smirnov тест на распределения пикселей |
| `anderson_darling_test()` | Anderson-Darling тест на гауссовость |
| `check_non_gaussianity()` | Skewness + kurtosis + p-values |
| `chi_squared_power_spectrum()` | $\chi^2$ тест $C_\ell^{obs}$ vs $C_\ell^{theory}$ с cosmic variance |
| `monte_carlo_significance()` | P-value из MC сравнения с N симуляциями |

**Cosmic variance:** $\text{Var}(C_\ell) = \frac{2 C_\ell^2}{2\ell + 1}$ — фундаментальная неопределённость от наблюдения одной реализации Вселенной.

---

### `archeon/anomaly/cold_spot.py`

**Идея:** специализированный анализ Cold Spot — самой обсуждаемой аномалии CMB.

| Функция | Описание |
|---|---|
| `find_cold_spots()` | Поиск холодных регионов: smoothing $\to$ threshold $\to$ connected components |
| `compute_radial_profile()` | Азимутально-усреднённый профиль температуры вокруг точки |
| `cold_spot_mc_significance()` | Monte Carlo значимость: сравнение с N симуляциями |

**Параметры реального Cold Spot:** $(l, b) = (209°, -57°)$, радиус $\sim 5°$, $\Delta T \sim -150$ мкК.

---

## Модуль 2: Сжатие Вселенной

### `archeon/compression/vae.py`

**Идея:** VAE (Variational Autoencoder) сжимает CMB-карты в вероятностное латентное пространство. В отличие от обычного autoencoder, VAE позволяет генерировать новые карты и интерполировать между космологиями.

| Класс/функция | Описание |
|---|---|
| `CosmologyVAE` | Encoder $\to$ ($\mu$, $\log\sigma^2$) $\to$ reparameterize $\to$ decoder |
| `vae_loss()` | $L = L_{recon} + \beta \cdot D_{KL}$ |
| `train_vae()` | Тренировочный цикл с beta-weighting |

**KL дивергенция:** $D_{KL} = -\frac{1}{2} \sum_j (1 + \log\sigma_j^2 - \mu_j^2 - \sigma_j^2)$ — регуляризирует латентное пространство к стандартному гауссиану.

**$\beta$-VAE:** $\beta > 1$ усиливает регуляризацию $\to$ более разделённое (disentangled) представление.

---

### `archeon/compression/disentanglement.py`

**Идея:** насколько хорошо каждое латентное измерение кодирует один физический параметр?

| Функция | Описание |
|---|---|
| `compute_mutual_info_gap()` | MIG: разница между двумя лучшими корреляциями для каждого параметра |
| `traversal_analysis()` | Варьировать одно измерение, фиксируя остальные — визуализация |
| `factor_correlation_matrix()` | Полная матрица корреляций latent vs физика |

**MIG (Mutual Information Gap):** высокий MIG = хорошее disentanglement (одно измерение доминирует для каждого параметра).

---

### `archeon/compression/interpretability.py`

**Идея:** физическая интерпретация — что каждое латентное измерение кодирует?

| Функция | Описание |
|---|---|
| `interpret_latent_space()` | Для каждого $z_i$ найти наиболее коррелированный параметр |
| `latent_space_summary()` | Человекочитаемый отчёт |
| `find_hidden_correlations()` | Поиск измерений, кодирующих КОМБИНАЦИИ параметров |

**Скрытые корреляции** — самый интересный результат: если $z_k$ кодирует $H_0 + \Omega_m$, это может указывать на физическую связь, не очевидную из уравнений.

---

## Терминология

| Термин | Определение |
|---|---|
| **Autoencoder** | Нейросеть, обучаемая реконструировать вход через узкое горлышко (bottleneck). Латентное представление = сжатие |
| **VAE** | Variational Autoencoder: кодирует в распределение, а не точку. Позволяет генерацию и интерполяцию |
| **Anomaly score** | Метрика аномальности. Для AE: ошибка реконструкции. Для latent: расстояние Махаланобиса |
| **Cold Spot** | Аномально холодная область CMB (~-150 мкК, 10°). Координаты: l=209°, b=-57° |
| **Non-Gaussianity** | Отклонение от гауссова распределения. Измеряется: skewness, kurtosis, $f_{NL}$ |
| **Kolmogorov-Smirnov test** | Сравнение двух распределений по максимальному расстоянию между CDF |
| **Anderson-Darling test** | Тест на принадлежность конкретному распределению (чувствительнее KS на хвостах) |
| **Cosmic variance** | Фундаментальная неопределённость: мы наблюдаем одну Вселенную. $\Delta C_\ell / C_\ell \sim \sqrt{2/(2\ell+1)}$ |
| **Monte Carlo significance** | P-value из прямого сравнения: доля симуляций с более экстремальным значением |
| **Connected components** | Алгоритм выделения связных регионов на изображении (scipy.ndimage.label) |
| **Mahalanobis distance** | Расстояние с учётом ковариации: более principled чем Евклидово |
| **KL divergence** | Мера различия между двумя распределениями. В VAE: разница между latent и стандартным Гауссом |
| **$\beta$-VAE** | VAE с $\beta > 1$ для KL — усиливает disentanglement за счёт качества реконструкции |
| **Reparameterization trick** | $z = \mu + \sigma \cdot \epsilon$, $\epsilon \sim \mathcal{N}(0,1)$ — делает сэмплирование дифференцируемым |
| **Disentanglement** | Свойство представления: каждое измерение кодирует один независимый фактор |
| **MIG** | Mutual Information Gap: метрика disentanglement. Разница корреляций топ-2 латентных измерений |
| **Traversal** | Движение вдоль одной оси latent space при фиксации остальных — визуализация «что кодирует» |
| **Hidden correlations** | Латентные измерения, кодирующие комбинации физических параметров |
| **t-SNE** | Нелинейное снижение размерности, сохраняющее локальную структуру |
| **UMAP** | Нелинейное снижение размерности, сохраняющее и локальную и глобальную структуру |
| **Radial profile** | Азимутально-усреднённая зависимость $T(r)$ вокруг точки |

---

## Результаты тестирования

### Новые тесты (34)

#### `test_anomaly.py` (18 тестов)
- **Autoencoder (4):** формы выходов, encode/decode roundtrip, anomaly scores, loss decreases
- **Latent Analysis (5):** extract latent, outlier detection, PCA dimensionality, 2D reduction, parameter correlation
- **Statistical Tests (7):** KS test same/different, Anderson-Darling, non-Gaussianity, chi-squared, MC significance (extreme + typical)
- **Cold Spot (4):** detect injected spot, no spots in uniform, radial profile, MC significance

#### `test_compression.py` (16 тестов)
- **VAE (6):** forward shapes, encode/decode, generate, loss positive, beta affects KL, training
- **Disentanglement (4):** MIG high for perfect, MIG low for random, traversal shape, correlation matrix
- **Interpretability (4):** all dims interpreted, strong correlation detected, summary string, hidden correlations

### Полный набор

```
171 passed, 9 warnings in 16.83s
```

---

## Архитектура

```
archeon/anomaly/
  autoencoder.py        CMBAutoencoder, anomaly scoring, training
  latent_analysis.py    outlier detection, PCA, t-SNE/UMAP, correlations
  statistical_tests.py  KS, Anderson-Darling, non-Gaussianity, chi2, MC
  cold_spot.py          Cold Spot detection, radial profiles, MC significance

archeon/compression/
  vae.py                CosmologyVAE, beta-VAE loss, training
  disentanglement.py    MIG, traversal, correlation matrix
  interpretability.py   physical interpretation, hidden correlations
```

---

## Следующие шаги (Фаза 6)

- `archeon/ml/emulator.py` — нейросетевой эмулятор $C_\ell$ спектра (замена CLASS)
- `archeon/ml/fno_structure.py` — Fourier Neural Operator для формирования структур
- `archeon/ml/pinn_friedmann.py` — Physics-Informed Neural Network для уравнений Фридмана
