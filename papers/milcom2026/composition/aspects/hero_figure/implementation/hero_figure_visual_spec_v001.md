> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../../../CONTEXT.md).

# Hero Figure Visual Specification v001

## Purpose

Create the main hero figure for the MILCOM paper. The figure should show DQNGuard as the RF preliminary-action open-set recognition layer that produces known PA evidence or unknown behavior candidates for downstream QR-CWoS, ATT&CK/EW, and label-making systems.

## Canvas

Format: double-column IEEE figure.

Target width: 7.1 inches.

Target height: 2.3 to 2.7 inches.

Background: white.

Orientation: left-to-right flow.

Style: clean academic vector block diagram.

## Typography

Font family: Helvetica, Arial, or another clean sans-serif for figure labels.

Main group titles: 8.5 to 9 pt, bold.

Box labels: 7.5 to 8 pt.

Detail labels: 6.5 to 7 pt.

Math variables: italic math style where possible.

Caption: normal IEEE LaTeX caption, not embedded in image.

## Colors

Use a muted palette that still works in grayscale.

Input / observation: light gray fill, dark gray border.

Backbone: light slate or gray-blue fill.

DQNGuard: muted blue fill, strongest border.

Known output: muted green fill.

Unknown output: muted orange fill.

Downstream modules: pale purple or light gray-green fill.

Arrows: dark gray.

Decision threshold arrow or unknown path: orange accent.

No saturated neon colors. No gradients. No heavy shadows.

## Geometry

Use four large grouped regions arranged left to right.

Use rounded rectangles with consistent corner radius.

Use 0.6 to 0.8 pt borders.

Use 0.8 to 1.0 pt arrows.

DQNGuard should be 1.3x to 1.5x wider than the other blocks.

## Region 1: OTA RF observation

Main label:

    OTA RF Window

Small detail text:

    complex IQ window
    WiFi / Bluetooth / Zigbee

Do not include hardware details.

## Region 2: Backbone evidence

Group title:

    PA Backbone

Internal labels:

    multi-domain RF representation
    IQ / FFT / DCT / polar
    closed-set logits z
    softmax p
    feature h
    predicted PA y-hat

Do not show Conv1D layers or eight branches in detail.

## Region 3: DQNGuard

Group title:

    DQNGuard

Subtitle:

    budgeted open-set decision layer

Internal three-stage layout:

    1. Predicted-class calibration
       select bands for y-hat

    2. Guard evidence
       P1, P1 - P2, H
       variance V, energy E

    3. Known-budget threshold
       r(x) >= tau_beta
       beta = 0.05

Visual form:

Use three numbered sub-boxes stacked vertically or arranged left-to-right inside the DQNGuard group. The guard evidence sub-box should visually include both Tiwari-style confidence state and Trott-style variance/energy evidence.

## Region 4: Outputs and downstream use

Split into two output boxes:

    Known PA evidence
    Scan / Burst / Sustain / Hop / Replay

and

    Unknown behavior pool
    candidate novel signal behavior

Then show downstream consumers:

    ATT&CK/EW precursor hypotheses
    LLM-assisted label-making
    QR-CWoS response planning

The downstream consumers should be visually smaller than DQNGuard. They are context, not the main method.

## Explicit exclusions

Do not include RL replay memory.

Do not include epsilon-greedy exploration.

Do not include CNN layer tables.

Do not include t-SNE scatterplots.

Do not include full mathematical equations.

Do not include response-policy action choices.

Do not imply this paper evaluates the full QR-CWoS response loop.

## Image-generation prompt

Create a clean IEEE-style academic vector block diagram for a two-column MILCOM paper. The figure should be 7.1 inches wide and about 2.5 inches tall, white background, left-to-right flow, thin dark-gray arrows, rounded rectangles, muted colors, no shadows, no gradients.

The figure title inside the image should not be included; leave caption text outside the image.

The diagram has four grouped regions from left to right.

Region 1, light gray: "OTA RF Window". Small text: "complex IQ window" and "WiFi / Bluetooth / Zigbee".

Region 2, gray-blue: "PA Backbone". Show a compact multi-domain input strip labeled "IQ / FFT / DCT / polar", then outputs labeled "logits z", "softmax p", "feature h", and "predicted PA y-hat". Do not draw individual CNN layers.

Region 3, muted blue and visually central: "DQNGuard". Subtitle: "budgeted open-set decision layer". Inside this region show three numbered sub-boxes:
1. "Predicted-class calibration" with small text "select bands for y-hat".
2. "Guard evidence" with small text "P1, P1-P2, H" and "variance V, energy E".
3. "Known-budget threshold" with small text "r(x) >= tau_beta" and "beta = 0.05".
Make DQNGuard the largest central group.

Region 4: split into two output boxes. Green box: "Known PA evidence" with small text "Scan / Burst / Sustain / Hop / Replay". Orange box: "Unknown behavior pool" with small text "candidate novel signal behavior". From these outputs, draw smaller downstream boxes labeled "ATT&CK/EW precursor hypotheses", "LLM-assisted label-making", and "QR-CWoS response planning".

Use Helvetica or Arial-like sans-serif labels. Main labels should be readable at IEEE two-column scale. Use 8-9 pt equivalent for major labels and 6.5-7.5 pt equivalent for details. Keep all text horizontal. Align boxes cleanly. The figure should look like a polished technical systems diagram, not an infographic.
