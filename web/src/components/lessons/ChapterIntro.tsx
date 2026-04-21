import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { MathBlock } from "../ui/Math";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { theme } from "../../theme";

export function ChapterIntro() {
  const { pick } = useT();
  return (
    <>
      <p>
        {pick({
          ru: <>Космология — это наука, которая задаёт самые большие вопросы во Вселенной: <em>откуда всё взялось</em>, <em>из чего сделано</em> и <em>куда мы летим</em>. Звучит как философия, но на самом деле — это настоящая физика, и почти всё в ней можно проверить телескопом.</>,
          en: <>Cosmology asks the biggest possible questions: <em>where did all this come from</em>, <em>what is it made of</em>, and <em>where is it heading</em>. It sounds like philosophy, but it's actually physics — and almost everything in it can be checked with a telescope.</>,
        })}
      </p>
      <p>
        {pick({
          ru: <>Если астрономия изучает отдельные объекты — звёзды, планеты, кометы — то космология изучает Вселенную как целое. Один большой пациент, и нам нужно поставить ему диагноз.</>,
          en: <>If astronomy studies individual objects — stars, planets, comets — cosmology studies the Universe as a whole. One enormous patient, and we have to make a diagnosis.</>,
        })}
      </p>

      <Callout variant="story" title={p("Очень короткая история", "A very short story")}>
        {pick({
          ru: <>13,8 миллиарда лет назад Вселенная была горячей и плотной. Она быстро расширилась (это и есть «<Term id="big-bang" />»), остыла, и в первые три минуты сварила водород и гелий. Через 380 000 лет освободился свет — мы до сих пор его видим как <Term id="cmb" />. Через сотни миллионов лет загорелись первые звёзды, потом появились галактики, скопления, планеты — и однажды кто-то на одной из этих планет задал вопрос: «А почему?»</>,
          en: <>13.8 billion years ago the Universe was hot and dense. It expanded rapidly (the "<Term id="big-bang" />"), cooled down, and in three minutes cooked up hydrogen and helium. After 380 000 years light broke free — we still see it as the <Term id="cmb" />. Hundreds of millions of years later the first stars lit up, then galaxies, then clusters and planets — and one day, someone on one of those planets asked: "Why?"</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Шесть чисел вместо целого учебника", en: "Six numbers instead of a whole textbook" })}</h3>
      <p>
        {pick({
          ru: <>Удивительно, но всю наблюдаемую Вселенную можно описать всего шестью числами. Их измерили космические телескопы Planck, WMAP и COBE. Вот они:</>,
          en: <>Astonishingly, the entire observable Universe can be described by just six numbers. They were measured by the Planck, WMAP and COBE satellites. Here they are:</>,
        })}
      </p>

      <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", margin: "16px 0 24px" }}>
        {[
          { id: "hubble", val: "67.36", unit: "km/s/Mpc" },
          { id: "omega-b-h2", val: "0.0224" },
          { id: "omega-cdm-h2", val: "0.120" },
          { id: "n-s", val: "0.965" },
          { id: "a-s", val: "ln(10¹⁰A_s) = 3.044" },
          { id: "tau", val: "0.054" },
        ].map((row) => (
          <Card key={row.id} padding={16} tone="plasma">
            <Badge tone="starlight"><Term id={row.id} /></Badge>
            <div style={{ fontFamily: theme.font.mono, fontSize: 22, color: theme.color.starlight, marginTop: 10 }}>
              {row.val}{row.unit ? ` ${row.unit}` : ""}
            </div>
          </Card>
        ))}
      </div>

      <Callout variant="wow">
        {pick({
          ru: <>Если изменить хотя бы одно число даже на пару процентов, то либо никогда не появятся звёзды, либо вся материя сожмётся обратно за миллион лет. Мы живём в очень тонко настроенной Вселенной — и это одна из главных загадок современной физики.</>,
          en: <>Change any of these numbers by even a few percent and either no stars ever ignite or all matter collapses back in a million years. We live in a finely tuned Universe — one of the deepest mysteries of modern physics.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Что мы можем измерить", en: "What we can measure" })}</h3>
      <p>
        {pick({
          ru: <>У космолога есть три «органа чувств»: свет, гравитация и частицы (нейтрино, космические лучи). Самый честный — свет. Он несёт записанную в нём температуру, состав, скорость удаления источника.</>,
          en: <>A cosmologist has three "senses": light, gravity, and particles (neutrinos, cosmic rays). The most honest one is light: it carries an imprint of temperature, composition, and recession speed.</>,
        })}
      </p>

      <MathBlock
        title={p("Закон Хаббла", "Hubble's law")}
        historyId="hubble-law"
        formula="v = H \cdot d"
        caption={p("Скорость удаления галактики пропорциональна её расстоянию.", "A galaxy's recession speed is proportional to its distance.")}
        legend={[
          { sym: "v", meaning: p("скорость, с которой галактика «убегает» от нас", "the galaxy's recession velocity") },
          { sym: "H", meaning: p("параметр Хаббла — насколько быстро расширяется Вселенная", "the Hubble parameter — how fast the Universe is expanding") },
          { sym: "d", meaning: p("расстояние до галактики", "distance to the galaxy") },
        ]}
      />

      <Callout variant="tip">
        {pick({
          ru: <>Подумай: если каждая дальняя галактика убегает быстрее, значит, Вселенная не имеет «центра». Все наблюдатели где угодно увидят то же самое. Это и есть <em>космологический принцип</em>.</>,
          en: <>Think: if every distant galaxy recedes faster the farther it is, then the Universe has no "centre". Every observer anywhere sees the same picture. That's the <em>cosmological principle</em>.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Чему ты научишься", en: "What you'll learn" })}</h3>
      <ul>
        <li>{pick({ ru: "Считать возраст Вселенной по красному смещению", en: "Compute the Universe's age from a redshift" })}</li>
        <li>{pick({ ru: "Различать барионную и тёмную материю", en: "Tell baryonic from dark matter" })}</li>
        <li>{pick({ ru: "Читать «небесный нотный лист» — спектр CMB", en: "Read the CMB power spectrum" })}</li>
        <li>{pick({ ru: "Запускать собственные мини-симуляции и охотиться на аномалии", en: "Run your own mini-simulations and hunt for anomalies" })}</li>
      </ul>

      <Callout variant="challenge" title={p("Задание главы 1", "Chapter 1 challenge")}>
        {pick({
          ru: <>Открой <strong>Лабораторию → Машина времени</strong> и поставь слайдер на «Now». Сравни числа температуры и параметра Хаббла с тем, что ты только что прочитал. Сходится?</>,
          en: <>Open the <strong>Lab → Time Machine</strong> and slide to "Now". Compare the temperature and Hubble parameter to what you just read. Do they match?</>,
        })}
      </Callout>
    </>
  );
}
