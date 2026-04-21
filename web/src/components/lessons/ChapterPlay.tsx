import React from "react";
import { useT, p } from "../../i18n";
import { Term } from "../ui/Term";
import { Callout } from "../ui/Callout";
import { Button } from "../ui/Button";
import { useRouter } from "../../router";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { theme } from "../../theme";

export function ChapterPlay() {
  const { pick } = useT();
  const { go } = useRouter();
  return (
    <>
      <p>
        {pick({
          ru: <>Дальше — твоя очередь. У тебя есть четыре инструмента и шесть рычагов. Можно построить свою Вселенную и посмотреть, какая получится. Будут ли в ней звёзды? Галактики? Планеты, где может появиться жизнь?</>,
          en: <>From here it's your turn. You have four tools and six levers. Build your own Universe and see what comes out. Will it host stars? Galaxies? Planets where life could rise?</>,
        })}
      </p>

      <Callout variant="story" title={p("Принцип игры", "How to play")}>
        {pick({
          ru: <>Каждая лаборатория — мини-симулятор. Двигай слайдеры, нажимай «запустить», смотри, что меняется. Никаких правильных и неправильных ответов — это эксперимент. Когда захочешь вернуться к «настоящей» Вселенной, нажми «Сброс к Planck 2018».</>,
          en: <>Each lab is a mini-simulator. Move the sliders, hit "run", watch what changes. There are no right or wrong answers — it's an experiment. When you want the "real" Universe back, hit "Reset to Planck 2018".</>,
        })}
      </Callout>

      <h3>{pick({ ru: "Четыре эксперимента — четыре открытия", en: "Four experiments, four discoveries" })}</h3>

      <div style={{ display: "grid", gap: 14, gridTemplateColumns: "1fr 1fr", margin: "20px 0" }}>
        <Card padding={20} tone="starlight">
          <Badge tone="starlight" glyph="⏳">{pick({ ru: "Машина времени", en: "Time Machine" })}</Badge>
          <h4 style={{ marginTop: 8, color: theme.color.ink }}>{pick({ ru: "Прыжки сквозь эпохи", en: "Jumping across epochs" })}</h4>
          <p style={{ color: theme.color.inkSoft, fontSize: 14, marginTop: 6 }}>
            {pick({
              ru: <>Слайдер log(t) идёт от 10⁻⁴³ секунды до 13.8 миллиардов лет. На каждой эпохе ты видишь температуру, плотность, какая компонента доминирует. Сравни «Planck» и «Now» — ощути масштаб.</>,
              en: <>The log(t) slider goes from 10⁻⁴³ s to 13.8 Gyr. At every epoch you see temperature, density, which component dominates. Compare "Planck" with "Now" — feel the scale.</>,
            })}
          </p>
          <Button variant="outline" size="sm" style={{ marginTop: 12 }} onClick={() => go({ name: "lab", tool: "time" })}>
            {pick({ ru: "Открыть лабораторию", en: "Open the lab" })}
          </Button>
        </Card>
        <Card padding={20} tone="plasma">
          <Badge tone="plasma" glyph="⚛">{pick({ ru: "Шесть параметров", en: "Six Parameters" })}</Badge>
          <h4 style={{ marginTop: 8, color: theme.color.ink }}>{pick({ ru: "Слышишь, как звучит небо", en: "Hear the sky" })}</h4>
          <p style={{ color: theme.color.inkSoft, fontSize: 14, marginTop: 6 }}>
            {pick({
              ru: <>Подвинь H₀, n_s, A_s — спектр CMB перерисовывается мгновенно. Попробуй найти параметры, при которых первый пик смещается влево (большие пятна на небе).</>,
              en: <>Slide H₀, n_s, A_s — the CMB spectrum redraws instantly. Try to find parameters that push the first peak to the left (bigger patches on the sky).</>,
            })}
          </p>
          <Button variant="outline" size="sm" style={{ marginTop: 12 }} onClick={() => go({ name: "lab", tool: "params" })}>
            {pick({ ru: "Открыть лабораторию", en: "Open the lab" })}
          </Button>
        </Card>
        <Card padding={20} tone="nova">
          <Badge tone="nova" glyph="🌀">{pick({ ru: "Играбельная Вселенная", en: "Playable Universe" })}</Badge>
          <h4 style={{ marginTop: 8, color: theme.color.ink }}>{pick({ ru: "Расти структуру руками", en: "Grow structure by hand" })}</h4>
          <p style={{ color: theme.color.inkSoft, fontSize: 14, marginTop: 6 }}>
            {pick({
              ru: <>Поставь параметры, нажми «Создать Вселенную» — посмотри, как из крошечных флуктуаций вырастает <Term id="dark-matter">тёмная</Term> паутина. Поставишь Ω_cdm на 0 — получишь скучную серую кашу.</>,
              en: <>Set parameters, hit "Create Universe" — watch a <Term id="dark-matter">dark</Term> web grow from tiny fluctuations. Zero out Ω_cdm and you'll see a boring grey mush.</>,
            })}
          </p>
          <Button variant="outline" size="sm" style={{ marginTop: 12 }} onClick={() => go({ name: "lab", tool: "playable" })}>
            {pick({ ru: "Открыть лабораторию", en: "Open the lab" })}
          </Button>
        </Card>
        <Card padding={20} tone="aurora">
          <Badge tone="aurora" glyph="🔭">{pick({ ru: "Охота за аномалиями", en: "Anomaly Hunter" })}</Badge>
          <h4 style={{ marginTop: 8, color: theme.color.ink }}>{pick({ ru: "Заметь странное на небе", en: "Spot the weird in the sky" })}</h4>
          <p style={{ color: theme.color.inkSoft, fontSize: 14, marginTop: 6 }}>
            {pick({
              ru: <>Сгенерируй небесную карту, прогони детектор. Скрипт ищет места, выходящие за порог 3σ — потенциальные кандидаты в новую физику.</>,
              en: <>Generate a sky map and run the detector. It searches for spots beyond 3σ — potential candidates for new physics.</>,
            })}
          </p>
          <Button variant="outline" size="sm" style={{ marginTop: 12 }} onClick={() => go({ name: "lab", tool: "anomaly" })}>
            {pick({ ru: "Открыть лабораторию", en: "Open the lab" })}
          </Button>
        </Card>
      </div>

      <Callout variant="wow" title={p("Тонкая настройка", "Fine-tuning")}>
        {pick({
          ru: <>Если измените Ω_cdm h² c 0.12 до 0.30, тёмной материи станет в 2.5 раза больше. Структура соберётся слишком быстро, галактики получатся плотными «мячиками» — без места для планетарных систем. А если уменьшите до 0.02, гравитация не успеет ничего собрать. Жизнь оказывается возможна в очень узком коридоре параметров.</>,
          en: <>Set Ω_cdm h² from 0.12 up to 0.30, and dark matter will be 2.5× more abundant. Structure forms too fast, galaxies become dense "balls" with no room for planetary systems. Drop it to 0.02 and gravity can't assemble anything. Life turns out to be possible only in a very narrow corridor of parameters.</>,
        })}
      </Callout>

      <Callout variant="challenge" title={p("Финальное задание", "Final challenge")}>
        {pick({
          ru: <>Создай «жилую» Вселенную: вырасти структуру, в которой паутина видна, но не слишком плотная. Сохрани в памяти параметры. Это твой собственный космологический рецепт.</>,
          en: <>Build a "habitable" Universe: grow a web that's visible but not too dense. Note down the parameters. That's your personal cosmological recipe.</>,
        })}
      </Callout>

      <p>
        {pick({
          ru: <>Поздравляем — ты прошёл базовый курс космологии Cosmic Academy. Это начало. Дальше — настоящие учебники, серьёзные статьи, может быть, своё открытие. Удачи!</>,
          en: <>Congratulations — you've completed Cosmic Academy's basic course. That's just the beginning. Next come real textbooks, serious papers, perhaps your own discovery. Good luck!</>,
        })}
      </p>
    </>
  );
}
