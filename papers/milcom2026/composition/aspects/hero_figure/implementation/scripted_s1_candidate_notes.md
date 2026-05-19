# Scripted Hero Figure Candidate S1

## Purpose

Candidate S1 is a deterministic SVG/PDF implementation of the DQNGuard hero figure. It is generated from Python rather than produced by a raster image-generation model so that layout, labels, sizes, colors, and geometry are reproducible.

## Input comparison point

Candidate S1 is intended to be compared against Gemini candidate G1.

Gemini G1 was useful for validating the overall four-region structure:

1. OTA RF Observation
2. PA Backbone
3. DQNGuard
4. Outputs and Downstream Use

However, G1 had several weaknesses for publication use:

- text was too small in places;
- downstream modules were cramped;
- PA Backbone was visually overcomplicated;
- mathematical notation was not reliably typeset;
- the figure was not easily editable or reproducible.

## S1 design choice

S1 keeps the same conceptual structure but implements it as a deterministic vector diagram:

- double-column IEEE figure dimensions;
- grouped regions with fixed positions;
- DQNGuard as the visual center;
- compressed PA Backbone representation;
- explicit known/unknown output split;
- downstream modules as contextual consumers;
- reusable script for future revisions.

## Files

Generated files:

- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s1.svg
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s1.pdf
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s1.png

Generator:

- papers/milcom2026/composition/aspects/hero_figure/implementation/generate_hero_figure_s1.py

## Next CA round

The next comparative-analysis round should be:

003_gemini_g1_vs_scripted_s1_hero_figure.md

Its goal is to compare G1 and S1 as figure candidates, identify which layout choices survive, and decide what S2 should change.
