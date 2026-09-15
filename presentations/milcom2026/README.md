# MILCOM 2026 Presentation Package

This directory is the cold-start entry point for planning and building the presentation for:

**DQNGuard: Towards Open-World RF Preliminary-Action Detection**

## Purpose

This presentation has two immediate uses:

1. first review with Nate before MILCOM,
2. polished final conference presentation for MILCOM 2026.

The first review deck should already be close to the intended final narrative, but it is expected to change after Nate's feedback.

## Audience

Assume an **industry professional with general technical, RF, and/or security competence**, but **no prior knowledge of this project's niche terminology**.

Do not assume familiarity with:

- Preliminary Actions (PAs),
- DQNGuard,
- VarMax,
- DQN-IDS,
- surrogate-open calibration,
- the Target-Surrogate Matrix,
- this repository's data-generation or experiment infrastructure.

The talk should be understandable without having read the paper.

## Communication contract

Use the same communication heuristics that guided the paper, tightened for a spoken presentation:

1. **Slide titles state conclusions, not topics.**
2. **One intellectual job per slide.**
3. **Concrete example before jargon.**
4. **Define niche terminology at first contact.**
5. **Prefer pictures -> labels -> numbers -> equations.**
6. **Every result must answer a question established earlier.**
7. **Optimize for the "lazy reviewer":** the story should remain recoverable from slide titles and major visuals alone.
8. **Do not overclaim beyond the paper or repository evidence.**
9. **Do not make the audience remember implementation details that are not required to understand the scientific claim.**
10. **Use the script to add nuance; do not overload the slide itself.**

## Canonical production files

A rendering session should read these in this order:

1. [SVG_PRODUCTION_SPEC.md](SVG_PRODUCTION_SPEC.md) — **production authority for SVG geometry, typography, palette, object hierarchy, asset use, and exact slide composition.**
2. [PRESENTATION_PLAN.md](PRESENTATION_PLAN.md) — canonical scientific/design provenance: audience takeaway, rationale, claims, numbers, and forbidden interpretations.
3. [SCRIPT.md](SCRIPT.md) — spoken script for Slides 2–12. The Slide 1 opening script is currently embedded in `SVG_PRODUCTION_SPEC.md`.

Read the broader repository only if a scientific ambiguity remains:

4. [../../papers/CONTEXT.md](../../papers/CONTEXT.md) — paper-writing and evidence discipline.
5. [../../papers/milcom2026/CONTEXT.md](../../papers/milcom2026/CONTEXT.md) — MILCOM paper tooling and provenance.
6. [../../experiments/context/DQNGUARD.md](../../experiments/context/DQNGUARD.md) — DQNGuard lineage and claim boundaries.
7. [../../experiments/context/RESULTS.md](../../experiments/context/RESULTS.md) — final result interpretation and provenance.

Do not read the repository recursively. Follow these routes only as needed.

## Source-of-truth precedence

For production work:

1. scientific claim / numerical conflict -> `PRESENTATION_PLAN.md` and reviewed result provenance win;
2. SVG/layout/rendering conflict -> `SVG_PRODUCTION_SPEC.md` wins;
3. narration wording -> `SCRIPT.md` wins except for Slide 1, whose opening script is in `SVG_PRODUCTION_SPEC.md`;
4. camera-ready paper title/author/affiliation block is authoritative for Slide 1.

An older `PRESENTATION_PLAN.md` status may still call Slide 1 `TBD`; that marker is stale. Slide 1 is now concept locked in `SVG_PRODUCTION_SPEC.md`.

## Camera-ready title-page identity

Use the submitted camera-ready paper identity:

**DQNGuard: Towards Open-World RF Preliminary-Action Detection**

Authors:

- Adam Trott — University of Massachusetts Dartmouth
- Cameron Popillo — University of Massachusetts Dartmouth
- Nathaniel D. Bastian — Johns Hopkins University
- Roulin Zhou — University of Massachusetts Dartmouth
- Gokhan Kul — University of Massachusetts Dartmouth

Do not infer author affiliations from older presentation material.

## Scientific interpretation that must not be lost

### Performance variability

The `mean ± standard deviation` values in the main results table are **across held-out PA folds**, not repeated identical evaluator runs.

For DQNGuard under the fixed Scan/PA1-surrogate condition:

- Burst / PA2 unknown F1: ~0.706
- Sustain / PA3 unknown F1: ~0.987
- Hop / PA4 unknown F1: ~0.783
- Replay / PA8 unknown F1: ~0.983
- mean ± standard deviation: **0.865 ± 0.142**

Interpretation:

- performance is strongly target-dependent;
- the Target-Surrogate Matrix shows that surrogate-target compatibility is a major source of this sensitivity;
- do **not** describe the ±0.142 value as stochastic rerun variance.

The current evaluator is deliberately seeded, and surviving repeated same-configuration DQNGuard evaluations reproduce identical metrics. This supports the distinction above.

### Future-work thread

A key future direction is **multi-surrogate DQNGuard calibration**, inspired by the earlier VarMax surrogate-all idea.

Goal:

> aggregate calibration evidence from multiple surrogate behaviors so DQNGuard is less dependent on a fortunate single surrogate-target pairing.

Candidate architectures currently retained for the presentation are:

- pooled multi-surrogate DQN,
- surrogate-specific DQN ensemble with score normalization/aggregation,
- hybrid VarMax/DQNGuard design that places multi-surrogate evidence in the deterministic guard portion while preserving one learned DQN signal.

These are **proposed future work**, not demonstrated results.

### Claim boundary

DQNGuard is a sensing / triage layer for open-world RF behavior. It is not the complete QR-CWoS response system.

## Current deck-level narrative

The locked main-deck story is:

> closed-set classifiers cannot reject novelty -> define the five Preliminary Actions -> establish the OTA three-protocol dataset -> motivate an explicit known-rejection operating constraint -> introduce DQNGuard -> explain surrogate-open calibration -> show the fixed-surrogate operating-point result -> expose target/surrogate dependence -> show why simple target-blind surrogate selection fails -> motivate multi-surrogate DQNGuard -> close with three takeaways.

The intellectual climax remains:

> DQNGuard improves the operating point -> performance still varies by target -> the Target-Surrogate Matrix reveals strong surrogate-target dependence -> target-blind selection is unreliable -> multi-surrogate calibration becomes the natural next research direction.

## Current status

- Slide 1: **concept locked; camera-ready title/author identity, 58/42 title layout, hero preview, and opening script are specified**
- Slides 2–12: **concept locked**
- Deck-wide visual system: **locked in `SVG_PRODUCTION_SPEC.md`**
- Per-slide 16:9 SVG geometry/object hierarchy: **locked in `SVG_PRODUCTION_SPEC.md`**
- Spoken script: **complete for Slides 2–12; Slide 1 opening retained in the SVG spec**
- Camera-ready DQNGuard hero asset: **available**
- Target-Surrogate Matrix presentation asset: **available**
- OTA image directories: **reserved; final imagery still pending**
- Final SVG slides: **not yet built**
- Final PowerPoint: **not yet assembled**

## Presentation assets

Current presentation asset tree:

```text
presentations/milcom2026/assets/
├── figures/
│   ├── hero_dqnguard_pipeline_s23_tikz.pdf
│   └── target_surrogate_unknown_f1_matrix.png
├── ota/
│   ├── wifi/
│   ├── bluetooth/
│   └── zigbee/
└── README.md
```

Asset rules are defined in `SVG_PRODUCTION_SPEC.md`.

Important constraints:

- use the committed **s23** camera-ready hero PDF, not older hero revisions;
- use the reviewed Target-Surrogate Matrix asset or intentionally regenerate it from reviewed provenance;
- never fabricate OTA scientific imagery for Slides 3–4;
- Slides 3–4 may be built with fixed neutral image slots and populated when the real OTA images are generated.

## SVG-production handoff

A ChatGPT Work / artifact-building session should treat `SVG_PRODUCTION_SPEC.md` as an implementation specification, not a brainstorming prompt.

The builder should not silently redesign a locked slide into a generic corporate template. Styling is already normalized across the deck; preserve:

- information hierarchy,
- reading order,
- exact audience-facing labels/numbers,
- semantic colors,
- source assets,
- claim-sensitive wording,
- arrow semantics,
- static-slide comprehensibility.

The production spec fixes:

- 1920×1080 SVG canvas,
- safe areas and grid,
- type hierarchy,
- palette and semantic colors,
- stroke/corner-radius grammar,
- object hierarchy for every slide,
- per-slide geometry,
- scientific-asset rules,
- forbidden substitutions,
- rendering/QA checklist.

## Recommended production order

1. Slide 1 — validate global style.
2. Slide 2 — validate two-panel grammar.
3. Slide 5 — validate three-panel grammar.
4. Slide 6 — validate imported vector figure treatment.
5. Slide 8 — validate chart/metric treatment.
6. Slide 9 — validate scientific-result asset treatment.
7. Slides 7, 10, 11, 12.
8. Slides 3–4 after OTA imagery is available, or build their fixed frames now and populate imagery later.

After every SVG, render it to 1920×1080 PNG and visually QA clipping, readability, alignment, and scientific fidelity before assembling PowerPoint.

## Handoff rule for another ChatGPT

Start from this file, then read `SVG_PRODUCTION_SPEC.md`.

Consult `PRESENTATION_PLAN.md` for scientific rationale or claim boundaries rather than re-deriving the research story.

Treat all twelve main-slide concepts as locked unless the user explicitly requests a redesign.

Do not silently replace a locked visual with a generic template.