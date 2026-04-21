import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { MathBlock } from "../ui/Math";

export function ChapterBigBang() {
  const { pick } = useT();
  return (
    <>
      <p>
        {pick({
          ru: <>Слово «<Term id="big-bang" />» придумал в 1949 году астроном Фред Хойл — и придумал, чтобы посмеяться. Он не верил в идею расширения и иронично сказал по радио BBC: «Что, ваша вселенная началась с большого взрыва?». Название прилипло.</>,
          en: <>The phrase "<Term id="big-bang" />" was coined in 1949 by astronomer Fred Hoyle — as a joke. He didn't believe in expansion and quipped on BBC radio: "What, your universe started with a big bang?" The name stuck.</>,
        })}
      </p>
      <p>
        {pick({
          ru: <>Но Большой Взрыв — это не взрыв в пустоте. Это начало расширения самого пространства из <strong>безумно горячего и плотного состояния</strong>. Если перемотать сегодняшнюю Вселенную назад во времени, вся материя сожмётся, температура подскочит до триллионов градусов, и в какой-то момент наша физика просто перестанет работать.</>,
          en: <>But the Big Bang isn't an explosion in empty space. It's the beginning of the expansion of space itself out of an <strong>insanely hot, dense state</strong>. Rewind today's Universe and matter compresses, temperature rises into the trillions, and at some point our physics simply stops working.</>,
        })}
      </p>

      <Callout variant="story" title={p("Балон с конфетти", "A balloon of confetti")}>
        {pick({
          ru: <>Представь воздушный шарик, на котором нарисованы конфетти. Когда ты его надуваешь, каждая «конфетинка» удаляется от другой. Никто не движется по поверхности — это сама поверхность растёт. Так и Вселенная: галактики стоят на месте, а пространство между ними растягивается.</>,
          en: <>Picture a balloon with confetti drawn on it. As you inflate it, every dot moves away from every other dot — but no dot is moving along the surface. The surface itself grows. The Universe is the same: galaxies sit still while the space between them stretches.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Самая первая секунда", en: "The very first second" })}</h3>
      <p>
        {pick({
          ru: <>Самое раннее время, о котором мы можем говорить, называется <Term id="planck-time">Планковским временем</Term>. Оно равно <strong>5,39 × 10⁻⁴⁴ секунды</strong>. Это не «начало», а самый первый момент, до которого наша математика держит крышу. Ниже этого порога нужно квантовая теория гравитации, которой у нас пока нет.</>,
          en: <>The earliest moment we can talk about is the <Term id="planck-time">Planck time</Term>: <strong>5.39 × 10⁻⁴⁴ seconds</strong>. It's not "the start" but the earliest moment our math still holds its roof. Below it, we'd need a quantum theory of gravity — and we don't have one yet.</>,
        })}
      </p>

      <MathBlock
        title={p("Планковское время", "Planck time")}
        historyId="planck-time"
        formula="t_P = \sqrt{\dfrac{\hbar\, G}{c^5}}"
        caption={p("Это единственная комбинация трёх «коренных» постоянных природы, имеющая размерность времени.", "It's the only combination of nature's three master constants that has the dimension of time.")}
        legend={[
          { sym: "\\hbar", meaning: p("приведённая постоянная Планка — масштаб квантовой механики", "reduced Planck's constant — the scale of quantum mechanics") },
          { sym: "G", meaning: p("гравитационная постоянная — сила гравитации", "Newton's constant — the strength of gravity") },
          { sym: "c", meaning: p("скорость света в вакууме", "speed of light in vacuum") },
        ]}
        steps={[
          { eq: "\\hbar \\approx 1.055 \\times 10^{-34}\\ \\text{Дж}\\cdot\\text{с}", note: p("Подставляем приведённую постоянную Планка.", "Plug in the reduced Planck constant.") },
          { eq: "G \\approx 6.674 \\times 10^{-11}\\ \\text{м}^3/(\\text{кг}\\cdot\\text{с}^2)", note: p("Подставляем гравитационную постоянную.", "Plug in Newton's gravitational constant.") },
          { eq: "c \\approx 3 \\times 10^{8}\\ \\text{м/с}", note: p("Скорость света — 300 000 км/с.", "Speed of light — 300 000 km/s.") },
          { eq: "t_P \\approx 5.39 \\times 10^{-44}\\ \\text{с}", note: p("Получаем минимальный «тик» Вселенной.", "Out comes the Universe's smallest tick.") },
        ]}
      />

      <Callout variant="wow">
        {pick({
          ru: <>Если бы возраст Вселенной (13,8 миллиарда лет) сократить до одной секунды, то Планковское время равнялось бы… 10⁻⁶¹ секунды. Это в миллион миллиардов миллиардов миллиардов миллиардов миллиардов раз меньше нашей секунды. Цифры космологии действительно странные.</>,
          en: <>If you compressed the Universe's 13.8 Gyr life into a single second, the Planck time would be 10⁻⁶¹ s — a million billion billion billion billion billion times smaller than our second. The numbers of cosmology really are unhinged.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Четыре силы — одна сила", en: "Four forces, one force" })}</h3>
      <p>
        {pick({
          ru: <>Сегодня в природе четыре фундаментальные силы: <strong>гравитация, электромагнитизм, слабое и сильное ядерные взаимодействия</strong>. В первые мгновения они были одной силой. По мере остывания Вселенной они «отщеплялись» одна за другой — это называется нарушением симметрии.</>,
          en: <>Today nature has four forces: <strong>gravity, electromagnetism, the weak and strong nuclear forces</strong>. In the first moments they were one. As the Universe cooled, they peeled off one by one — a process called symmetry breaking.</>,
        })}
      </p>

      <Callout variant="math" title={p("Связь температуры и времени", "Linking temperature to time")}>
        <p>
          {pick({
            ru: <>На очень ранней Вселенной (когда доминирует излучение) есть простая формула:</>,
            en: <>In the very early radiation-dominated Universe there's a simple formula:</>,
          })}
        </p>
        <MathBlock
          formula="T\ [\text{МэВ}] \approx \dfrac{1}{\sqrt{t/\text{с}}}"
          caption={p("Очень грубая оценка: возьми время в секундах, извлеки корень и переверни — получишь температуру в мегаэлектронвольтах.", "Very rough rule of thumb: take time in seconds, square-root and invert to get temperature in megaelectronvolts.")}
        />
        <p style={{ marginTop: 8 }}>
          {pick({
            ru: <>При t = 1 секунда — около 1 МэВ (гамма-лучи). При t = 10⁻¹⁰ секунды — 100 ГэВ (как в Большом адронном коллайдере).</>,
            en: <>At t = 1 s temperature is around 1 MeV (gamma rays). At t = 10⁻¹⁰ s — about 100 GeV (Large Hadron Collider energies).</>,
          })}
        </p>
      </Callout>

      <Callout variant="challenge" title={p("Задание", "Challenge")}>
        {pick({
          ru: <>Открой <strong>Машину времени</strong> и поставь слайдер на «Planck». Какая там температура? Запиши число — мы вернёмся к нему через две главы.</>,
          en: <>Open the <strong>Time Machine</strong> and slide to "Planck". What's the temperature there? Note it — we'll come back to that number two chapters from now.</>,
        })}
      </Callout>
    </>
  );
}
