# Comparative Analysis Round 002: Tiwari DQN-IDS vs. Trott RF VarMax Model Diagrams

## Aspect

hero_figure

## Purpose

This round determines the internal visual logic of the hero figure. Round 001 established that the paper should use one combined hero figure placed early in the methodology. Round 002 determines what should appear inside that figure and how DQNGuard should be visually represented.

## References compared

1. Tiwari et al., DQN-IDS: A Deep Reinforcement Learning Approach for Open Set-Enabled Intrusion Detection.
2. Trott et al., Model Evaluation for Radio-Frequency Signal Modulation Classifiers in the Existence of Novel Samples.

## Core conclusion

The hero figure should not be a neural-network architecture diagram, a DQN training diagram, or a t-SNE/result visualization. It should be an evidence-flow diagram.

The winning structure is:

    OTA RF window
    -> multi-domain PA backbone
    -> DQNGuard decision layer
    -> known PA evidence or unknown behavior pool
    -> downstream ATT&CK/EW, LLM label-making, and QR-CWoS planning

Inside the DQNGuard box, show only the decision evidence:

    predicted-class calibration
    confidence / variance / energy guard evidence
    known-budgeted thresholding

Do not show Conv1D layers, DQN replay memory, epsilon-greedy training, t-SNE clusters, or full pseudocode.

## Tiwari DQN-IDS analysis

Tiwari's strongest visual is the DQN-IDS flowchart on page 4. It is simple, vertical, grayscale, and readable. It gives the conceptual chain:

    CNN training
    -> test softmax outputs
    -> extract features P1, P1 - P2, entropy H
    -> state = [P1, P1 - P2, H]
    -> DQN decision
    -> known or unknown

This is useful because it shows that a DQN-based OSR head can be visually communicated as a state-extraction and binary-decision layer, not as an RL textbook diagram.

The architecture table on the same page is useful, but not for the hero figure. It belongs in prose or a compact methods table if needed. The hero figure should not show Conv1D layer counts, kernel sizes, dropout values, or optimizer details.

Page 5 adds the algorithm box and confidence metric distributions. The algorithm box is too expensive for a six-page paper. The distributions are useful as evidence, but they are not hero-figure material. They tell us what the DQN consumes, not how the whole paper's system fits together.

### Tiwari-derived heuristics

T1. Represent the OSR head as a compact state/evidence extraction layer.

T2. Show the confidence state explicitly: P1, P1 - P2, H.

T3. Use a binary known/unknown output split.

T4. Avoid drawing DQN training machinery in the hero figure.

T5. Avoid algorithm boxes for the main method unless the algorithm itself is the paper's core visual object.

T6. Keep architecture details in a table or text, not in the hero figure.

## Trott RF VarMax analysis

The RF VarMax paper provides the missing RF-domain logic.

Page 2 shows that multi-domain RF feature design can be compressed into a table. The architecture details are important, but visually they are too dense for a hero figure. The hero figure should not show eight Conv1D branches in detail. Instead, it should summarize the backbone as:

    multi-domain RF representation
    -> PA backbone
    -> logits z, probabilities p, feature h

Page 4 is the most important visual source for DQNGuard. The score-spread figure shows variance and energy distributions grouped by predicted class. This is the key idea that became class-conditioned calibration: the expected score range depends on the predicted class, and unknowns can deviate above or below the known distribution.

The decision cascade below that figure is also important. It communicates the OSR style better than a generic model architecture would:

    top-2 confidence
    -> variance band
    -> energy band
    -> unknown if all checks fail

For DQNGuard, this becomes:

    predicted class
    -> class-conditioned guard bands
    -> aggregate unknown score
    -> known-budget threshold

Page 8, the t-SNE comparison, is valuable but not for the hero figure. It is a result/discussion visual style: it explains how representations separate or fail to separate unknowns. It should not be part of the hero figure.

### Trott-derived heuristics

R1. Treat the backbone as a compressed evidence generator, not as a full layer-by-layer architecture.

R2. Show multi-domain RF representation only as a compact upstream block.

R3. Make predicted-class conditional calibration visually explicit.

R4. Represent variance/energy evidence as guard bands or score evidence, not just as equations.

R5. Preserve the staged decision-cascade logic, but compress it into a diagram.

R6. Keep t-SNE and latent-space visuals for Results or Discussion, not the hero figure.

## Synthesis

Tiwari gives the confidence-state -> DQN decision -> known/unknown visual.

Trott gives the RF backbone -> class-conditioned variance/energy bands -> decision cascade visual.

DQNGuard should combine these as:

    Backbone evidence:
      z, p, h, predicted class

    DQNGuard evidence:
      confidence state: P1, P1 - P2, H
      guard evidence: variance V, energy E
      class-conditioned bands: bounds indexed by predicted class
      threshold: known-only budget beta = 0.05

    Output:
      known PA evidence
      unknown behavior pool

The hero figure should therefore be a single double-column figure with four grouped regions:

    1. OTA RF observation
    2. Backbone evidence
    3. DQNGuard
    4. Downstream consumers

DQNGuard should be the visual center.

## Updated winning configuration

One double-column vector figure.

One combined system + DQNGuard method diagram.

DQNGuard is the visual center.

Backbone is compressed.

DQN internals are compressed to confidence state/evidence.

VarMax inheritance appears as variance/energy guard evidence and class-conditioned bands.

Downstream QR-CWoS/ATT&CK/LLM modules appear as context, not as evaluated claims.
