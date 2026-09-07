> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../../../CONTEXT.md).

# Scripted Hero Figure Candidate S5

## Purpose

Candidate S5 is a layout and typography refinement of S4.

## Changes from S4

1. Renamed panels:
   - RF Signal Input
   - Multi-Domain PA Encoder
   - DQNGuard
   - Evidence Outputs and Consumers

2. Reordered backbone metrics:
   - predicted PA y-hat
   - logits z
   - softmax p
   - feature h

3. Routed predicted PA y-hat directly to the predicted-class calibration stage.

4. Routed z, p, and h directly to the guard-evidence stage.

5. Shortened transform labels:
   - IQ
   - FFT
   - DCT
   - Polar

6. Shortened fusion label:
   - Concat + AvgPool
   - N = 8192

7. Kept explicit PA CNN block:
   - PA CNN
   - encoder + head

8. Improved typography:
   - more formal sans-serif font stack;
   - less cartoonish heavy bold;
   - serif italic math classes for variables.

9. Strengthened the output panel visibility.

10. Preserved branch color semantics:
    - neutral upstream evidence arrows;
    - green known branch;
    - scarlet unknown branch.

## Next step

Review S5 PNG. If the standalone diagram is acceptable, insert the S5 PDF into the Methodology section and evaluate it in the compiled IEEE paper.
