# Фаза 7: Интерактивная Обсерватория (API + WebGPU)

## Обзор

Фаза 7 создаёт полный стек «бэкенд + фронтенд» для взаимодействия с ARCHEON:

| Слой | Технология | Назначение |
|------|------------|------------|
| Backend API | FastAPI + Pydantic | REST-эндпоинты для всех вычислений |
| Frontend | React + TypeScript + Vite | 4 интерактивных компонента |
| GPU Engine | WebGPU WGSL | Compute shaders для рендеринга частиц |

---

## Часть 1: FastAPI Backend

### Архитектура

```
FastAPI App (service.py)
├── /health                          → статус сервиса
├── /api/v1/spectrum                 → эмуляция C_l спектра
├── /api/v1/inference                → вывод параметров из CMB-карты
├── /api/v1/anomalies                → детекция аномалий
├── /api/v1/explorer                 → Parameter Explorer
└── simulations/ (router)
    ├── /api/v1/simulations/timeline → Cosmic Time Machine
    └── /api/v1/simulations/playable → Playable Universe
```

### Эндпоинты

#### POST `/api/v1/spectrum`

Предсказание углового спектра мощности C_l из 6 космологических параметров через нейросетевой эмулятор.

| Поле | Тип | Описание |
|------|-----|----------|
| `params` | `CosmoParams` | 6 параметров ΛCDM |
| `l_max` | int | Максимальный мультиполь (2–5000) |

**Ответ**: `{ ell: [2, 3, ...], cl: [...], inference_time_ms: 0.8 }`

#### POST `/api/v1/inference`

Вывод космологических параметров из 2D CMB-карты.

| Метод | Описание |
|-------|----------|
| `cnn` | Один прямой проход BayesianCosmologyCNN → μ, σ |
| `ensemble` | MC Dropout: N стохастических проходов → среднее + неопределённость |

**Ответ**: список `ParameterEstimate` с name, value, uncertainty, 68%-интервал.

#### POST `/api/v1/anomalies`

Детекция аномалий в CMB-карте.

1. Автоэнкодер вычисляет ошибку реконструкции
2. Пиксели выше threshold_sigma × std маскируются
3. Связные компоненты = кандидаты-аномалии
4. `check_non_gaussianity` оценивает скошенность и эксцесс

**Ответ**: `global_score`, список кандидатов, тесты на негауссовость.

#### POST `/api/v1/simulations/timeline`

Cosmic Time Machine: физическое состояние Вселенной в заданный момент.

- Вход: `log_time_seconds` (от −43 до 17.64)
- База: 10 ключевых космологических эпох от Планковской до современной
- Для каждой эпохи: температура, красное смещение, масштабный фактор, H(a), доминирующая компонента, описание, ключевые процессы

#### POST `/api/v1/simulations/playable`

Playable Universe: sandbox-симуляция формирования структур.

- Вход: модифицированные космологические параметры + размер сетки
- Процесс:
  1. Генерация начального Гауссова поля с P(k) ∝ k^(n_s−1)
  2. Эволюция через линейный growth factor (Carroll+ 1992)
  3. Лог-нормальная нелинейная аппроксимация
  4. N снимков от z=1100 до z≈0
- Выход: массив снимков, красные смещения, спектры мощности, флаг structure_formed

#### POST `/api/v1/explorer`

Parameter Explorer: мгновенный пересчёт C_l при изменении слайдеров.

- Использует тот же эмулятор что и `/spectrum`
- Опционально возвращает поле плотности

### Pydantic-схемы (`models.py`)

| Модель | Описание |
|--------|----------|
| `CosmoParams` | 6 параметров ΛCDM с валидацией диапазонов |
| `InferenceRequest/Response` | Запрос/ответ для вывода параметров |
| `SpectrumRequest/Response` | Запрос/ответ для C_l |
| `AnomalyRequest/Response` | Запрос/ответ для аномалий |
| `TimelineRequest/Response` | Запрос/ответ для Time Machine |
| `PlayableRequest/Response` | Запрос/ответ для sandbox |
| `CosmicEpoch` | Описание космологической эпохи |
| `ParameterEstimate` | Оценка одного параметра с неопределённостью |

### Ленивая загрузка моделей (`AppState`)

Нейросетевые модели (эмулятор, CNN, автоэнкодер) загружаются по первому запросу, а не при старте сервера — это ускоряет запуск и экономит RAM.

---

## Часть 2: Frontend (React + TypeScript)

### Стек технологий

| Инструмент | Версия | Назначение |
|------------|--------|------------|
| React | 19 | UI-фреймворк |
| TypeScript | 5.6 | Типизация |
| Vite | 6 | Сборщик с HMR |

### Компоненты

#### 1. TimeTraveler

**Машина времени Вселенной.**

- Слайдер от 10⁻⁴³ секунд до 13.8 млрд лет
- Быстрые метки эпох (Planck, Inflation, QCD, BBN, CMB, Dawn, Now)
- Карточки с: z, T, a, H, доминирующей компонентой
- Debounced-запросы к API (200 мс)

#### 2. ParameterExplorer

**Исследователь параметров с мгновенным пересчётом.**

- 6 слайдеров для H₀, Ω_b h², Ω_cdm h², n_s, ln(10¹⁰A_s), τ_reio
- Canvas-график D_l = l(l+1)C_l / 2π в лог-лог шкале
- Время инференса в мс (отображается пользователю)
- Кнопка "Reset to Planck 2018"

#### 3. PlayableUniverse

**Управляемая Вселенная — sandbox.**

- 4 ключевых слайдера (H₀, n_s, ln10As, Ω_cdm h²)
- Кнопка "Create Universe" → серия снимков поля плотности
- Анимация (Play/Pause) через покадровое отображение
- Слайдер покадрового скроллинга с отображением z и a
- Индикатор: "Structure formed" / "No structure"
- Canvas с colormap (синий → белый → красный)

#### 4. AnomalyMap

**Интерактивная карта аномалий CMB.**

- Клиентская генерация синтетических CMB-карт (для оффлайн-демо)
- Canvas-визуализация с CMB-стилем colormap
- Красные кружки вокруг обнаруженных аномалий
- Панель: global score, число аномалий, skewness, kurtosis, p-values
- Индикатор гауссовости / негауссовости

### API-клиент (`api/client.ts`)

Типизированные функции для взаимодействия с бэкендом:
- `post<T>(path, body)` — generic POST-запрос
- TypeScript-интерфейсы для всех ответов API
- `DEFAULT_PARAMS` — значения Planck 2018

---

## Часть 3: WebGPU Particle Engine

### Архитектура

```
WebGPU Pipeline
├── Compute Shader (WGSL)
│   ├── N-body gravity (субвыборка: Barnes-Hut approximation)
│   ├── Hubble expansion: v += H·r·dt
│   ├── Leapfrog integration: pos += vel·dt
│   └── Periodic boundary conditions
└── Render Shader (WGSL)
    ├── Point sprites
    ├── MVP-матрица с вращением
    └── Color by velocity: blue → white → red
```

### Compute Shader

Каждый поток (workgroup size = 64) обновляет одну частицу:

1. **Gravity**: суммирует гравитационное притяжение от подвыборки частиц (stride = N/256) с softening
2. **Hubble drag**: acc -= H · pos (расширение пространства)
3. **Velocity update**: vel += acc · dt, затем damping
4. **Position update**: pos += vel · dt
5. **Periodic wrap**: частицы, покинувшие box, появляются с другой стороны

### Данные частицы (struct Particle)

| Поле | Тип | Описание |
|------|-----|----------|
| `pos.xyz` | vec3f | Позиция в box |
| `pos.w` | f32 | Масса |
| `vel.xyz` | vec3f | Скорость |
| `vel.w` | f32 | Padding |

### Параметры симуляции (SimParams)

| Параметр | Default | Описание |
|----------|---------|----------|
| `dt` | 0.02 | Шаг интегрирования |
| `gravity` | 0.001 | Гравитационная постоянная |
| `hubble` | 0.0 | Параметр расширения |
| `damping` | 0.999 | Затухание скорости (для стабильности) |
| `softening` | 0.1 | Минимальное расстояние (предотвращает сингулярность) |
| `box_size` | 10.0 | Размер периодической области |

### Утилиты

- `initParticles(n, boxSize)` — инициализация равномерно-случайных позиций
- `createMVP(time, aspect, distance)` — perspective + rotation матрица

---

## Космологические эпохи (база знаний Cosmic Time Machine)

| # | Эпоха | log₁₀(t/s) | Ключевые процессы |
|---|-------|-----------|-------------------|
| 1 | Планковская | −43.5 ... −36 | Квантовая гравитация, великое объединение |
| 2 | Инфляция | −36 ... −32 | Экспоненциальное расширение, генерация флуктуаций |
| 3 | Кварковая / Reheating | −32 ... −10 | Бариогенез, кварк-глюонная плазма |
| 4 | QCD-переход | −10 ... −4 | Конфайнмент кварков, протоны и нейтроны |
| 5 | BBN | −4 ... 3 | Синтез H, He-4, D, Li-7 |
| 6 | Равенство материи-излучения | 3 ... 11 | Начало роста структур |
| 7 | Рекомбинация / CMB | 11 ... 13 | Нейтральный водород, свободные фотоны = CMB |
| 8 | Тёмные века | 13 ... 15.5 | Нет источников света, рост гало |
| 9 | Cosmic Dawn | 15.5 ... 16.3 | Первые звёзды, реионизация |
| 10 | Галактики / Современность | 16.3 ... 17.64 | Филаменты, войды, ускоренное расширение |

---

## Результаты валидации

### Тесты

| Группа | Тестов | Статус |
|--------|--------|--------|
| TestHealth | 1 | ✅ |
| TestSpectrum | 3 | ✅ |
| TestInference | 4 | ✅ |
| TestAnomalies | 2 | ✅ |
| TestTimeline | 4 | ✅ |
| TestPlayable | 2 | ✅ |
| TestExplorer | 2 | ✅ |
| TestModels | 4 | ✅ |
| TestSimulationsUnit | 3 | ✅ |
| **Итого Фаза 7** | **25** | **✅** |
| **Весь проект** | **235** | **✅** |

### Что проверяют тесты

- **Health check**: сервис отвечает 200
- **Spectrum**: корректные C_l > 0, валидация диапазонов Pydantic
- **Inference**: CNN и MC Dropout оба возвращают параметры с неопределённостями; ресайз не-64×64 карт; ошибка 400 для неизвестного метода
- **Anomalies**: global score и non-gaussianity; порог влияет на число кандидатов
- **Timeline**: правильные эпохи (BBN, Inflation); T(early) > T(late)
- **Playable**: воспроизводимость при одном seed; корректные размерности
- **Explorer**: C_l возвращается; density field по запросу
- **Models**: валидация диапазонов, defaults
- **Simulations unit**: find_epoch, compute_state (физическая согласованность)

---

## Структура файлов

```
archeon/api/
├── __init__.py
├── models.py           ← Pydantic-схемы (15 моделей)
├── service.py          ← FastAPI app + 6 эндпоинтов
├── simulations.py      ← Router: Timeline + Playable Universe
└── routes/
    └── __init__.py

web/
├── package.json        ← React 19, Vite 6, TypeScript 5.6
├── tsconfig.json
├── vite.config.ts      ← proxy /api → localhost:8000
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx          ← Tab-навигация (4 режима)
    ├── api/
    │   └── client.ts   ← Типизированный HTTP-клиент
    ├── components/
    │   ├── TimeTraveler.tsx
    │   ├── ParameterExplorer.tsx
    │   ├── PlayableUniverse.tsx
    │   └── AnomalyMap.tsx
    └── engine/
        └── particles.ts ← WGSL compute/render shaders + утилиты

tests/
└── test_api.py         ← 25 тестов
```

---

## Запуск

```bash
# Backend
cd /home/anton/projects/early-universe
uvicorn archeon.api.service:app --reload --port 8000

# Frontend (отдельный терминал)
cd web
npm install
npm run dev
# → http://localhost:5173
```

Vite проксирует `/api/*` запросы на бэкенд (порт 8000).

---

## Глоссарий

| Термин | Определение |
|--------|-------------|
| **FastAPI** | Высокопроизводительный Python web-фреймворк с автогенерацией OpenAPI-документации |
| **Pydantic** | Библиотека валидации данных через Python type hints. Обеспечивает проверку типов и диапазонов на входе API |
| **CORS** | Cross-Origin Resource Sharing — механизм, позволяющий фронтенду на другом порту обращаться к API |
| **WebGPU** | Современный GPU API для веба (замена WebGL). Поддерживает compute shaders |
| **WGSL** | WebGPU Shading Language — язык шейдеров WebGPU |
| **Compute Shader** | GPU-программа для произвольных вычислений (не только рендеринг). Каждый тред обрабатывает одну частицу |
| **Softening** | Параметр ε в гравитационной формуле: F ∝ 1/(r² + ε²). Предотвращает бесконечную силу при r→0 |
| **Periodic Boundary** | Частицы, покидающие область, появляются с противоположной стороны. Имитирует бесконечную Вселенную |
| **Point Sprite** | Техника рендеринга: каждая вершина = один пиксель/точка. Эффективно для миллионов частиц |
| **Debounce** | Задержка перед отправкой запроса при изменении слайдера. Предотвращает перегрузку API |
| **Growth Factor D(a)** | Функция, описывающая рост возмущений плотности. D ∝ a в материальной эпохе |
| **Lognormal Transform** | δ_final = exp(G·δ_init) - 1. Простейшая модель нелинейной эволюции поля плотности |

---

## Ограничения и будущие улучшения

1. **WebGPU Engine**: шейдеры написаны, но нет React-компонента-обёртки для инициализации WebGPU-контекста. Необходим `useWebGPU` хук
2. **Playable Universe**: использует лог-нормальную аппроксимацию, а не реальное N-body. Для продакшена нужен JAX-бэкенд
3. **Anomaly Map**: оффлайн-демо с простым PRNG. Для реальных карт нужен HEALPix-рендерер
4. **Authentication**: отсутствует. Для публичного деплоя нужен rate limiting и API key
5. **State Management**: React state без Redux/Zustand. При усложнении UI потребуется централизованное хранилище

---

## Следующий шаг

→ **Фаза 8**: Альтернативные Космологии — f(R) гравитация, вариация констант, циклические модели.
