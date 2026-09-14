# MILCOM 2026 Presentation Plan

This file is the canonical slide-by-slide design specification.

Statuses:

- **CONCEPT LOCKED** — audience takeaway and basic information architecture are approved.
- **DRAFT** — concept exists but still needs user review.
- **TBD** — not yet designed.

---

# Deck skeleton

| # | Working slide title | Job | Status |
|---|---|---|---|
| 1 | Title | Introduce the work and speaker | TBD |
| 2 | Closed-set RF classifiers cannot say "I don't know" | Establish the capability gap | **CONCEPT LOCKED** |
| 3 | Preliminary Actions describe RF behavior before full attack attribution | Define PAs and make the five behaviors tangible | TBD |
| 4 | OTA dataset and system overview | Show what was actually collected and evaluated | TBD |
| 5 | Existing OSR heads do not provide the operating behavior we need | Motivate DQNGuard from VarMax and DQN-IDS | TBD |
| 6 | DQNGuard adds class-conditional guards and a known-rejection budget | Explain the proposed decision layer | TBD |
| 7 | Evaluation separates the true unknown from calibration surrogates | Explain target unknown, surrogate unknown, and fair comparison | TBD |
| 8 | DQNGuard improves the usable fixed-budget operating point | Present the main method comparison | TBD |
| 9 | Performance still depends strongly on the unseen behavior | Explain the across-fold standard deviation correctly | TBD |
| 10 | Surrogate usefulness depends on the target unknown | Present and interpret the Target-Surrogate Matrix | TBD |
| 11 | Multi-surrogate calibration may reduce target-surrogate sensitivity | Future work and broader implications | TBD |
| 12 | Takeaways | Leave three memorable conclusions and transition to Q&A | TBD |

The intellectual climax should remain:

> DQNGuard improves the operating point -> performance still varies by target -> the Target-Surrogate Matrix reveals strong surrogate-target dependence -> multi-surrogate calibration becomes a natural next research direction.

---

# Slide 2 — Closed-set RF classifiers cannot say "I don't know"

## Status

**CONCEPT LOCKED**

The first visual concept was rejected because its output examples could be mistaken for an enumeration of the known label space. The visual below is the **second iteration** and should be preserved for future presentation-building work.

## Audience takeaway

> A conventional RF classifier must assign every observation to something it already knows, even when the observed behavior is genuinely novel.

The audience should understand this slide within a few seconds without needing the narration.

## Slide title

**Closed-set RF classifiers cannot say "I don't know"**

## Supporting sentence

**Unseen behavior is forced into a known label, even when the prediction is wrong.**

Do not introduce DQNGuard in the title or supporting sentence.

## Visual concept

Use a large **side-by-side before/after comparison**.

The visual should contrast:

1. a conventional closed-set classifier, and
2. the open-world capability the application actually needs.

Use the **same known input and same novel input** in both panels so that the only difference is the available decision behavior.

### Left panel — CLOSED-SET CLASSIFIER

At the top:

**CLOSED-SET CLASSIFIER**

Show its allowed outputs explicitly:

**Allowed outputs:** `Scan | Burst | Hop`

Then show two cases.

**Case 1: known behavior**

`Known Burst behavior -> RF classifier -> Burst ✓`

**Case 2: novel behavior**

`Novel RF behavior -> RF classifier -> forced known prediction: Hop ✕`

The specific wrong label is not scientifically important. It simply demonstrates that the classifier must choose a known class.

Bottom callout:

**"Unknown" is not an available output.**

### Right panel — OPEN-WORLD REQUIREMENT

At the top:

**OPEN-WORLD REQUIREMENT**

Allowed outputs:

`Scan | Burst | Hop | UNKNOWN`

Use the exact same two example inputs.

**Case 1: known behavior**

`Known Burst behavior -> open-world decision -> Burst ✓`

**Case 2: novel behavior**

`Novel RF behavior -> open-world decision -> UNKNOWN ✓`

Bottom callout:

**Preserve known evidence. Isolate unfamiliar behavior.**

## Rough visual mockup — second iteration

Preserve this mockup as design intent even if the final slide uses polished graphics:

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ Closed-set RF classifiers cannot say “I don’t know”                         │
│ Unseen behavior is forced into a known label, even when the prediction       │
│ is wrong.                                                                    │
│                                                                               │
│     CLOSED-SET CLASSIFIER                 OPEN-WORLD REQUIREMENT              │
│                                                                               │
│     Allowed outputs:                       Allowed outputs:                    │
│     Scan | Burst | Hop                     Scan | Burst | Hop | UNKNOWN        │
│                                                                               │
│     [Known Burst]                          [Known Burst]                       │
│           ↓                                      ↓                            │
│      RF classifier                         open-world decision                 │
│           ↓                                      ↓                            │
│        Burst ✓                                Burst ✓                          │
│                                                                               │
│     [Novel behavior]                       [Novel behavior]                    │
│           ↓                                      ↓                            │
│      RF classifier                         open-world decision                 │
│           ↓                                      ↓                            │
│         Hop ✕                               UNKNOWN ✓                          │
│                                                                               │
│     “Unknown” is not an option.            Preserve known evidence.           │
│                                            Isolate unfamiliar behavior.       │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Final graphic treatment

The final slide should be visually much cleaner than the ASCII mockup.

Preferred treatment:

- two balanced panels;
- minimal prose;
- small RF/spectrogram-style thumbnails for the known and novel observations rather than plain text boxes, if an appropriate asset is available;
- visually de-emphasize the particular wrong known label;
- visually emphasize that **UNKNOWN is absent on the left and available on the right**;
- keep the same input examples aligned horizontally between the two panels.

Do not add all five final PA classes here. Slide 3 will properly introduce the PA taxonomy.

## Why this visual is structured this way

The visual must communicate two things at once without ambiguity:

1. open-set recognition adds the ability to reject unfamiliar behavior;
2. it should **not** discard correct known classifications.

The second point prepares the audience for the later 5% known-rejection budget. We are planting the preservation requirement before presenting the mechanism.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-2--closed-set-rf-classifiers-cannot-say-i-dont-know).

## Transition

End with:

> **"So what exactly are the RF behaviors we're trying to recognize?"**

This should transition directly into Slide 3.

## Terminology / claim constraints

- Do **not** use "zero-day" on this slide; it carries a narrower software-security meaning than needed here.
- Prefer **"previously unseen RF behavior"**, **"novel behavior"**, or **"behavior outside the trained taxonomy."**
- Do not introduce OSR jargon until the capability gap is already understood.
- Do not imply that high confidence guarantees correctness.
- Do not imply that the open-world decision is intended to replace known-class classification.

---

# Slide 3 — Preliminary Actions

## Status

**TBD**

Next design task.

The slide should answer, in plain language:

> What exactly is a Preliminary Action, how is it different from protocol/modulation classification, and what five behaviors were evaluated?

Potential five final behaviors:

- Scan
- Burst
- Sustain
- Hop
- Replay

Do not lock composition until this slide is explicitly reviewed.

---

# Performance-variability note for later slides

The final paper's main result table reports **standard deviation across held-out PA folds**, not repeated identical runs.

For fixed Scan/PA1-surrogate DQNGuard:

| Target unknown | Unknown F1 |
|---|---:|
| Burst / PA2 | ~0.706 |
| Sustain / PA3 | ~0.987 |
| Hop / PA4 | ~0.783 |
| Replay / PA8 | ~0.983 |
| Mean ± SD | **0.865 ± 0.142** |

Slide 9 should explain that this is target-dependent variation.

The Target-Surrogate Matrix then provides the broader evidence that surrogate-target compatibility materially affects unknown detection.

Do **not** claim that surrogate-target interaction quantitatively explains "almost all" variance unless a dedicated decomposition is performed.

---

# Future-work note for later slides

A strong future direction is to extend DQNGuard from **single-surrogate calibration** toward **multi-surrogate calibration**, inspired by VarMax surrogate-all.

Desired presentation claim:

> Aggregating evidence from several surrogate behaviors may make DQNGuard less dependent on a favorable single surrogate-target pairing and may reduce target-dependent performance variability.

This is a hypothesis / proposed future direction, not a demonstrated result.
