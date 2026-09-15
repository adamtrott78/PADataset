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

## Canonical planning files

Read in this order:

1. [PRESENTATION_PLAN.md](PRESENTATION_PLAN.md) — canonical slide-by-slide concept and visual plan.
2. [SCRIPT.md](SCRIPT.md) — spoken script for slides whose concepts are sufficiently stable.
3. [../../papers/CONTEXT.md](../../papers/CONTEXT.md) — paper-writing and evidence discipline.
4. [../../papers/milcom2026/CONTEXT.md](../../papers/milcom2026/CONTEXT.md) — MILCOM paper tooling and provenance.
5. [../../experiments/context/DQNGUARD.md](../../experiments/context/DQNGUARD.md) — DQNGuard lineage and claim boundaries.
6. [../../experiments/context/RESULTS.md](../../experiments/context/RESULTS.md) — final result interpretation and provenance.

Do not read the repository recursively. Follow these routes only as needed.

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

Possible future architectures include pooled surrogate calibration, per-surrogate guard ensembles, robust envelopes, or learned weighting. These are **proposed future work**, not demonstrated results.

### Claim boundary

DQNGuard is a sensing / triage layer for open-world RF behavior. It is not the complete QR-CWoS response system.

## Current deck-level narrative

The current intended story is:

> why open-world PA recognition matters -> what a PA is -> what data/system was built -> why existing OSR heads are insufficient -> what DQNGuard does -> how it was evaluated -> what it improves -> why performance varies -> what the Target-Surrogate Matrix reveals -> what should come next.

The current target is approximately 11-12 main slides plus backups. Exact slide count remains adjustable to the MILCOM speaking slot.

## Current status

- Deck skeleton: **provisional but strong**
- Slide 2: **concept locked; visual composition revised once and retained in full**
- Slide 3: **concept locked; Preliminary Action framing and five-behavior visual retained in full**
- Slide 4: **concept locked; OTA 3×5 protocol/behavior matrix and N210 capture overview retained in full**
- Slide 5: **concept locked; OSR predecessor comparison and corrected DQN-style confidence diagram retained in full**
- Slide 6: **concept locked; final s22 DQNGuard hero-figure source path, mockup, and speaker script retained in full**
- Slide 7: **concept locked; leave-two-out surrogate-open calibration design, one-backbone mechanics, and script retained in full**
- Slide 8: **concept locked; fixed-surrogate operating-point comparison, AUROC caveat, plot mockup, and script retained in full**
- Slide 9: **concept locked; Figure 2 Target-Surrogate Matrix centered, provenance distinction preserved, and consolidated speaker script retained in full**
- Slide 10: **concept locked; target-blind surrogate-selection diagnostics, negative-result framing, and consolidated speaker script retained in full**
- Slide 11: **concept locked; VarMax surrogate-all mechanism, DQNGuard architectural mismatch, future architecture options, and consolidated speaker script retained in full**
- Remaining slides: **to be designed one by one**
- Final PowerPoint: **not yet built**
- Final spoken script: **not yet complete**

## Handoff rule for another ChatGPT

Start from this file, then read `PRESENTATION_PLAN.md`.

Treat any slide marked **CONCEPT LOCKED** as authoritative unless the user explicitly requests a redesign.

Do not silently replace a locked visual with a generic template. Preserve the intended audience takeaway, information hierarchy, and transition even if the final graphic treatment changes.
