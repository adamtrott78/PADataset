> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../../../CONTEXT.md).

# Scripted Hero Figure Candidate S2

## Purpose

Candidate S2 revises S1 after comparing Gemini G1 and Scripted S1.

## Main changes from S1

1. Replaced SVG marker arrows with custom polygon arrowheads.
2. Reduced arrowhead size.
3. Reduced figure height.
4. Reduced font sizes.
5. Removed the bottom explanatory note.
6. Made PA Backbone connectors quieter.
7. Improved downstream spacing.
8. Preserved the four-region evidence-flow structure.

## Design intent

S2 keeps the deterministic SVG/PDF workflow while correcting the visual issues that made S1 look too aggressive and cluttered. It remains a scripted figure so later revisions can be controlled through code rather than repeated image-generation prompts.

## Files

Generator:

- papers/milcom2026/composition/aspects/hero_figure/implementation/generate_hero_figure_s2.py

Generated outputs:

- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s2.svg
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s2.pdf
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s2.png

## Next step

Compare S1 and S2 from a reader perspective. If S2 is visually superior, insert S2 into the paper methodology section and compile the full PDF.
