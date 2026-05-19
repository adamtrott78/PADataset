# Current Winning Configuration: Hero Figure

## Current decision

Use one combined hero figure rather than separate system and method figures.

## Intended role

The hero figure should show DQNGuard as the RF preliminary-action OSR layer that enables QR-CWoS evidence flow.

## Current structure

The figure should contain four grouped regions:

1. OTA RF observation
2. Backbone evidence
3. DQNGuard decision layer
4. Downstream consumers

## DQNGuard internal stages

1. Predicted-class conditional calibration
2. Variance/energy/gap guard evidence
3. Known-budget thresholding
4. Known PA or unknown behavior output

## Placement

Place near the beginning of Methodology, preferably page 2 or early page 3.

## Open questions for next CA round

1. How much backbone architecture should be shown?
2. Should DQNGuard be represented as a sequential cascade or as a centered decision block?
3. How should DQN-style confidence state and VarMax-style variance/energy evidence be visually combined?
4. Should downstream QR-CWoS/ATT&CK/LLM modules appear as full boxes or as a compact right-side context layer?
