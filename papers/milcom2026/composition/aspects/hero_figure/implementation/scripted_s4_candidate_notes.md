> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../../../CONTEXT.md).

# Scripted Hero Figure Candidate S4

## Purpose

Candidate S4 is a horizontal-only refinement of S3.

## Changes from S3

1. Renamed panels:
   - RF Observation
   - Multi-Domain PA Backbone
   - DQNGuard
   - Decision Outputs and Consumers

2. Added an explicit model block:
   - PA CNN encoder
   - closed-set head

3. Reworked backbone flow:
   - OTA RF Window
   - Original IQ / FFT / DCT / Polar
   - fusion: concatenate + adaptive average pooling, N = 8192
   - PA CNN encoder
   - logits z, softmax p, feature h, predicted PA y-hat

4. Routed metric arrows to corresponding DQNGuard stages:
   - predicted PA y-hat goes to predicted-class calibration
   - z, p, and h go to guard evidence

5. Added subtle vertical cascade arrows inside DQNGuard while preserving numbered stages.

6. Added a light output panel to remove the floating-caption effect.

7. Changed the unknown branch from orange to a red/scarlet family.

8. Reduced PA Backbone dominance by adding a model block and tightening the layout.

## Next step

Review the generated PNG. If acceptable, insert the S4 PDF into the Methodology section and compile the paper for reader-level QA.
