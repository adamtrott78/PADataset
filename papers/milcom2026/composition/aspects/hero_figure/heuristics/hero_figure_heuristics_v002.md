> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../../../CONTEXT.md).

# Hero Figure Heuristics v002

## Role of the figure

The hero figure is an evidence-flow diagram. It is not a neural-network architecture figure, not a DQN training figure, and not a results visualization.

## Primary structure

Use one double-column vector figure with four grouped regions:

1. OTA RF observation
2. Backbone evidence
3. DQNGuard decision layer
4. Downstream consumers

## DQNGuard structure

DQNGuard should be the visual center. Show three internal stages:

1. Predicted-class calibration
2. Guard evidence
3. Known-budget thresholding

## Evidence to show

Show the following evidence variables in compact form:

    P1
    P1 - P2
    H
    variance V
    energy E
    r(x)
    tau_beta
    beta = 0.05

## Evidence to avoid

Do not show:

    replay memory
    epsilon-greedy exploration
    DQN training episodes
    full CNN layer architecture
    t-SNE clusters
    full equations
    QR-CWoS response-policy actions

## Backbone rule

Compress the backbone into a single evidence-generator block. It may show:

    IQ / FFT / DCT / polar
    logits z
    softmax p
    feature h
    predicted PA y-hat

Do not draw all convolutional branches.

## Output rule

Use a binary output split:

    Known PA evidence
    Unknown behavior pool

Then show downstream modules as context:

    ATT&CK/EW precursor hypotheses
    LLM-assisted label-making
    QR-CWoS response planning

## Caption rule

The caption must explain that DQNGuard is the RF OSR sensing layer that produces known PA evidence or unknown behavior candidates for downstream systems. It must not claim that the figure implements or evaluates the full QR-CWoS response loop.

## Preserved source-specific observations

These observations were extracted from the retired composition-framework and
nested hero-analysis drafts at pre-modularization commit
`077c8d9466e1a4e70bb8163560e4b52e108cef92`. They are the project's historical
readings, not a new verification of the source papers or mandatory page rules.

| Source | Useful transferable observation | Boundary |
|---|---|---|
| Baye MILCOM varMax | Introduce OSR concepts and a high-level method flow before metric-heavy results; explain the operating comparison clearly | Do not inherit its number of separate figures |
| Wei MILCOM multi-domain work | Group a self-contained system diagram consistently; use compact architecture/training tables to carry detailed parameters | Its autoencoder/GAN architecture and equation density are not DQNGuard requirements |
| Broggi HICSS varMax | Use precise OSR definitions and confidence-calibration framing | Do not import a long literature-review structure into a short paper |
| Tiwari DQN-IDS | Define confidence states clearly and explain an algorithm with compact performance/runtime evidence | Do not imply deployment-time continual adaptation without an experiment |
| Trott RF VarMax | Explain fold behavior mechanistically and retain RF-specific claim boundaries | Avoid repeated details and long mixed-purpose paragraphs |

The old winning-config document's useful requirements are retained above:
compressed backbone evidence, three DQNGuard stages, a known/unknown output split,
5% budget notation, and downstream precursor-level reasoning. Its “next candidate”
status is obsolete; active graphics are selected by main.tex.

The nested draft's page-1 prohibition and page-2 placement rule were local layout
choices. Place the figure where readers need its explanatory role and verify the
compiled layout. Captions should explain the evidence flow and scientific scope.
Parameter tables can free diagram space; select visuals that reduce ambiguity
rather than mechanically copying the old figure/table package or word counts.
