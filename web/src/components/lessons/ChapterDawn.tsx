import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { MathBlock } from "../ui/Math";

export function ChapterDawn() {
  const { pick } = useT();
  return (
    <>
      <p>
        {pick({
          ru: <>После рекомбинации Вселенная стала прозрачной. Но смотреть в ней было… не на что. Звёзд ещё не было. Только остывающий нейтральный водород, тёмная материя и тёмные «комки», в которые гравитация постепенно собирала газ. Этот период длился около ста миллионов лет и называется <Term id="dark-ages">тёмными веками</Term>.</>,
          en: <>After recombination the Universe was transparent. But there was nothing to look at. No stars yet. Only cooling neutral hydrogen, dark matter, and slowly forming gravitational clumps. This phase lasted about a hundred million years — the <Term id="dark-ages">Dark Ages</Term>.</>,
        })}
      </p>

      <Callout variant="story" title={p("Невидимый каркас", "The invisible scaffold")}>
        {pick({
          ru: <><Term id="dark-matter">Тёмная материя</Term> начала формировать каркас будущей Вселенной задолго до того, как зажглись первые звёзды. Она не светится, но гравитирует, и обычное вещество стекало в её «гравитационные колодцы». Сначала появились гало — компактные сгустки тёмной материи, потом в них начал концентрироваться газ.</>,
          en: <><Term id="dark-matter">Dark matter</Term> started building the future Universe's scaffold long before any stars lit up. It doesn't glow, but it does gravitate, and ordinary matter poured into its "gravity wells". First came halos — compact dark matter clumps — then gas concentrated inside them.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Включаются первые звёзды", en: "The first stars switch on" })}</h3>
      <p>
        {pick({
          ru: <>Через ≈ 100–200 миллионов лет первый сгусток газа стал достаточно плотным, чтобы зажечь термоядерные реакции. Так появилась первая звезда — представитель самого первого поколения, <strong>Population III</strong>. Эти звёзды были огромными (десятки и сотни масс Солнца), голубыми и короткоживущими.</>,
          en: <>About 100–200 million years in, the first gas clump grew dense enough to ignite thermonuclear fusion. The very first star was born — a member of the original generation, <strong>Population III</strong>. They were huge (tens to hundreds of solar masses), blue, and short-lived.</>,
        })}
      </p>

      <Callout variant="wow">
        {pick({
          ru: <>Каждая звезда первого поколения прожила, возможно, всего несколько миллионов лет — и взорвалась как сверхновая. Но за этот короткий миг она навсегда заменила лицо Вселенной: создала первые тяжёлые элементы и засеяла ими межгалактический газ. Из этих «семян» через миллиарды лет возникнет всё — углерод твоих клеток, железо твоей крови, кислород твоего вдоха.</>,
          en: <>A first-generation star may have lived just a few million years — then exploded as a supernova. But in that brief instant it forever changed the Universe: it forged the first heavy elements and seeded them into the intergalactic gas. From those seeds, billions of years later, everything would grow — the carbon in your cells, the iron in your blood, the oxygen in your breath.</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Реионизация", en: "Reionization" })}</h3>
      <p>
        {pick({
          ru: <>Ультрафиолет первых звёзд оказался настолько мощным, что начал разрывать атомы водорода обратно на электрон + протон. Этот процесс — <em>реионизация</em>. Параметр, который описывает, насколько сильно она «помешала» CMB, называется <Term id="tau" />.</>,
          en: <>The first stars' ultraviolet light was powerful enough to tear hydrogen atoms back into electron + proton. This process is <em>reionization</em>. The parameter that captures how much it interfered with the CMB is called <Term id="tau" />.</>,
        })}
      </p>

      <MathBlock
        title={p("Подавление амплитуды CMB", "CMB amplitude suppression")}
        formula="C_ℓ → C_ℓ · e^{−2τ}"
        caption={p("Чем больше τ, тем сильнее «приглушается» исходный CMB на больших ℓ.", "The bigger τ, the more the original CMB on small angular scales gets muted.")}
        legend={[
          { sym: "τ", meaning: p("оптическая глубина реионизации — доля рассеянных фотонов", "reionization optical depth — fraction of scattered photons") },
          { sym: "C_ℓ", meaning: p("исходный спектр CMB", "original CMB spectrum") },
        ]}
      />

      <Callout variant="tip">
        {pick({
          ru: <>Современные значения: τ ≈ 0.054 — это значит, что ≈ 5% фотонов CMB рассеялись в эпоху первых звёзд. Звучит мало, но именно по этому числу мы оцениваем, когда зажглись первые звёзды (около z ≈ 8, или 600 миллионов лет после Большого Взрыва).</>,
          en: <>Today's value: τ ≈ 0.054 — about 5% of CMB photons scattered during the first-stars era. Tiny number, but it tells us when the first stars ignited (around z ≈ 8, or 600 million years after the Big Bang).</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Космическая паутина", en: "The cosmic web" })}</h3>
      <p>
        {pick({
          ru: <>Через миллиарды лет гравитация сложила всё в гигантскую структуру: галактики собрались в скопления, скопления — в сверхскопления, между ними протянулись филаменты, разделённые гигантскими пустотами (войдами). Если посмотреть на самую большую карту Вселенной — выглядит это как трёхмерная нейросеть. Или как… паутина.</>,
          en: <>Over billions of years gravity assembled everything into a giant structure: galaxies clumped into clusters, clusters into superclusters, with filaments connecting them and vast voids in between. The largest cosmic maps look like a 3D neural network — or a spider's web.</>,
        })}
      </p>

      <Callout variant="challenge">
        {pick({
          ru: <>Открой <strong>Лабораторию → Играбельная Вселенная</strong> и нажми «Создать Вселенную». Получится ли паутина? Затем уменьши Ω_cdm h² до 0.05 и попробуй снова. Что произошло?</>,
          en: <>Open <strong>Lab → Playable Universe</strong> and press "Create Universe". Does a web appear? Then drop Ω_cdm h² to 0.05 and try again. What happened?</>,
        })}
      </Callout>
    </>
  );
}
