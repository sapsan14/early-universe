import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { MathBlock } from "../ui/Math";

export function ChapterCMB() {
  const { pick } = useT();
  return (
    <>
      <p>
        {pick({
          ru: <>Долгое время после Большого Взрыва Вселенная была непрозрачной — как туман. Свет существовал, но он постоянно сталкивался со свободными электронами и не мог далеко улететь. И вдруг, через 380 000 лет, всё изменилось.</>,
          en: <>For a long time after the Big Bang the Universe was opaque — like fog. Light existed, but it kept bouncing off free electrons and couldn't travel far. Then, 380 000 years in, everything changed.</>,
        })}
      </p>

      <Callout variant="story" title={p("Туман рассеялся", "The fog cleared")}>
        {pick({
          ru: <>Температура опустилась до 3000 K — впервые электроны смогли удержаться в составе атома водорода. Этот процесс называется <Term id="recombination">рекомбинацией</Term>. И в один миг Вселенная стала прозрачной: фотоны, которым некуда было лететь, помчались во все стороны. Этот «выпущенный на свободу» свет мы наблюдаем до сих пор. Это и есть <Term id="cmb">реликтовое излучение</Term>.</>,
          en: <>The temperature dropped to 3000 K — and for the first time electrons could be held inside hydrogen atoms. The process is called <Term id="recombination">recombination</Term>. In an instant the Universe became transparent: photons that had nowhere to go suddenly flew off in every direction. That "freed" light is what we still observe today: the <Term id="cmb">cosmic microwave background</Term>.</>,
        })}
      </Callout>

      <p>
        {pick({
          ru: <>За 13,8 миллиардов лет пути этот свет растянулся, и его длина волны увеличилась примерно в 1100 раз — превратившись из видимого красного в микроволны. Сегодня мы видим CMB при температуре 2,725 K — это всего на 3 градуса выше абсолютного нуля.</>,
          en: <>Over its 13.8-billion-year journey this light stretched, growing in wavelength by roughly a factor of 1100 — from visible red into microwaves. Today we see the CMB at 2.725 K — barely 3 degrees above absolute zero.</>,
        })}
      </p>

      <h3>{pick({ ru: "Карта неба", en: "The sky map" })}</h3>
      <p>
        {pick({
          ru: <>Если посмотреть на CMB достаточно внимательно, обнаружится, что он не идеально однородный. На некоторых пятнышках температура чуть выше, на других — чуть ниже. Эти пятна — крошечные, всего ±10⁻⁵ от средней температуры. Но именно они — гравитационные «зародыши», из которых выросли все галактики.</>,
          en: <>Look at the CMB closely and you'll find it isn't perfectly uniform. Some patches are a touch hotter, some a touch cooler. The variations are tiny — just ±10⁻⁵ of the mean. But those tiny patches are the gravitational seeds from which every galaxy grew.</>,
        })}
      </p>

      <Callout variant="wow">
        {pick({
          ru: <>Каждый раз, когда твой старый аналоговый телевизор показывал «снег» — около 1% этого шума было реликтовым излучением. То есть ты в детстве ненарочно смотрел детство Вселенной.</>,
          en: <>Every time an old analog TV showed static, about 1% of that "snow" was the cosmic microwave background. As a kid you were unintentionally watching the Universe's babyhood.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Спектр мощности — нотный лист неба", en: "The power spectrum — sheet music of the sky" })}</h3>
      <p>
        {pick({
          ru: <>Карта неба — это, по сути, сложная картинка. Чтобы извлечь из неё физику, космологи раскладывают её на «гармоники» — аналог разложения музыки на ноты. Каждая нота — это <Term id="multipole">мультиполь</Term> с номером ℓ.</>,
          en: <>The sky map is a complex picture. To extract the physics, cosmologists decompose it into "harmonics" — like decomposing music into notes. Each note is a <Term id="multipole">multipole</Term> with index ℓ.</>,
        })}
      </p>

      <MathBlock
        title={p("Спектр мощности CMB", "CMB power spectrum")}
        historyId="cmb-power-spectrum"
        formula="D_\ell = \dfrac{\ell(\ell+1)\, C_\ell}{2\pi}"
        caption={p("Сколько «энергии» в флуктуациях температуры на каждом угловом масштабе.", "How much temperature-fluctuation 'energy' lives on each angular scale.")}
        legend={[
          { sym: "\\ell", meaning: p("номер мультиполя — мелкость рисунка. Большое ℓ — мелкая рябь.", "multipole index — fineness of the pattern. Large ℓ = fine ripples.") },
          { sym: "C_\\ell", meaning: p("дисперсия на этом мультиполе — насколько «громко» звучит нота", "variance at that multipole — how 'loud' the note plays") },
          { sym: "D_\\ell", meaning: p("приведённая мощность, удобная для глаза", "rescaled power, easier on the eye") },
        ]}
      />

      <p>
        {pick({
          ru: <>На графике D_ℓ видно три «пика» — это акустические колебания плазмы до рекомбинации. Барионы и фотоны вместе работали как пружинка-шарик, а тёмная материя притягивала их обратно. Высота пиков рассказывает о составе Вселенной.</>,
          en: <>The D_ℓ plot shows three "peaks" — acoustic oscillations of the plasma before recombination. Baryons and photons acted like a spring–mass system, and dark matter pulled them back in. The heights of the peaks reveal the Universe's composition.</>,
        })}
      </p>

      <Callout variant="math" title={p("Почему пиков именно три?", "Why three peaks?")}>
        {pick({
          ru: <>Это «застывшая фотография» звуковых волн в момент рекомбинации. Первый пик — масштаб, где волны успели один раз сжаться. Второй — успели сжаться и разжаться. Третий — два раза сжаться. Сравнивая высоты пиков, мы узнаём, сколько в Вселенной <Term id="baryon">барионов</Term>, сколько <Term id="dark-matter">тёмной материи</Term>, и насколько искривлено пространство.</>,
          en: <>Think of it as a frozen snapshot of sound waves at recombination. The first peak is the scale where the wave had time to compress once. The second — compress and rarefy. The third — compress twice. Comparing peak heights tells us how many <Term id="baryon">baryons</Term> there are, how much <Term id="dark-matter">dark matter</Term>, and how curved space is.</>,
        })}
      </Callout>

      <Callout variant="challenge">
        {pick({
          ru: <>Открой <strong>Лабораторию → Шесть параметров</strong>. Подвинь Ω_b h² и наблюдай, как меняется высота пиков. Затем подвинь n_s и заметь общий наклон. Это космологи делают каждый день — только с реальными данными от телескопов.</>,
          en: <>Open <strong>Lab → Six Parameters</strong>. Slide Ω_b h² and watch the peak heights change. Then slide n_s and note the overall tilt. Cosmologists do exactly this — only with real data from telescopes.</>,
        })}
      </Callout>
    </>
  );
}
