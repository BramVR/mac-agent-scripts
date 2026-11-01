---
name: statechart-report
description: "Interactive HTML report for statechart / TLA+ / TLC model-check results."
---

# Statechart Report

Present results from `t3-pstack:statechart`. Pstack checks the model; this skill only presents its output. Do not edit or copy the pstack skill.

## Run

After the statechart command writes its `--out` folder:

```sh
node <skill dir>/scripts/statechart-report.mjs OUT_DIR [--config FILE]
```

Needs Node 18+. The first run installs `pele@1.9.0` under `${XDG_CACHE_HOME:-~/.cache}/statechart-report/` with npm.

Writes into `OUT_DIR`:

- `report.html`: standalone self-contained page, Field Notes theme (Flexoki paper, ink-blue path, brick-red failure).
- `report.embed.html`: same page for T3 `html_render`, drawn as one rounded paper card with no page background.
- `chart.svg`: `chart.mmd` rendered with Pele, using the statechart skill's `references/render.md` mark classes in Flexoki light and dark colors.

`--config` defaults to `SPEC.cfg` beside the spec path TLC printed in `tlc.out`. Pass it when the spec folder moved.

## Show

1. `html_preview` with the contents of `report.embed.html`. Check the screenshot and console.
2. `html_render` with the same HTML and `contentHeight` as height.
3. In the reply, give the absolute paths of `report.html` and `chart.svg`, plus the statechart skill's usual hand-off lines. The report does not replace the Mermaid block or the per-bug lines that the statechart skill asks for.

## What it shows

- Each rule from `report.md`: breaks, holds, not checked, or no result (listed in the config but absent from `report.md`). Never present not checked or no result as passing.
- Failure replay per broken rule with Previous and Next. Steps come only from the numbered path in `report.md`, which the statechart command takes from TLC's state graph. A step that stays in one chart state, or whose arrow the view hides, is shown as such. No step is invented from the Mermaid chart.
- TLC's own printed counterexample from `tlc.out` or `tlc-RULE.out`, with actions, source lines, and changed values. It can differ from the replay path when TLC finds a different shortest path of the same length. Both are real checker paths.
- Bounds: config text, `report.md` notes, and TLC run facts. Rule and action source lines appear only when the spec files are still at the path in `tlc.out`.

## Readable labels

Labels come from the statechart view (`state()`, `step()`). Raw TLA+ action names in the report mean the view lacks `step()`. Fix the view and rerun the statechart command. The renderer does not rename anything.

## Test

```sh
node --test <skill dir>/scripts/test/*.test.mjs
```

Fixtures are real statechart outputs: TwoPhase (fails), MediaPlayerFixed (passes), MediaPlayerProps (properties and loops). The DOM test installs `jsdom@30.1.3` into the same cache.
