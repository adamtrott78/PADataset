# Current Winning Configuration: Hero Figure

## Current decision

Use one combined double-column hero figure rather than separate system and method figures.

## Intended role

The hero figure should show DQNGuard as the RF preliminary-action OSR sensing layer that enables QR-CWoS evidence flow.

## Figure type

Evidence-flow diagram.

Not a CNN architecture diagram.
Not a DQN training diagram.
Not a t-SNE or result visualization.
Not a response-policy diagram.

## Layout

Four grouped regions arranged left to right:

1. OTA RF observation
2. Backbone evidence
3. DQNGuard decision layer
4. Downstream consumers

## DQNGuard internal stages

1. Predicted-class conditional calibration
2. Guard evidence using confidence, variance, and energy
3. Known-budget thresholding
4. Known PA or unknown behavior output

## Backbone representation

Compress backbone details into one block:

    multi-domain RF representation
    logits z
    softmax p
    feature h
    predicted PA y-hat

The diagram may include a small IQ / FFT / DCT / polar strip, but should not show all Conv1D branches.

## DQNGuard evidence

Show:

    P1
    P1 - P2
    H
    V
    E
    r(x)
    tau_beta
    beta = 0.05

## Outputs

Known branch:

    Known PA evidence
    Scan / Burst / Sustain / Hop / Replay

Unknown branch:

    Unknown behavior pool
    candidate novel signal behavior

Downstream context:

    ATT&CK/EW precursor hypotheses
    LLM-assisted label-making
    QR-CWoS response planning

## Placement

Place near the beginning of Methodology, preferably page 2 or early page 3.

## Status

Round 001 established MILCOM placement and page-economy rules.
Round 002 established internal DQNGuard visual structure.
Next step: generate hero figure candidates using the visual specification, then rebuild the selected candidate as a publication-quality vector figure.
