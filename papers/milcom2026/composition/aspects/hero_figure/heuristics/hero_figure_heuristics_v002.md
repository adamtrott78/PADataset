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
