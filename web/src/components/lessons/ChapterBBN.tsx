import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { MathBlock } from "../ui/Math";

export function ChapterBBN() {
  const { pick } = useT();
  return (
    <>
      <p>
        {pick({
          ru: <>В первые секунды после Большого Взрыва Вселенная была кухней. Не звёздной — ядерной. За три минуты она сварила почти весь существующий водород, гелий и крошечные следы дейтерия и лития. Этот процесс называется <Term id="bbn">первичным нуклеосинтезом</Term> (или просто BBN — от Big Bang Nucleosynthesis).</>,
          en: <>In the first seconds after the Big Bang, the Universe was a kitchen — a nuclear one. In three minutes it cooked almost all the existing hydrogen, helium, and traces of deuterium and lithium. This process is called <Term id="bbn">Big Bang Nucleosynthesis</Term> (BBN for short).</>,
        })}
      </p>

      <Callout variant="story" title={p("Три минуты, изменившие всё", "Three minutes that changed everything")}>
        {pick({
          ru: <>Когда Вселенной была одна секунда, температура составляла около 10 миллиардов градусов — горячее центра Солнца в тысячу раз. Электроны, протоны, нейтроны и фотоны летали в виде раскалённой плазмы. Через три минуты температура упала до 100 миллионов градусов, и в этом «окне» успели слиться ядра. Открой это окно слишком рано — слишком жарко, ядра разваливаются. Слишком поздно — нейтроны распадаются, и не из чего собирать гелий.</>,
          en: <>When the Universe was one second old, the temperature was around 10 billion kelvin — a thousand times hotter than the Sun's core. Electrons, protons, neutrons and photons buzzed in a glowing plasma. After three minutes it had cooled to 100 million kelvin, and in that window nuclei could fuse. Too early — too hot, nuclei break apart. Too late — neutrons decay, and there's nothing left to make helium from.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Рецепт Вселенной", en: "The recipe of the Universe" })}</h3>
      <p>
        {pick({
          ru: <>В конце концов получился такой состав:</>,
          en: <>The final mix came out like this:</>,
        })}
      </p>
      <ul>
        <li><strong>{pick({ ru: "≈ 75% водорода", en: "≈ 75% hydrogen" })}</strong> {pick({ ru: "(одиночные протоны)", en: "(lone protons)" })}</li>
        <li><strong>{pick({ ru: "≈ 25% гелия-4", en: "≈ 25% helium-4" })}</strong> {pick({ ru: "(2 протона + 2 нейтрона)", en: "(2 protons + 2 neutrons)" })}</li>
        <li><strong>{pick({ ru: "≈ 0.01% дейтерия и трития", en: "≈ 0.01% deuterium & tritium" })}</strong></li>
        <li><strong>{pick({ ru: "≈ 10⁻⁹ лития-7", en: "≈ 10⁻⁹ lithium-7" })}</strong></li>
      </ul>
      <p>
        {pick({
          ru: <>Никаких более тяжёлых элементов в этой кухне ещё не варилось. Углерод, кислород, железо, золото — всё это придёт позже, в недрах звёзд. Ты, кстати, преимущественно сварен из звёздного пепла.</>,
          en: <>Nothing heavier was cooked in this kitchen. Carbon, oxygen, iron, gold — all of it comes later, inside stars. You, by the way, are mostly stardust.</>,
        })}
      </p>

      <Callout variant="wow">
        {pick({
          ru: <>Каждый атом водорода в стакане воды был создан в первые три минуты после Большого Взрыва. Чашка чая в твоей руке — это памятник той эпохе.</>,
          en: <>Every hydrogen atom in your glass of water was forged in the first three minutes after the Big Bang. Your cup of tea is a monument to that era.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Почему именно 25% гелия?", en: "Why 25% helium?" })}</h3>
      <p>
        {pick({
          ru: <>Когда Вселенная остыла настолько, что свободные нейтроны перестали превращаться в протоны (и наоборот), их соотношение «застыло» примерно как 1 нейтрон на 7 протонов. Все нейтроны затем встроились в гелий-4 (по 2 нейтрона на ядро). Доля массы гелия — это доля нейтронов умножить на 2 + 2:</>,
          en: <>When the Universe cooled enough that free neutrons stopped flipping back and forth with protons, their ratio froze at roughly 1 neutron to 7 protons. All neutrons then snapped into helium-4 (2 neutrons per nucleus). The helium mass fraction is the neutron fraction times 2 + 2:</>,
        })}
      </p>
      <MathBlock
        title={p("Доля гелия", "Helium fraction")}
        historyId="helium-fraction"
        formula="Y_p = \dfrac{2\, n}{n + p} \approx 0.25"
        caption={p("Почти не зависит от космологических параметров — это одно из лучших предсказаний BBN.", "Almost independent of cosmological parameters — one of BBN's strongest predictions.")}
        legend={[
          { sym: "Y_p", meaning: p("массовая доля гелия-4", "helium-4 mass fraction") },
          { sym: "n/p", meaning: p("отношение нейтронов к протонам в момент заморозки ≈ 1/7", "neutron-to-proton ratio at freeze-out ≈ 1/7") },
        ]}
      />

      <Callout variant="math" title={p("Зачем нам Ω_b h²?", "Why we care about Ω_b h²")}>
        {pick({
          ru: <>Доля дейтерия очень чувствительна к плотности обычного вещества. Если барионов больше — дейтерий быстрее сгорает в гелий, и его остаётся меньше. Измерив дейтерий в древних квазарах, астрономы получают независимую оценку <Term id="omega-b-h2" />, и она прекрасно сходится с тем, что Planck измерил в CMB. Две совершенно разные методики дают одно число — и это огромный успех современной космологии.</>,
          en: <>The deuterium fraction is very sensitive to the density of ordinary matter. More baryons → deuterium burns away into helium faster → less D survives. Measuring deuterium in ancient quasars gives an independent estimate of <Term id="omega-b-h2" />, and it matches Planck's CMB measurement beautifully. Two completely different techniques agree — a huge success for modern cosmology.</>,
        })}
      </Callout>

      <Callout variant="challenge">
        {pick({
          ru: <>Открой <strong>Лабораторию → Шесть параметров</strong> и подвинь Ω_b h² к нижней границе. Какие пики спектра CMB изменятся? (Совет: первые два — баланс барионов и тёмной материи.)</>,
          en: <>Open <strong>Lab → Six Parameters</strong> and push Ω_b h² to the low end. Which peaks of the CMB spectrum shift? (Hint: the first two — they reflect the balance of baryons and dark matter.)</>,
        })}
      </Callout>
    </>
  );
}
