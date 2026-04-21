import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { MathBlock } from "../ui/Math";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { theme } from "../../theme";

export function ChapterIngredients() {
  const { pick } = useT();
  return (
    <>
      <p>
        {pick({
          ru: <>Стандартная модель космологии называется <strong>ΛCDM</strong> (Лямбда + Cold Dark Matter, тёмная энергия плюс холодная тёмная материя). Она описывает Вселенную всего шестью свободными параметрами. Если задать их, можно с потрясающей точностью предсказать всё, что мы наблюдаем.</>,
          en: <>The standard model of cosmology is called <strong>ΛCDM</strong> (Lambda + Cold Dark Matter — dark energy plus cold dark matter). It describes the Universe with just six free parameters. Set them and you can predict, to astonishing accuracy, everything we observe.</>,
        })}
      </p>

      <Callout variant="story" title={p("Шесть рычагов", "Six levers")}>
        {pick({
          ru: <>Представь себе шесть ползунков. Каждый управляет одной важной чертой Вселенной: как быстро она расширяется, сколько в ней обычной и тёмной материи, как «громко» прозвучала инфляция, и сколько фотонов CMB переопрошлось при первых звёздах. Шесть чисел — и все 13,8 миллиардов лет в твоих руках.</>,
          en: <>Picture six sliders. Each controls one essential trait of the Universe: how fast it expands, how much ordinary and dark matter it contains, how "loud" inflation was, and how many CMB photons got rescattered when the first stars lit up. Six numbers — and 13.8 billion years are in your hands.</>,
        })}
      </Callout>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", margin: "20px 0 28px" }}>
        {[
          { id: "hubble", val: "67.36", what: pick({ ru: "Скорость расширения сегодня", en: "Today's expansion rate" }) },
          { id: "omega-b-h2", val: "0.0224", what: pick({ ru: "Сколько обычного вещества", en: "Amount of ordinary matter" }) },
          { id: "omega-cdm-h2", val: "0.120", what: pick({ ru: "Сколько тёмной материи", en: "Amount of dark matter" }) },
          { id: "n-s", val: "0.965", what: pick({ ru: "Наклон спектра инфляции", en: "Tilt of the inflation spectrum" }) },
          { id: "a-s", val: "ln10A_s = 3.044", what: pick({ ru: "Громкость инфляционного шёпота", en: "Loudness of the inflation whisper" }) },
          { id: "tau", val: "0.054", what: pick({ ru: "Когда зажглись первые звёзды", en: "When the first stars ignited" }) },
        ].map((row) => (
          <Card key={row.id} padding={16} tone="plasma">
            <Badge tone="starlight"><Term id={row.id} /></Badge>
            <div style={{ fontFamily: theme.font.mono, fontSize: 22, color: theme.color.starlight, marginTop: 10 }}>{row.val}</div>
            <div style={{ color: theme.color.inkSoft, fontSize: 13, marginTop: 4 }}>{row.what}</div>
          </Card>
        ))}
      </div>

      <h3>{pick({ ru: "Главное уравнение", en: "The master equation" })}</h3>
      <p>
        {pick({
          ru: <>Все эти числа подставляются в <Term id="friedmann">уравнение Фридмана</Term>. Это космологический «двигатель». Запиши его — и можно посчитать, как Вселенная расширялась в любую эпоху.</>,
          en: <>All those numbers feed into the <Term id="friedmann">Friedmann equation</Term>. It's cosmology's engine. Write it down and you can compute how the Universe expanded at any epoch.</>,
        })}
      </p>

      <MathBlock
        title={p("Уравнение Фридмана", "Friedmann equation")}
        formula="H² = (8πG/3) · (ρ_r + ρ_m + ρ_Λ)"
        caption={p("Скорость расширения H зависит от плотностей излучения, материи и тёмной энергии.", "The expansion rate H depends on the densities of radiation, matter and dark energy.")}
        legend={[
          { sym: "H", meaning: p("параметр Хаббла — скорость расширения", "Hubble parameter — expansion rate") },
          { sym: "G", meaning: p("гравитационная постоянная Ньютона", "Newton's gravitational constant") },
          { sym: "ρ_r", meaning: p("плотность энергии излучения", "energy density of radiation") },
          { sym: "ρ_m", meaning: p("плотность энергии материи (барионы + тёмная)", "energy density of matter (baryons + dark)") },
          { sym: "ρ_Λ", meaning: p("плотность тёмной энергии", "energy density of dark energy") },
        ]}
        steps={[
          { eq: "ρ_r ∝ a⁻⁴", note: p("Излучение разреживается быстрее всех — расширение растягивает длину волны.", "Radiation dilutes fastest — expansion also stretches wavelengths.") },
          { eq: "ρ_m ∝ a⁻³", note: p("Материя — пропорционально объёму.", "Matter — inversely with volume.") },
          { eq: "ρ_Λ = const", note: p("Тёмная энергия не разреживается. Поэтому она «выигрывает» поздно.", "Dark energy doesn't dilute. That's why it wins out late.") },
        ]}
      />

      <Callout variant="wow">
        {pick({
          ru: <>Сравнивая, какая компонента в данный момент доминирует, можно «нарисовать» всю историю Вселенной:<br />— излучение (до z ≈ 3400),<br />— материя (3400 &gt; z &gt; 0.7),<br />— тёмная энергия (z &lt; 0.7).</>,
          en: <>By tracking which component dominates when, you can sketch the Universe's whole biography:<br />— radiation (until z ≈ 3400),<br />— matter (3400 &gt; z &gt; 0.7),<br />— dark energy (z &lt; 0.7).</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Загадка H₀", en: "The H₀ mystery" })}</h3>
      <p>
        {pick({
          ru: <>В современной космологии есть <em>тенсия</em>: разные методы дают чуть разные значения H₀.<br />— Planck (по CMB): 67.36 ± 0.5 км/с/Мпк.<br />— Прямые измерения по сверхновым (Hubble Space Telescope): 73 ± 1 км/с/Мпк.<br />Разница в 5–6 километров в секунду — небольшая, но статистически значимая. Это либо ошибка в измерениях, либо <strong>намёк на новую физику</strong>. Ставки сейчас сделаны.</>,
          en: <>Modern cosmology has a <em>tension</em>: different methods give slightly different H₀ values.<br />— Planck (from the CMB): 67.36 ± 0.5 km/s/Mpc.<br />— Direct supernova measurements (Hubble Space Telescope): 73 ± 1 km/s/Mpc.<br />A difference of 5–6 km/s — small, but statistically significant. Either there's a measurement bug, or it's a <strong>hint of new physics</strong>. The bets are on.</>,
        })}
      </p>

      <Callout variant="challenge">
        {pick({
          ru: <>В лаборатории <strong>«Шесть параметров»</strong> подвинь H₀ к 73 км/с/Мпк. Заметь, как смещается первый акустический пик. Изменения малы — именно поэтому ловить тенсию H₀ так трудно.</>,
          en: <>In the <strong>Six Parameters</strong> lab, slide H₀ up to 73 km/s/Mpc. Note how the first acoustic peak shifts. The changes are subtle — that's why detecting the H₀ tension is so hard.</>,
        })}
      </Callout>
    </>
  );
}
