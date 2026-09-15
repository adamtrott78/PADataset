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
| 3 | Preliminary Actions capture RF behavior, not final attack labels | Define PAs and make the five behaviors tangible | **CONCEPT LOCKED** |
| 4 | We evaluate the same five behaviors over-the-air across three protocol families | Show what was actually collected and evaluated | **CONCEPT LOCKED** |
| 5 | Unknown detection is only useful if known behavior stays usable | Motivate DQNGuard from VarMax and DQN-IDS | **CONCEPT LOCKED** |
| 6 | DQNGuard adds a budgeted open-world decision layer to the PA classifier | Explain the proposed decision layer | **CONCEPT LOCKED** |
| 7 | A surrogate unknown shapes the DQN; the true unknown remains unseen until test | Explain target unknown, surrogate unknown, and fair comparison | **CONCEPT LOCKED** |
| 8 | DQNGuard gives the strongest usable operating point at low known rejection | Present the main method comparison | **CONCEPT LOCKED** |
| 9 | Surrogate usefulness depends strongly on the unseen target | Make Figure 2 the central diagnostic result and explain target-surrogate dependence | **CONCEPT LOCKED** |
| 10 | No simple target-blind rule reliably predicts the best surrogate | Explain failed surrogate-selection diagnostics and the remaining deployment problem | **CONCEPT LOCKED** |
| 11 | VarMax can search across surrogates; DQNGuard must learn how to combine them | Explain surrogate-all, the architectural mismatch, and the multi-surrogate DQNGuard research direction | **CONCEPT LOCKED** |
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

# Slide 3 — Preliminary Actions capture RF behavior, not final attack labels

## Status

**CONCEPT LOCKED**

## Audience takeaway

> A Preliminary Action is observable RF behavior that may precede, enable, or contextualize a later cyber or Electronic Warfare attack technique. It is precursor evidence, not a final attack-technique label.

The audience should understand that the project classifies **behavior visible in RF**, not final ATT&CK/EW attribution.

## Slide title

**Preliminary Actions capture RF behavior, not final attack labels**

## Supporting sentence

**Preliminary Actions are observable RF behaviors, not final attack-technique labels.**

Keep the visible slide text short. The fuller MITRE ATT&CK connection belongs in the spoken script.

## Visual concept

Use five equal behavior cards across the middle of the slide. The slide should be dominated by the five behaviors themselves rather than by another flowchart.

Each card should contain:

1. behavior name,
2. representative RF/spectrogram-style thumbnail,
3. one very short plain-English behavioral description.

### Behavior cards

**Scan**  
Discovery-like activity

**Burst**  
Short transmissions + quiet gaps

**Sustain**  
Persistent channel occupancy

**Hop**  
Frequency dwell + revisits

**Replay**  
Repeated waveform / template

Prefer representative examples from the actual dataset or existing presentation assets over generic icons.

Do not show repository identifiers PA1 / PA2 / PA3 / PA4 / PA8 in the main slide. Those identifiers are implementation provenance, not audience-facing terminology.

## Bottom conceptual contrast

At the bottom of the slide, make the claim boundary explicit with two compact labels:

**WHAT IT TELLS US**  
Observable RF behavior

**WHAT IT DOES NOT CLAIM**  
Final attack-technique attribution

Optional footer:

**Same behavioral taxonomy evaluated across WiFi, Bluetooth, and Zigbee.**

This footer also prepares the transition into the OTA dataset/system slide.

## Rough visual mockup

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ Preliminary Actions capture RF behavior, not final attack labels             │
│ Preliminary Actions are observable RF behaviors, not final attack-technique   │
│ labels.                                                                       │
│                                                                               │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│   │   SCAN   │ │  BURST   │ │ SUSTAIN  │ │   HOP    │ │  REPLAY  │           │
│   │          │ │          │ │          │ │          │ │          │           │
│   │ [RF img] │ │ [RF img] │ │ [RF img] │ │ [RF img] │ │ [RF img] │           │
│   │          │ │          │ │          │ │          │ │          │           │
│   │Discovery │ │Short TX +│ │Persistent│ │Freq dwell│ │Repeated  │           │
│   │ activity │ │quiet gaps│ │ occupancy│ │+ revisits│ │ template │           │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                               │
│   WHAT IT TELLS US                          WHAT IT DOES NOT CLAIM             │
│   Observable RF behavior                    Final attack-technique attribution │
│                                                                               │
│   Same behavioral taxonomy evaluated across WiFi, Bluetooth, and Zigbee      │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Why this visual is structured this way

Slide 2 establishes that the classifier needs an `UNKNOWN` option. The natural next question is:

> Unknown relative to what?

Slide 3 answers that question by making the known PA taxonomy concrete.

The audience should leave understanding that these are **behavioral RF patterns** intended to serve as precursor evidence. They should not leave thinking the model directly assigns final ATT&CK or EW attack-technique labels.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-3--preliminary-actions-capture-rf-behavior-not-final-attack-labels).

## Transition

End with:

> **"To test that in the real RF environment, we built an over-the-air dataset spanning all three protocol families."**

This transitions directly into Slide 4.

## Terminology / claim constraints

- Use **cyber or Electronic Warfare attack technique** rather than the vaguer term `effect`.
- The MITRE ATT&CK connection may be stated as downstream **ATT&CK-style reasoning**, not as a claim that the PA labels themselves are ATT&CK technique labels.
- Preserve the paper's framing that a PA may **precede, enable, or contextualize** a later attack technique.
- Do not overstate temporal ordering by defining every PA as something that literally occurs before an attack.
- Use **Scan, Burst, Sustain, Hop, Replay** in the main talk; reserve PA numbers for backup/provenance.
- Do not imply that protocol identity is the PA label. The same behavioral taxonomy is studied across WiFi, Bluetooth, and Zigbee.


---

# Slide 4 — We evaluate the same five behaviors over-the-air across three protocol families

## Status

**CONCEPT LOCKED**

## Audience takeaway

> The classifier is evaluated on real over-the-air RF captures, with the same five behavioral labels expressed through WiFi, Bluetooth, and Zigbee.

This slide establishes experimental scope and credibility without becoming a hardware-specification slide.

## Slide title

**We evaluate the same five behaviors over-the-air across three protocol families**

## Supporting sentence

**WiFi, Bluetooth, and Zigbee each express Scan, Burst, Sustain, Hop, and Replay behavior in captured RF.**

The emphasis should be on **behavior across protocols**, not protocol identification.

## Visual concept

Use two coordinated regions:

1. a large **3 × 5 behavior/protocol matrix** showing dataset scope;
2. a compact **OTA capture pipeline** showing how one classifier input is produced.

### Left — 3 × 5 dataset scope matrix

Rows:

- WiFi
- Bluetooth
- Zigbee

Columns:

- Scan
- Burst
- Sustain
- Hop
- Replay

Preferred treatment is one representative RF/spectrogram-style thumbnail per cell if the images remain legible. If 15 thumbnails become visually noisy, use a reduced image treatment while preserving the obvious 3-protocol × 5-behavior structure.

Above the matrix, include a compact label:

**5 behaviors × 3 protocols**

The matrix should visually communicate:

> the same behavioral taxonomy is instantiated across multiple protocol families.

### Right — OTA capture pipeline

Keep the acquisition flow intentionally simple:

```text
USRP N210 TX
     ↓
 over the air
     ↓
USRP N210 RX
     ↓
32 ms RF window
     ↓
classifier input
```

Use the hardware label:

**2× USRP N210 SDRs**

Do **not** label the device as "Ettus N210" in the presentation.

Add only the key capture facts:

- **12.5 MS/s**
- **400,000 complex IQ samples / window**
- **2.437 GHz**
- **32 ms per RF window**

Do not include daughterboard names, antenna model, radio spacing, switch model, gain settings, shard counts, or seed schedules in the main slide. Those belong in backup material if needed.

## Rough visual mockup

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ We evaluate the same five behaviors over-the-air across three protocol families │
│ WiFi, Bluetooth, and Zigbee each express the same PA taxonomy in captured RF.   │
│                                                                                  │
│                    5 BEHAVIORS × 3 PROTOCOLS          OTA CAPTURE                │
│                                                                                  │
│               Scan  Burst Sustain  Hop Replay          ┌───────────┐             │
│ WiFi          [img] [img]  [img]  [img] [img]         │N210 TX SDR│             │
│                                                       └─────┬─────┘             │
│ Bluetooth     [img] [img]  [img]  [img] [img]               │ RF                │
│                                                               ▼                 │
│ Zigbee        [img] [img]  [img]  [img] [img]         ┌───────────┐             │
│                                                       │N210 RX SDR│             │
│                                                       └─────┬─────┘             │
│                                                               ▼                 │
│                                                        32 ms RF window           │
│                                                                                  │
│                                           12.5 MS/s • 400k complex IQ samples    │
│                                           2.437 GHz • 2× USRP N210 SDRs          │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Why this visual is structured this way

Slide 3 defines the PA taxonomy. Slide 4 answers the next audience question:

> What did you actually test this on?

The matrix establishes that the research object is **behavior recognition across protocol realizations**, not simply protocol classification.

The small capture pipeline establishes that evaluation uses captured OTA RF rather than only synthetic or digital waveforms.

Do not spend the audience's attention budget on a large system-architecture diagram here. The major architecture diagram later should be reserved for DQNGuard.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-4--we-evaluate-the-same-five-behaviors-over-the-air-across-three-protocol-families).

## Transition

End with:

> **"With that dataset in place, the next question is how to decide when the classifier's prediction should actually be trusted."**

This transitions into the OSR decision-layer motivation.

## Terminology / claim constraints

- Use **USRP N210 SDR** / **USRP N210 software-defined radio** in the presentation.
- Do not describe the PA label as the protocol label.
- Emphasize that the same behavioral taxonomy is evaluated across WiFi, Bluetooth, and Zigbee.
- The OTA window is **400,000 complex IQ samples at 12.5 MS/s**, corresponding to **32 ms**.
- Main capture frequency: **2.437 GHz**.
- A generation target of 10,000 windows per protocol/action pair exists in the paper, but it is intentionally omitted from the main slide unless later needed for audience context.


---

# Slide 5 — Unknown detection is only useful if known behavior stays usable

## Status

**CONCEPT LOCKED**

## Audience takeaway

> A detector can appear good at finding unknowns simply by rejecting too many legitimate known samples. The operational requirement is unknown detection under an explicit cost on known rejection.

This slide motivates DQNGuard from the operating requirement rather than from algorithm names.

## Slide title

**Unknown detection is only useful if known behavior stays usable**

## Supporting sentence

**The OSR decision must detect unfamiliar behavior without solving the problem by rejecting too much known data.**

## Visual concept

Use a three-panel horizontal story:

1. **VarMax — score-based rejection**
2. **DQN-style confidence head — learned decision**
3. **Operational requirement — explicit known-rejection budget**

The three panels are conceptually related but are **not one continuous pipeline**. In particular, the DQN-style panel must not visually connect to the known-rejection-budget panel with a shared arrow.

### Left panel — VarMax

Heading:

**VARMAX — SCORE-BASED REJECTION**

Plain-English role:

**Uses confidence, variance, and energy-style evidence to score unfamiliar inputs.**

Simple flow:

```text
classifier evidence
       ↓
unknownness score
       ↓
   threshold
       ↓
 known / unknown
```

Positive tag:

**✓ useful unknownness evidence**

Limitation tag:

**✕ threshold choice can sacrifice known samples**

Do not frame VarMax as a failed method. It is prior work that supplies useful novelty evidence and motivates part of DQNGuard.

### Middle panel — DQN-style confidence head

Heading:

**DQN-STYLE CONFIDENCE HEAD**

Plain-English role:

**Learns a known/unknown decision from confidence-state features.**

The correct diagram is:

```text
P1      ┐
P1-P2   ├──→ learned decision ───→ known / unknown
H(p)    ┘
```

Alternative polished rendering:

```text
[DQN confidence state]
 P1
 P1 − P2
 H(p)
        ↓
 [learned decision]
        ↓
 known / unknown
```

The three confidence features all feed into **one learned decision block**. No arrow from this panel should cross into or point at the operational-requirement panel.

Positive tag:

**✓ learned decision boundary**

Limitation tag:

**✕ no explicit guarantee on known rejection**

### Right panel — operational requirement

Heading:

**WHAT DEPLOYMENT ACTUALLY NEEDS**

Core visual:

```text
Detect unknowns
      +
Preserve known classifications
      ↓
EXPLICIT KNOWN-REJECTION BUDGET
```

Strong callout:

> **Reject unfamiliar behavior — but only within a controlled known-sample cost.**

This should be the visually strongest panel because it is the requirement DQNGuard is designed around.

## Rough visual mockup — corrected

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Unknown detection is only useful if known behavior stays usable                 │
│ The OSR decision must detect unfamiliar behavior without rejecting too much      │
│ legitimate known data.                                                          │
│                                                                                  │
│   VARMAX                    DQN-STYLE HEAD             OPERATIONAL REQUIREMENT    │
│                                                                                  │
│   classifier evidence       P1      ┐                  Detect unknowns            │
│          ↓                  P1-P2   ├──→ learned             +                   │
│   unknownness score         H(p)    ┘    decision      Preserve known             │
│          ↓                               ↓                   ↓                    │
│      threshold                        known / unknown   KNOWN-REJECTION BUDGET    │
│          ↓                                                                       │
│    known / unknown                                                               │
│                                                                                  │
│   ✓ useful evidence          ✓ learned boundary         “Reject unfamiliar        │
│   ✕ threshold can            ✕ no explicit               behavior within a        │
│     sacrifice knowns           known-cost guarantee       controlled cost.”       │
└──────────────────────────────────────────────────────────────────────────────────┘
```

The DQN-style arrows above are the **corrected diagram**. They do not cross and do not point toward the known-rejection-budget panel.

## Why this visual is structured this way

The slide should not read as:

> Here are two old methods and now here is our method.

It should read as:

1. VarMax shows that classifier-output structure contains useful novelty evidence.
2. DQN-style work shows that confidence can be treated as a learned decision state.
3. Neither framing alone makes the known-sample cost the explicit operating constraint.
4. Therefore the next design requirement is a known-rejection budget.

This makes Slide 6 feel like a direct response to a clearly established requirement.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-5--unknown-detection-is-only-useful-if-known-behavior-stays-usable).

## Transition

End with:

> **“That operating constraint is the central idea behind DQNGuard.”**

This transitions directly into Slide 6.

## Terminology / claim constraints

- Do not show Table I numbers on this slide; save the empirical payoff for the results section.
- Do not imply that VarMax or the DQN-style head are useless; present them as useful predecessors with different operating behavior.
- Do not claim that the DQN-style head literally has no threshold; the presentation claim is that it does not make the known-rejection budget the explicit deployment constraint.
- Keep the focus on the operational cost of rejecting legitimate known samples.


---

# Slide 6 — DQNGuard adds a budgeted open-world decision layer to the PA classifier

## Status

**CONCEPT LOCKED**

## Audience takeaway

> DQNGuard does not replace the PA classifier. It evaluates whether the classifier's prediction conforms to learned known behavior and routes nonconforming observations to an unknown pool under an explicit known-rejection budget.

This is the central architecture slide of the talk.

## Slide title

**DQNGuard adds a budgeted open-world decision layer to the PA classifier**

## Supporting sentence

**DQNGuard decides whether the classifier's prediction conforms to learned known behavior.**

Keep this sentence short. The mechanism is already visible in the hero figure.

## Canonical visual asset

Reuse the final hero figure from the accepted paper.

**Canonical source file:**

`papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.tex`

The accepted paper references a compiled vector PDF named:

`papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.pdf`

but that compiled PDF is not currently tracked in GitHub. The presentation-building workflow should therefore render/export the **s22 TikZ source** to a presentation-friendly vector format, preferably SVG or another PowerPoint-safe vector representation, rather than using an earlier SVG iteration.

Do **not** substitute an older `s1`–`s13` SVG merely because it is already an SVG. The s22 TikZ source is the authoritative final figure.

## Figure content that must remain legible

The hero figure communicates this left-to-right evidence flow:

```text
RF Input
   ↓
Multi-Domain PA Encoder
   IQ | FFT | DCT | Polar
   ↓
PA CNN
   ↓
PA prediction / logits / softmax / features
   ↓
DQNGuard
   1. Predicted-class calibration
   2. Guard evidence
   3. Known-budget threshold (β = 0.05)
   ↓
Known PA  OR  Unknown
   ↓
Downstream ATT&CK/EW hypotheses / label-making / QR-CWoS planning
```

The main talk should preserve the entire figure because the audience needs to see that DQNGuard is a **decision layer over a closed-set PA backbone**, not a replacement classifier.

## What is newly introduced on this slide

Slides 2–5 establish:

- why `UNKNOWN` is necessary;
- what Preliminary Actions are;
- what OTA dataset was evaluated;
- why unknown detection must control known-sample cost.

Slide 6 introduces the internal DQNGuard mechanism for the first time:

1. **Predicted-class calibration**  
   Compare the sample against calibration statistics for the class the backbone predicts.

2. **Guard evidence**  
   Use confidence-gap, entropy, variance-style, energy-style, and related evidence to measure nonconformity.

3. **Known-budget threshold**  
   Route the sample as unknown only when its nonconformity crosses a threshold selected from known calibration data to respect the explicit known-rejection budget.

The main experiments use **β = 0.05**, corresponding to a 5% known-rejection budget.

## Visual composition

The slide should be visually simple:

- conclusion-style title at top;
- one short supporting sentence;
- final s22 hero figure spanning nearly the full remaining width;
- no additional bullet column competing with the figure.

Optional presentation polish:

- during narration, use simple progressive emphasis / highlighting over the three DQNGuard stages if PowerPoint animation is reliable;
- otherwise, keep the full figure static and use a pointer / verbal walk-through.

Do not redraw the architecture from scratch unless the final vector export is unusable at presentation scale.

## Rough visual mockup

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ DQNGuard adds a budgeted open-world decision layer to the PA classifier          │
│ DQNGuard decides whether the classifier's prediction conforms to learned known    │
│ behavior.                                                                         │
│                                                                                   │
│  ┌───────────┐  ┌───────────────────────────────┐  ┌──────────────────────┐       │
│  │ RF INPUT  │→ │ MULTI-DOMAIN PA ENCODER       │→ │      DQNGUARD        │       │
│  │           │  │ IQ | FFT | DCT | Polar        │  │                      │       │
│  │ RF window │  │      ↓                         │  │ 1. predicted-class   │       │
│  │           │  │    PA CNN                      │  │    calibration       │       │
│  └───────────┘  │      ↓                         │  │          ↓           │       │
│                 │ pred / logits / softmax / h    │  │ 2. guard evidence    │       │
│                 └───────────────────────────────┘  │          ↓           │       │
│                                                    │ 3. known-budget       │       │
│                                                    │    threshold β=.05    │       │
│                                                    └──────────┬───────────┘       │
│                                                               │                   │
│                                                   ┌───────────┴───────────┐       │
│                                                   ▼                       ▼       │
│                                               KNOWN PA                UNKNOWN      │
│                                                   │                       │       │
│                                                   └──────→ downstream ←───┘       │
│                                                          reasoning                 │
│                                                                                   │
│                    [USE FINAL s22 PAPER HERO FIGURE, NOT THIS REDRAW]              │
└──────────────────────────────────────────────────────────────────────────────────┘
```

The mockup is only an information-layout reminder. The **actual slide should use the final s22 paper figure**.

## Why this visual is structured this way

The paper hero figure already embodies the presentation's communication heuristic: observation -> backbone evidence -> guard decision -> downstream consumer.

Reusing it preserves consistency between the accepted paper and the talk and avoids forcing the audience to reconcile two different architectural representations of DQNGuard.

The slide should make one conceptual point:

> DQNGuard sits between the closed-set classifier and downstream reasoning, and it controls the accept/reject decision under a known-sample cost.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-6--dqnguard-adds-a-budgeted-open-world-decision-layer-to-the-pa-classifier).

## Transition

End with:

> **"But this creates one more problem: if the true unknown has never been seen before, what open-set evidence do we use to calibrate that decision?"**

This transitions directly into Slide 7 and introduces surrogate-open calibration exactly when the audience has a reason to care about it.

## Intentionally deferred to Slide 7

Do **not** explain surrogate-open calibration on Slide 6.

After this slide, the audience should understand **how DQNGuard makes the routing decision**, but not yet where surrogate-open calibration evidence comes from.

Slide 7 will introduce:

- target unknown,
- surrogate unknown,
- known classes,
- fixed-surrogate evaluation,
- the distinction between calibration evidence and the genuinely unseen target behavior.

## Terminology / claim constraints

- DQNGuard is a **decision layer over the PA backbone**, not a replacement classifier.
- The final deployed threshold is selected from **known calibration scores** under the known-rejection budget.
- Surrogate-open evidence may shape / diagnose the guard but does not define the final known-budget threshold in the current implementation.
- Keep downstream ATT&CK/EW / label-making / QR-CWoS boxes visible enough to reinforce that DQNGuard is a sensing and triage layer, not the full response system.


---

# Slide 7 — A surrogate unknown shapes the DQN; the true unknown remains unseen until test

## Status

**CONCEPT LOCKED**

## Audience takeaway

> DQNGuard intentionally withholds two PA behaviors from the backbone: one becomes surrogate-open calibration evidence, while the other remains completely unseen until final evaluation.

The surrogate is not a class the backbone is expected to recognize. It is deliberately out-of-taxonomy behavior used to shape the DQN confidence decision. The true target unknown is never used for backbone training or OSR calibration.

## Slide title

**A surrogate unknown shapes the DQN; the true unknown remains unseen until test**

## Supporting sentence

**One leave-two-out backbone is trained on the remaining known PAs; the surrogate is used only for OSR calibration, while the target appears only at test.**

## Concrete example

Use one specific fold to make the roles obvious:

- **Surrogate unknown:** Scan
- **True target unknown:** Sustain
- **Known classes:** Burst, Hop, Replay

For this fold, the backbone output taxonomy contains only:

`Burst | Hop | Replay`

There is no Scan output class and no Sustain output class.

## Critical mechanism

The slide must communicate four facts directly:

1. **One backbone, not two.**  
   The backbone is trained only on Burst, Hop, and Replay.

2. **Scan is withheld from backbone training.**  
   During OSR calibration, Scan windows are passed through that same three-class backbone. The backbone necessarily forces them into one of its known labels; DQNGuard observes the resulting confidence state as surrogate-open evidence.

3. **The surrogate affects DQN fitting.**  
   The DQN confidence head is fitted using both known calibration states and surrogate-open states.

4. **Sustain remains completely untouched until final evaluation.**  
   Sustain is not used for backbone training, DQN fitting, guard-band fitting, or threshold selection. Scan is also absent from final evaluation.

## Important calibration distinction

The surrogate does **not** directly choose every part of DQNGuard.

Current implementation:

- **DQN fitting:** known calibration + surrogate-open calibration
- **Predicted-class guard bands:** known calibration only
- **Final 5% score threshold:** known calibration scores only
- **Final evaluation:** known test classes + target unknown only; surrogate excluded

This distinction must remain explicit so the slide does not imply that the surrogate directly sets the final 5% threshold.

## Visual composition

Use a single central backbone with two clearly separated withheld behaviors.

The slide should read top-to-bottom:

1. train the leave-two-out backbone;
2. use known + surrogate evidence to fit the DQN;
3. use known calibration alone to fit guard bands and the 5% operating threshold;
4. evaluate on known test data plus the untouched target unknown.

The surrogate and target should have visibly different roles:

- **Scan — surrogate-open calibration only**
- **Sustain — test only**

Use a visible note near the evaluation block:

**Scan is not included in final test metrics.**

## Rough visual mockup

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ A surrogate unknown shapes the DQN; the true unknown remains unseen until test  │
│ One leave-two-out backbone is trained on the remaining known PAs.                │
│                                                                                  │
│                    EXAMPLE: surrogate = Scan | target = Sustain                  │
│                                                                                  │
│                         BACKBONE TRAINING                                         │
│                  Burst + Hop + Replay only                                       │
│                              │                                                   │
│                              ▼                                                   │
│                   3-class PA backbone                                            │
│                   Burst | Hop | Replay                                            │
│                              │                                                   │
│               ┌──────────────┴──────────────┐                                    │
│               │                             │                                    │
│               ▼                             ▼                                    │
│      KNOWN CALIBRATION                 SCAN SURROGATE                             │
│      Burst / Hop / Replay              withheld from training                    │
│               │                             │                                    │
│               └──────────────┬──────────────┘                                    │
│                              ▼                                                   │
│                     FIT DQN CONFIDENCE HEAD                                      │
│                   known + surrogate states                                       │
│                              │                                                   │
│          ┌───────────────────┴───────────────────┐                               │
│          │                                       │                               │
│          ▼                                       ▼                               │
│  FIT GUARD BANDS ON KNOWN ONLY        SET 5% THRESHOLD ON KNOWN ONLY            │
│          │                                       │                               │
│          └───────────────────┬───────────────────┘                               │
│                              ▼                                                   │
│                         FINAL EVALUATION                                          │
│             Known test: Burst + Hop + Replay                                     │
│             Target unknown: Sustain                                              │
│             Surrogate Scan: NOT INCLUDED                                         │
│                              │                                                   │
│                              ▼                                                   │
│                        KNOWN / UNKNOWN?                                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Why this visual is structured this way

The audience already knows from Slide 6 how DQNGuard scores an observation. Slide 7 answers the harder question:

> If the real unknown has never been seen, where does open-set calibration evidence come from?

The answer is not to expose the true target unknown. Instead, a second withheld PA acts as a **surrogate unknown**. It shapes the DQN confidence decision, and the resulting system is then tested on a different PA that remained completely unseen.

The scientific transfer being tested is therefore:

> **Can open-set behavior learned from one withheld PA help reject a different withheld PA?**

This is the central surrogate-open contribution and must be visually obvious.

## Main comparison regime

For the main method comparison:

- **Scan is fixed as the surrogate**
- **Burst, Sustain, Hop, and Replay each take a turn as the target unknown**

For each fold, Scan and the target are both absent from backbone training. The remaining three behaviors form the known taxonomy.

The reported mean and standard deviation in the main result table are therefore across these held-out target folds, not repeated stochastic reruns.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-7--a-surrogate-unknown-shapes-the-dqn-the-true-unknown-remains-unseen-until-test).

## Transition

End with:

> **“With that fixed-surrogate design, we can now ask whether DQNGuard gives us a better usable operating point than the existing OSR heads.”**

This transitions directly into Slide 8.

## Terminology / claim constraints

- Do not describe the surrogate as a label the backbone should predict.
- The backbone's known taxonomy contains only the remaining three PA classes in each Target–Surrogate fold.
- Do not claim there are two separately trained backbones whose thresholds are transferred between them.
- The surrogate affects **DQN fitting**.
- Guard bands and the final known-budget threshold are fitted from **known calibration** only in the current implementation.
- The target unknown is never used during backbone training or surrogate-open OSR calibration.
- The surrogate is excluded from final evaluation metrics.


---

# Slide 8 — DQNGuard gives the strongest usable operating point at low known rejection

## Status

**CONCEPT LOCKED**

## Audience takeaway

> Under the main fixed-Scan-surrogate comparison, DQNGuard achieves the best thresholded operating tradeoff: the highest Unknown F1 and OSR macro F1 while keeping known rejection near the intended 5% budget.

Do **not** summarize this as “DQNGuard wins every metric.” VarMax has the highest AUROC. The scientific claim is about the usable thresholded operating point under known-sample cost.

## Slide title

**DQNGuard gives the strongest usable operating point at low known rejection**

## Guiding question

**At a practical rejection operating point, which OSR head best detects unseen PAs without sacrificing known classifications?**

## Experiment strip

Use a narrow strip at the top of the result area to restate the experimental condition:

**Fixed-surrogate comparison**

- Surrogate: **Scan**
- Targets: **Burst, Sustain, Hop, Replay**
- Reported values: **mean ± sample SD across four held-out target folds**

The ± values are **not repeated-seed variability**.

Do not claim that all three methods receive identical calibration information. The recovered comparison provenance shows that the VarMax `surrogate-all` row uses a different internal pseudo-unknown calibration scheme. Present the rows as the three evaluated OSR approaches under their reported comparison configurations.

## Main visual

Use a two-dimensional operating-point plot rather than pasting the paper table as the primary visual.

- **x-axis:** Known rejection rate — lower is better
- **y-axis:** Unknown F1 — higher is better
- desirable region: **upper-left**

Plot the paper means, and add error bars only if they remain visually clean and readable at presentation scale.

### Values

| Method | Known rejection | Unknown F1 | OSR macro F1 | AUROC |
|---|---:|---:|---:|---:|
| DQNGuard | **0.050 ± 0.004** | **0.865 ± 0.142** | **0.881 ± 0.109** | 0.891 ± 0.129 |
| DQN-IDS-style / Shreyash CNN head | 0.063 ± 0.017 | 0.701 ± 0.197 | 0.764 ± 0.119 | 0.829 ± 0.092 |
| VarMax surrogate-all | 0.128 ± 0.043 | 0.745 ± 0.146 | 0.778 ± 0.104 | **0.951 ± 0.060** |

For audience-facing wording, prefer **DQN-IDS-style head** unless provenance requires the exact tracked table label.

## AUROC caveat

Use a compact secondary callout on the right:

**VARMAX RANKS UNKNOWNS BEST**

- VarMax AUROC: **0.951**
- DQNGuard AUROC: **0.891**
- DQN-IDS-style: **0.829**

Then state:

> **Ranking quality ≠ usable thresholded decision**

This is a central interpretation, not an embarrassment to hide. VarMax provides strong aggregate ranking separation, but at its selected operating point it rejects more known samples and achieves lower Unknown F1 than DQNGuard.

## Rough visual mockup

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ DQNGuard gives the strongest usable operating point at low known rejection     │
│ Which OSR head best detects unseen PAs without sacrificing known evidence?      │
│                                                                                 │
│ FIXED-SURROGATE EXPERIMENT                                                      │
│ Scan surrogate • targets: Burst / Sustain / Hop / Replay                        │
│ mean ± SD across four held-out target folds                                     │
│                                                                                 │
│       UNKNOWN F1 ↑                                      AUROC / RANKING         │
│   1.0 ┤                                                                         │
│       │                                                                         │
│  .865 ┤    ● DQNGuard                                  VarMax        0.951       │
│       │      0.865 F1                                  DQNGuard      0.891       │
│       │      5.0% known reject                         DQN-style     0.829       │
│  .745 ┤                          ● VarMax                                       │
│       │                            0.745 F1             ───────────────────      │
│  .701 ┤       ● DQN-style          12.8% reject                                 │
│       │         0.701 F1                                                       │
│       │         6.3% reject                            Ranking quality ≠         │
│       └──────────────────────────────────────→          usable thresholded       │
│             5%      6.3%             12.8%             decision                 │
│                   KNOWN REJECTION →                                             │
│                      lower is better                                             │
│                                                                                 │
│        DQNGuard: highest Unknown F1 + lowest known rejection                    │
│        OSR macro F1: 0.881 ± 0.109                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

The final plot should be cleaner than the ASCII sketch. The key visual encoding is the upper-left operating region.

## Why this visual is structured this way

The experiment asks about an operational tradeoff, not just independent metric maxima.

A table forces the audience to mentally combine known rejection and Unknown F1. The 2D plot makes that tradeoff spatial:

- moving **left** preserves more known behavior;
- moving **up** rejects the true unknown more effectively.

DQNGuard occupies the strongest mean operating point. The AUROC callout prevents overclaiming by showing that VarMax wins the ranking metric while still losing at the selected thresholded operating point.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-8--dqnguard-gives-the-strongest-usable-operating-point-at-low-known-rejection).

## Transition

End with:

> **“But that 0.865 average hides substantial target-to-target variation.”**

The next result slide should unpack the dependence on which PA is actually unseen.

## Terminology / claim constraints

- Mean ± SD values are across **four held-out target folds**, not repeated seeds.
- DQNGuard has the strongest **thresholded operating point**, not the highest value on every metric.
- VarMax has the highest AUROC and should be credited for it.
- Do not claim all methods use scientifically identical surrogate calibration; the VarMax comparison row has different internal calibration provenance.
- Known rejection is the fraction of legitimate known test samples incorrectly routed as unknown.
- Unknown F1 is binary detection performance for the held-out target PA.
- OSR macro F1 includes the known classes plus the unknown class and therefore penalizes methods that gain unknown detection by sacrificing known classification.


---

# Slide 9 — Surrogate usefulness depends strongly on the unseen target

## Status

**CONCEPT LOCKED**

## Audience takeaway

> The surrogate-open assumption transfers unevenly: a surrogate that is highly useful for one unseen PA can be nearly useless for another.

Figure 2 is the centerpiece of this slide. The purpose is to explain **why the target-surrogate relationship matters**, not merely to show another result graphic.

## Slide title

**Surrogate usefulness depends strongly on the unseen target**

## Supporting sentence

**Rotating both the target unknown and surrogate-open class reveals strong, directional calibration dependence.**

## Experiment connection to Slide 8

Slide 8 used the fixed-Scan-surrogate comparison and reported:

**DQNGuard Unknown F1 = 0.865 ± 0.142 across the four held-out target folds.**

That standard deviation reflects **target-to-target heterogeneity**, not repeated stochastic reruns.

Slide 9 broadens the question. Instead of holding the surrogate fixed, rotate both roles:

- 5 possible target PAs
- 4 distinct surrogate choices for each target
- **20 ordered target-surrogate cells**

This tests whether surrogate-open calibration transfers uniformly across PA behaviors.

### Important provenance distinction

Do **not** claim that the Scan column in Figure 2 is numerically identical to the four fixed-Scan folds summarized on Slide 8.

The fixed-surrogate comparison and the final Target-Surrogate Matrix come from distinct reviewed result chains. Use Slide 8's `0.865 ± 0.142` to establish that target difficulty varies, then use Figure 2 as the broader experiment showing that **surrogate choice also changes performance**.

## Main visual

Make the accepted paper's **Figure 2 Target-Surrogate Matrix** approximately 70–75% of the usable slide area.

Paper include path:

`papers/milcom2026/figures/target_surrogate_matrix/target_surrogate_unknown_f1_matrix.pdf`

The compiled PDF/PNG/CSV are generated artifacts and may not be tracked in GitHub. The authoritative tracked generator is:

`papers/milcom2026/figures/target_surrogate_matrix/make_target_surrogate_matrix.py`

For presentation construction, prefer the actual accepted-paper Figure 2 asset when available. If regeneration is required, use the reviewed matrix source/provenance chain documented in `experiments/context/RESULTS.md`; do not reconstruct the matrix by manually typing values into a new graphic.

## How to read Figure 2

- **Rows:** true held-out target unknown
- **Columns:** surrogate-open calibration class
- **Cell value:** Unknown F1
- **Diagonal:** invalid / masked because the target cannot simultaneously be its own surrogate
- **Bold cell in each row:** best surrogate for that target in the plotted matrix

The accepted-paper matrix values are:

| Target ↓ / Surrogate → | Scan | Burst | Sustain | Hop | Replay |
|---|---:|---:|---:|---:|---:|
| Scan | — | 0.32 | 0.00 | **0.71** | 0.04 |
| Burst | 0.58 | — | 0.01 | 0.15 | **0.61** |
| Sustain | **0.90** | 0.00 | — | 0.79 | 0.01 |
| Hop | **0.84** | 0.10 | 0.11 | — | 0.49 |
| Replay | **0.85** | 0.77 | 0.19 | 0.76 | — |

## Bottom interpretation strip

Use three compact conclusions below the figure.

### 1. Target difficulty is real

**Slide 8: 0.865 ± 0.142 across held-out targets**

Caption:

**Variation is across target PAs — not repeated runs.**

### 2. The best surrogate changes with the target

- Scan target → **Hop**
- Burst target → **Replay**
- Sustain target → **Scan**
- Hop target → **Scan**
- Replay target → **Scan**

Headline:

**No universally best surrogate**

### 3. Some pairings nearly fail

Several cells are at or near zero Unknown F1.

Headline:

**Mismatched calibration evidence may not transfer at all**

The near-zero cells are more informative than a generic statement that performance “varies.” They show that the wrong surrogate can provide calibration evidence that is fundamentally unhelpful for the actual unseen behavior.

## Rough visual mockup

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ Surrogate usefulness depends strongly on the unseen target                    │
│ Rotating both target and surrogate reveals directional calibration dependence. │
│                                                                                │
│                     TARGET–SURROGATE MATRIX                                    │
│                                                                                │
│                           Surrogate →                                          │
│                    Scan   Burst  Sustain   Hop   Replay                         │
│            Scan      —     .32     .00     .71    .04                          │
│ Target     Burst    .58     —      .01     .15    .61                          │
│   ↓        Sustain  .90    .00      —      .79    .01                          │
│            Hop      .84    .10     .11      —     .49                          │
│            Replay   .85    .77     .19     .76     —                           │
│                                                                                │
│                 [USE ACTUAL ACCEPTED-PAPER FIGURE 2]                           │
│                                                                                │
│ ────────────────────────────────────────────────────────────────────────────── │
│ TARGET VARIATION            BEST SURROGATE CHANGES        SOME PAIRS FAIL      │
│ Slide 8: 0.865 ± 0.142      Scan → Hop                    F1 ≈ 0 in several     │
│ across target PAs           Burst → Replay                cells                │
│                             Others → Scan                                       │
│ NOT repeated-run variance   No universal surrogate        Calibration mismatch │
└────────────────────────────────────────────────────────────────────────────────┘
```

The actual figure should remain the visual focal point. The bottom strip interprets it; it should not compete with it.

## Why this visual is structured this way

The experimental story is:

1. Slide 8 establishes that DQNGuard has a strong average operating point under a fixed surrogate.
2. The large across-target SD tells us that the average is hiding heterogeneous target difficulty.
3. Figure 2 asks the broader diagnostic question: what happens when the surrogate changes too?
4. The answer is that calibration transfer is **target dependent and directional**.

This is stronger than showing a separate “variation” chart followed by the matrix on another slide. Figure 2 directly explains the broader calibration-transfer problem and keeps the experimental narrative compact.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-9--surrogate-usefulness-depends-strongly-on-the-unseen-target).

## Transition

End with:

> **“So the remaining deployment problem is not just finding a surrogate — it is knowing whether that surrogate will transfer to the unknown we have not seen yet.”**

The next slide should address the attempted surrogate-selection diagnostics and why no simple target-blind rule was reliable.

## Terminology / claim constraints

- Figure 2 reports **Unknown F1**, not AUROC or OSR macro F1.
- Target and surrogate roles are directional; `Target=A, Surrogate=B` is not equivalent to the reverse.
- The diagonal is invalid because a PA cannot serve simultaneously as the true target unknown and its surrogate.
- Do not interpret Slide 8's ±0.142 as repeated-seed or repeated-identical-run variability.
- Do not claim Figure 2's Scan column is the exact source of Slide 8's four fixed-surrogate values; preserve the distinct result provenance.
- Near-zero cells support the claim that some surrogate evidence is badly mismatched to some targets; they do not prove the underlying backbone is universally incapable of representing those targets.


---

# Slide 10 — No simple target-blind rule reliably predicts the best surrogate

## Status

**CONCEPT LOCKED**

## Audience takeaway

> The Target–Surrogate Matrix contains clear structure, but the obvious target-blind diagnostics we tested do not reliably predict which surrogate will transfer best to a future unknown.

This slide should remain part of the experimental-results story. It is not a generic limitations slide.

## Slide title

**No simple target-blind rule reliably predicts the best surrogate**

## Guiding question

**Can we choose a good surrogate before the true unknown has ever been observed?**

## Supporting sentence

**Calibration success on the surrogate itself does not reliably predict transfer to a different unseen behavior.**

## Diagnostic experiment framing

Slide 9 establishes that surrogate choice matters substantially. Slide 10 asks whether that dependence can be solved with a simple target-blind rule.

Test three intuitive families of surrogate-selection diagnostics:

1. surrogate calibration performance;
2. confidence-space geometry;
3. learned feature-space geometry.

These are exploratory surrogate-selection diagnostics, not a separately validated production selection algorithm.

## Main visual

Use three equal-width diagnostic columns that all flow into one shared conclusion.

### 1. Surrogate calibration performance

Question:

**“If I reject the surrogate well, will I reject the true unknown well?”**

Observed diagnostic:

- Spearman correlation with eventual target Unknown F1: **ρ ≈ −0.075**
- Pearson correlation: **r ≈ −0.047**
- selected the actual best surrogate for **2 of 5 targets**

Interpretation:

> **Rejecting the surrogate well does not imply that its calibration transfers.**

### 2. Confidence geometry

Question:

**“Does confidence-space behavior tell us which surrogate will transfer?”**

Candidate signals included:

- maximum softmax probability,
- top-two probability gap,
- entropy.

Observed combined confidence-geometry diagnostic:

- **ρ ≈ −0.552**

Interpretation:

> **The intuitive confidence-space rule pointed in the wrong direction overall.**

### 3. Feature geometry

Question:

**“Can representation-space distance identify a useful surrogate?”**

Observed best simple positive feature diagnostic:

- approximately **ρ ≈ +0.406**
- selected the actual best surrogate for **1 of 5 targets**

Interpretation:

> **Some positive signal exists, but feature proximity alone was not a reliable selector.**

## Rough visual mockup

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│ No simple target-blind rule reliably predicts the best surrogate                │
│ Can we choose a good surrogate before the true unknown has ever been observed?  │
│                                                                                  │
│  CALIBRATION PERFORMANCE      CONFIDENCE GEOMETRY        FEATURE GEOMETRY       │
│                                                                                  │
│  “Reject surrogate well?”     “Looks informative in      “Close in learned      │
│                                confidence space?”          feature space?”       │
│            │                           │                         │                │
│            ▼                           ▼                         ▼                │
│     ρ ≈ −0.075                  ρ ≈ −0.552                best +ρ ≈ +0.406       │
│     best: 2 / 5                wrong direction           best: 1 / 5             │
│            │                           │                         │                │
│            └───────────────────────────┴─────────────────────────┘                │
│                                      ▼                                           │
│                                                                                  │
│                         NO RELIABLE SINGLE-SURROGATE                              │
│                               SELECTION RULE                                      │
│                                                                                  │
│          Good surrogate performance does not imply good target transfer.         │
└──────────────────────────────────────────────────────────────────────────────────┘
```

The bottom conclusion should be the strongest visual element after the title.

## Why this visual is structured this way

The experimental progression is:

1. **Slide 8:** DQNGuard gives a strong fixed-surrogate operating point.
2. **Slide 9:** surrogate choice materially changes performance.
3. **Slide 10:** obvious target-blind diagnostics do not reliably solve the surrogate-selection problem.

This is scientifically stronger than presenting the Target–Surrogate Matrix as an isolated curiosity. The follow-up experiment asks whether its structure can be exploited prospectively and documents that the simple rules tested were insufficient.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-10--no-simple-target-blind-rule-reliably-predicts-the-best-surrogate).

## Transition

End with:

> **“If choosing one surrogate is fragile, and we cannot reliably know which one will transfer, the next step is to stop betting on a single surrogate.”**

This transitions directly into the multi-surrogate future-work direction.

## Terminology / claim constraints

- These are **exploratory surrogate-selection diagnostics**, not a validated automatic selection algorithm.
- Do not claim that the Target–Surrogate Matrix is random; it is structured but not captured reliably by the simple target-blind diagnostics tested.
- Do not imply access to the true target unknown when making the selection. The point is to evaluate target-blind proxies.
- Correlation does not establish a causal mechanism.
- The weak positive feature-space signal is insufficient to claim reliable surrogate prediction.
- Preserve the distinction between retrospective matrix analysis and a deployable target-blind selection policy.


---

# Slide 11 — VarMax can search across surrogates; DQNGuard must learn how to combine them

## Status

**CONCEPT LOCKED**

## Audience takeaway

> VarMax surrogate-all can compare many pseudo-unknown calibration candidates inside one fixed decision architecture. DQNGuard cannot import that procedure unchanged because changing the surrogate changes the learned DQN score function itself.

This slide serves three purposes:

1. explain **VarMax surrogate-all** as an original methodological contribution;
2. explain the concrete architectural reason it does not transfer directly into current DQNGuard;
3. turn that limitation into a specific future research direction.

## Slide title

**VarMax can search across surrogates; DQNGuard must learn how to combine them**

## Supporting sentence

**In VarMax, surrogates change calibration parameters; in DQNGuard, the surrogate changes the learned open-set decision function itself.**

Use a visible label near the VarMax section:

**ORIGINAL CONTRIBUTION — VARMAX SURROGATE-ALL**

Use a visible label near the future-work section:

**FUTURE WORK — NOT YET EVALUATED**

## Part 1 — How VarMax surrogate-all works

VarMax surrogate-all operates on **one frozen backbone**.

The backbone's known classes remain part of the classifier taxonomy. During validation/calibration, each known class takes a turn as a **pseudo-unknown** in a held-out score subset.

For each pseudo-unknown choice, VarMax sweeps candidate decision parameters:

- global top-two probability-gap threshold;
- predicted-class variance percentile bands;
- predicted-class energy percentile bands.

The validation data are partitioned so that the calibration search has separate known fitting, known guard, and pseudo-open score roles.

Each surrogate-specific threshold candidate is tested against known-retention / per-class-recall requirements plus a minimum pseudo-open recall requirement.

Candidates from **all available surrogate specifications compete in the same search**. The selected result becomes one final VarMax decision rule.

Key point:

> **Surrogate-all is not an ensemble. It searches across surrogate-specific calibration candidates and selects one final rule.**

The same trained backbone and same deterministic VarMax score/acceptance architecture are used for every candidate. Only the calibration parameters differ.

## Part 2 — Why the same procedure does not port directly to DQNGuard

Current DQNGuard is architecturally different in two important ways.

### A. The surrogate changes the learned score function

Current DQNGuard fitting uses:

```text
known confidence states
        +
surrogate-open confidence states
        ↓
      fit DQN
        ↓
Q_unknown(x) - Q_known(x)
        +
known-only band distance
        ↓
combined unknown score
```

Therefore:

- Scan surrogate → one fitted DQN;
- Burst surrogate → a different fitted DQN;
- Hop surrogate → another fitted DQN.

These are **different learned nonlinear score functions**, not merely different scalar threshold values.

The final 5% score threshold is selected from known calibration **after** that DQN has been fitted. A numeric cutoff belonging to DQN A is therefore not automatically meaningful in DQN B's score space.

This makes the VarMax operation:

> “Generate many parameter candidates, compare them directly, select one.”

non-portable as a trivial DQNGuard calibration switch.

### B. DQNGuard's external surrogate is outside the backbone taxonomy

In the main DQNGuard Target–Surrogate regime, both the target and the surrogate are withheld from backbone training.

VarMax surrogate-all is different: its pseudo-unknowns are **backbone-known classes** temporarily repurposed during calibration.

Trying to preserve DQNGuard's current external-surrogate philosophy while withholding many surrogates at once would progressively shrink the known-class taxonomy. With only five PA classes, a literal leave-many-out version quickly stops being a useful closed-set recognition problem.

## Part 3 — Future architectural question

The research question is therefore not:

> “Can we turn on surrogate-all in DQNGuard?”

It is:

> **How should DQNGuard combine multiple surrogate signals while preserving one coherent score space and its explicit known-rejection budget?**

Three concrete candidate architectures are worth testing.

### Option A — pooled multi-surrogate DQN

```text
surrogate A ─┐
surrogate B ─┼→ pooled open-state set → ONE DQN → one score space
surrogate C ─┘
```

Potential advantage:

- simplest route to one unified DQN score;
- existing known-only 5% thresholding can remain conceptually intact.

Research risk:

- heterogeneous surrogate geometries may blur the strong unknown signal learned from a favorable single surrogate.

### Option B — surrogate-specific DQN ensemble

```text
surrogate A → DQN A ─┐
surrogate B → DQN B ─┼→ normalize / aggregate → unified unknown score
surrogate C → DQN C ─┘
```

Potential advantage:

- preserves specialized surrogate-specific unknown signals.

Research problems:

- normalize incompatible DQN score spaces;
- determine aggregation rule;
- recalibrate one global known-rejection budget after aggregation.

### Option C — hybrid VarMax / DQNGuard multi-surrogate design

```text
multiple pseudo-unknowns
        ↓
VarMax-style multi-surrogate
guard / calibration evidence
        +
single learned DQN confidence signal
        ↓
budgeted combined score
```

Potential advantage:

- place multi-surrogate reasoning in the deterministic calibration/guard portion, where candidate evidence is naturally comparable;
- preserve a single learned DQN confidence signal and DQNGuard's known-budget operating constraint.

This option is especially natural given DQNGuard's historical synthesis of DQN confidence evidence with VarMax-derived predicted-class guards.

## Result motivation

VarMax surrogate-all achieved the highest AUROC in the main comparison:

**AUROC = 0.951 ± 0.060**

DQNGuard achieved the better thresholded operating point:

- Unknown F1: **0.865 ± 0.142**
- OSR macro F1: **0.881 ± 0.109**
- known rejection: **0.050 ± 0.004**

Do not claim that surrogate-all caused VarMax's AUROC advantage or that any proposed multi-surrogate DQNGuard architecture will improve results.

The motivating research objective is:

> **Can we combine VarMax's multi-surrogate calibration philosophy with DQNGuard's strong thresholded operating point and explicit known-rejection budget?**

## Rough visual mockup

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ VarMax can search across surrogates; DQNGuard must learn how to combine them           │
│ In VarMax, surrogates change parameters; in DQNGuard, they change the learned scorer.  │
│                                                                                        │
│ ORIGINAL CONTRIBUTION                     WHY IT DOESN'T PORT DIRECTLY                 │
│ VARMAX SURROGATE-ALL                                                                  │
│                                                                                        │
│       ONE FROZEN BACKBONE                  Scan surrogate  → DQN A                     │
│              │                             Burst surrogate → DQN B                     │
│   ┌──────────┼──────────┐                  Hop surrogate   → DQN C                     │
│   ▼          ▼          ▼                         │                                   │
│ Scan      Burst        Hop                         ▼                                   │
│ pseudo-   pseudo-      pseudo-              DIFFERENT LEARNED                         │
│ unknown   unknown      unknown                SCORE SPACES                             │
│   │          │          │                         │                                   │
│   └──── threshold / band candidates ───┐          │ thresholds are not               │
│                                        │          │ directly interchangeable         │
│                                        ▼          │                                   │
│                              ALL CANDIDATES       │                                   │
│                                  COMPETE           │                                   │
│                                        │          │                                   │
│                                        ▼          │                                   │
│                              SELECT ONE RULE      │                                   │
│                                                                                        │
│ ────────────────────────────────────────────────────────────────────────────────────── │
│ FUTURE WORK — HOW DO WE COMBINE MULTIPLE SURROGATES IN DQNGUARD?                      │
│                                                                                        │
│ POOLED DQN                    DQN ENSEMBLE                 HYBRID GUARD                 │
│ A ─┐                          A → DQN A ─┐                 A ─┐                         │
│ B ─┼→ ONE DQN                 B → DQN B ─┼→ aggregate     B ─┼→ VarMax-style evidence │
│ C ─┘                          C → DQN C ─┘                 C ─┘       + ONE DQN         │
│                                                                                        │
│ GOAL: preserve DQNGuard's strong Unknown F1 / OSR F1 / 5% known-budget operating point│
│       while reducing dependence on a favorable single surrogate.                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

This is intentionally a denser slide than the rest of the deck. During final PowerPoint construction, use progressive emphasis or staged appearance if reliable so the audience sees:

1. VarMax surrogate-all;
2. architectural mismatch;
3. future architectures;

in sequence rather than all at once.

## Speaker script

See [SCRIPT.md](SCRIPT.md#slide-11--varmax-can-search-across-surrogates-dqnguard-must-learn-how-to-combine-them).

## Transition

End with:

> **“So the paper leaves us with both a working open-world detector and a concrete architectural question: how do we retain DQNGuard's operating-point advantage while learning from more than one kind of unknown?”**

Then move to the final takeaway slide.

## Terminology / claim constraints

- VarMax surrogate-all is a **multi-surrogate calibration search**, not an ensemble of deployed VarMax detectors.
- VarMax pseudo-unknown classes remain backbone-known classes; they are temporarily treated as open only in the calibration score subset.
- Current DQNGuard's surrogate is excluded from backbone training and affects **DQN fitting**.
- Do not describe different DQNGuard thresholds as directly transferable between separately fitted DQNs.
- Do not claim multi-surrogate DQNGuard has been implemented or evaluated.
- Pooled DQN, DQN ensemble, and hybrid guard designs are **candidate future architectures**.
- Preserve the explicit goal of retaining DQNGuard's strong thresholded performance and 5% known-rejection operating constraint.

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
