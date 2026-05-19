# MILCOM Paper Composition Framework

This document defines the composition rules for the MILCOM 2026 paper. It combines lessons from the reference papers, our experiment evidence, and our target narrative.

## Paper spine

Every section should support this chain:

    QR-CWoS requires early trustworthy evidence.
    RF preliminary actions are early evidence.
    Closed-set RF classifiers fail on novel behaviors.
    DQNGuard provides budgeted OSR for known/unknown PAs.
    OTA experiments test whether this works.
    Target--Surrogate Matrix shows surrogate choice matters.
    Detected unknowns feed label-making and attack-chain prediction.

If a paragraph does not support one of these links, cut it or move it.

## Figure and table package

Target figure/table set:

    Figure 1: System pipeline / QR-CWoS evidence pipeline
    Figure 2: DQNGuard decision-layer diagram
    Figure 3: Target--Surrogate Matrix heatmap
    Table I: OTA dataset and capture setup
    Table II: Method comparison across calibration regimes
    Table III: Best/worst surrogate per target

If space is tight, merge Figure 1 and Figure 2 into one hero figure:

    RF window -> backbone -> DQNGuard -> known/unknown PA -> downstream QR-CWoS / label-making

## Paragraph design rules

IEEE two-column layout punishes long blocks.

Use:

    One paragraph = one claim.
    First sentence = claim.
    Middle = mechanism/evidence.
    Final sentence = why it matters.

Target paragraph length:

    80--140 words in source
    4--7 lines in PDF

Avoid paragraphs that mix motivation, method, result, and future work. Split them.

## Section blueprint

### Abstract

Write last. Structure:

    problem -> method -> dataset -> key results -> system implication

No citations.

### Introduction

Preserve the professor's QR-CWoS framing. End with compact contributions:

    1. formulate RF PA OSR as QR-CWoS sensing layer
    2. introduce DQNGuard
    3. evaluate OTA PA dataset
    4. analyze surrogate calibration and target-open calibration

### Related Work

Three compact paragraphs:

    1. Open-set recognition and varMax
    2. RF unknown-signal detection and multi-domain features
    3. DQN-IDS, attack-chain prediction, and label-making

Wei is used for representation precedent, not as a direct DQNGuard predecessor.
Baye/Broggi are used for varMax and confidence-based OSR.
Tiwari is used for DQN confidence-state OSR heads.
Trott RF VarMax is used for RF-domain varMax adaptation and class-conditioned variance/energy bands.

### Methodology

Use compact definitions and equations only where they clarify the decision rule.

Keep:

    closed-set logits
    DQN-IDS state
    DQNGuard class-conditioned bands
    known-budgeted threshold
    final decision rule

Avoid excessive implementation detail.

### Experimental Design

Keep as the ground-truth section:

    RQs
    OTA dataset and capture setup
    backbone training and splits
    calibration regimes
    metrics

### Results

Use the old RF VarMax paper's strongest writing style: explain mechanisms, not only numbers.

Suggested order:

    1. Method comparison: DQNGuard vs VarMax under Scan surrogate.
    2. Target--Surrogate Matrix: surrogate choice matters.
    3. Best/worst surrogate analysis: Scan broadly transfers, Sustain fails.
    4. Target-open calibration: how much target-open evidence recovers.
    5. Surrogate-selection heuristics failed: one sentence plus future work.

### Discussion

Tie back to the system:

    DQNGuard does not choose responses.
    It creates reliable PA/unknown evidence.
    Unknown detections populate the LLM label-making loop.
    Known PA sequences can feed attack-chain prediction.
    Surrogate selection remains a deployment challenge.

### Conclusion

Short, operational, and no new results.

## Figure rules

Use figures only when they change how the reader understands the method.

Good figures:

    pipeline diagrams
    heatmaps
    compact comparison plots
    feature/score distributions only when they explain a failure

Avoid:

    decorative architecture blocks
    too many per-fold bar charts
    dense screenshots
    multiple small plots with unreadable labels

## Table rules

Tables should be small enough to read in one column unless central to the paper.

Use three decimals for results:

    0.846
    0.833
    0.872

Use percentages only when the entire table is percent-based.

## Caption rules

Captions should say what the figure means, not only what it is.

Weak:

    Target--Surrogate Matrix.

Better:

    Target--Surrogate Matrix showing unknown F1 for each target unknown and surrogate-open calibration class. Surrogate choice changes unknown detection substantially, with Scan serving as the strongest overall surrogate.

## Source-specific lessons

| Source | Copy this | Do not copy this |
|---|---|---|
| Baye MILCOM varMax | Early conceptual OSR figure; method pipeline; bias-neutral framing | Too many separate result figures |
| Wei MILCOM DUNES | Clean system diagram; architecture/training tables; SNR/sample-size result logic | Heavy autoencoder/GAN equation density |
| Broggi HICSS varMax | Formal OSR definition; confidence calibration framing | Long literature-review density |
| Tiwari DQN-IDS | Confidence-state definition; algorithmic DQN explanation; compact performance/runtime tables | Overclaiming continual adaptation |
| Trott RF VarMax | Mechanistic fold explanations; RF-domain honesty; class-specific interpretation | Long paragraphs and repeated details |

## Non-negotiable narrative constraints

The QR-CWoS/window-of-superiority framing must remain. The correct claim is:

    This paper evaluates the RF OSR sensing layer that enables QR-CWoS, not the full response-policy loop.

The LLM label-making cycle should be framed as downstream:

    DQNGuard detects unknown signal behaviors.
    Detected unknowns form a candidate pool.
    LLM-assisted label-making can filter false positives and propose new semantic labels.
    The detector can later be updated with curated new classes.

The ATT&CK/EW link should be precursor-level:

    PAs are not direct ATT&CK technique labels.
    PAs are RF-observable precursor evidence for downstream ATT&CK/EW hypotheses.
