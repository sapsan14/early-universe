import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { MathBlock } from "../ui/Math";

export function ChapterInflation() {
  const { pick } = useT();
  return (
    <>
      <p>
        {pick({
          ru: <>В начале 1980-х физик Алан Гут заметил кое-что странное. Если перемотать Вселенную к самым ранним моментам, обнаружатся две большие проблемы:</>,
          en: <>In the early 1980s physicist Alan Guth noticed something strange. If you wind the Universe back to its earliest moments, two big problems pop up:</>,
        })}
      </p>
      <ol>
        <li>
          <strong>{pick({ ru: "Проблема горизонта.", en: "The horizon problem." })}</strong>{" "}
          {pick({
            ru: <>Противоположные точки неба имеют практически одинаковую температуру (с точностью до 0,01%). Но они никогда не могли «обмениваться теплом» — свет за всё время существования Вселенной не успел бы пройти от одного конца до другого. Откуда взялась такая идеальная одинаковость?</>,
            en: <>Opposite sides of the sky have nearly identical temperatures (to within 0.01%). But they could never have "exchanged heat" — light couldn't have crossed from one to the other in the age of the Universe. Where did such perfect uniformity come from?</>,
          })}
        </li>
        <li>
          <strong>{pick({ ru: "Проблема плоскости.", en: "The flatness problem." })}</strong>{" "}
          {pick({
            ru: <>Геометрия Вселенной с поразительной точностью «евклидова» — ни выпуклая, ни вогнутая, а плоская. Но даже малейшее отклонение в начале выросло бы до огромного. Почему она так идеально настроена?</>,
            en: <>The geometry of the Universe is astonishingly "Euclidean" — neither curved up nor curved down, but flat. Yet even the slightest tilt early on would amplify into a huge one. Why so perfectly tuned?</>,
          })}
        </li>
      </ol>

      <Callout variant="story" title={p("Великое Растяжение", "The Great Stretch")}>
        {pick({
          ru: <>Идея Гута: между t ≈ 10⁻³⁶ и 10⁻³² секунды Вселенная пережила крошечный момент <em>экспоненциального</em> расширения. За это время каждый сантиметр пространства превратился в галактику. Любой искривлённый кусочек растягивается до плоского — как сморщенный полиэтиленовый пакет, который надули до размера футбольного поля.</>,
          en: <>Guth's idea: between t ≈ 10⁻³⁶ and 10⁻³² s the Universe underwent a tiny burst of <em>exponential</em> expansion. In that instant every centimetre became a galaxy. Any wrinkles get stretched flat — like a crumpled plastic bag inflated to the size of a football field.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Сколько именно?", en: "How much, exactly?" })}</h3>
      <MathBlock
        title={p("Закон инфляции", "The inflation law")}
        historyId="inflation"
        formula="a(t) = a_0 \, e^{H_{\text{inf}}\, t}"
        caption={p("Масштабный фактор a(t) растёт экспоненциально — гораздо быстрее, чем по любому степенному закону.", "The scale factor a(t) grows exponentially — much faster than any power law.")}
        legend={[
          { sym: "a(t)", meaning: p("во сколько раз больше Вселенная в момент t", "how much bigger the Universe is at time t") },
          { sym: "H_{\\text{inf}}", meaning: p("параметр Хаббла во время инфляции — гигантский", "Hubble parameter during inflation — enormous") },
          { sym: "e", meaning: p("число Эйлера ≈ 2.718, основа экспоненты", "Euler's number ≈ 2.718, base of exponentials") },
        ]}
        steps={[
          { eq: "\\Delta t \\approx 10^{-32}\\ \\text{с},\\ H_{\\text{inf}}\\Delta t \\approx 60", note: p("За такое короткое время — 60 «удвоений» Вселенной.", "In that brief instant — 60 cosmic doublings.") },
          { eq: "\\dfrac{a_{\\text{конец}}}{a_{\\text{начало}}} = e^{60}", note: p("Каждое удвоение умножает на e ≈ 2.7.", "Each doubling multiplies by e ≈ 2.7.") },
          { eq: "\\approx 10^{26}", note: p("Маковое зёрнышко становится размером с галактику.", "A poppy seed becomes the size of a galaxy.") },
        ]}
      />

      <Callout variant="wow">
        {pick({
          ru: <>Если бы атом водорода (≈10⁻¹⁰ м) внезапно вырос в e⁶⁰ раз, его размер достиг бы около 10¹⁶ метров — это размер Солнечной системы. И всё это — за время гораздо короче триллионной от триллионной от триллионной доли секунды.</>,
          en: <>If a hydrogen atom (≈10⁻¹⁰ m) suddenly grew by e⁶⁰, it would become 10¹⁶ m across — the size of the Solar System. And all of that takes a time far shorter than a trillionth of a trillionth of a trillionth of a second.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Зародыши галактик", en: "Galaxy seeds" })}</h3>
      <p>
        {pick({
          ru: <>В вакууме нет полной пустоты — он постоянно «дышит» <Term id="quantum-fluctuation">квантовыми флуктуациями</Term>. Во время инфляции эти крошечные дрожания растянулись до космических масштабов и навсегда «застыли». Потом, миллионы лет спустя, они стали первыми галактиками.</>,
          en: <>The vacuum isn't truly empty — it constantly breathes with <Term id="quantum-fluctuation">quantum fluctuations</Term>. During inflation these tiny jitters were stretched to cosmic scales and "frozen" forever. Millions of years later they grew into the first galaxies.</>,
        })}
      </p>

      <Callout variant="math" title={p("Спектр первичных флуктуаций", "Primordial fluctuation spectrum")}>
        <MathBlock
          historyId="primordial-spectrum"
          formula="P(k) = A_s \left( \dfrac{k}{k_\ast} \right)^{n_s - 1}"
          caption={p("Сколько «силы» в флуктуациях каждого пространственного масштаба k.", "How much power lives in fluctuations of each spatial scale k.")}
          legend={[
            { sym: "A_s", meaning: p("общая громкость квантового шёпота", "overall loudness of the quantum whisper") },
            { sym: "n_s", meaning: p("наклон спектра. n_s = 1 — все масштабы равноправны", "spectral tilt. n_s = 1 — every scale equal") },
            { sym: "k_\\ast", meaning: p("опорный масштаб (обычно 0.05 Mpc⁻¹)", "pivot scale (usually 0.05 Mpc⁻¹)") },
          ]}
        />
        <p style={{ marginTop: 8 }}>
          {pick({
            ru: <>Сегодня измерено: <strong>n_s ≈ 0.965</strong> — слегка меньше единицы, как и предсказывает большинство моделей инфляции. Маленькая «несимметричность» спектра — лучшее подтверждение того, что инфляция действительно была.</>,
            en: <>The measured value is <strong>n_s ≈ 0.965</strong> — slightly under unity, exactly as most inflation models predict. That tiny tilt is the best evidence we have that inflation actually happened.</>,
          })}
        </p>
      </Callout>

      <Callout variant="challenge" title={p("Эксперимент", "Experiment")}>
        {pick({
          ru: <>Открой <strong>Лабораторию → Шесть параметров</strong>. Подвинь ползунок n_s от 0.85 до 1.10. Спектр CMB наклоняется! При n_s &gt; 1 много мелких пятен, при n_s &lt; 1 — больше крупных. Это и есть «отпечаток инфляции».</>,
          en: <>Open the <strong>Lab → Six Parameters</strong>. Slide n_s from 0.85 to 1.10. The CMB spectrum tilts! At n_s &gt; 1 lots of small patches, at n_s &lt; 1 more big ones. That's the imprint of inflation.</>,
        })}
      </Callout>
    </>
  );
}
