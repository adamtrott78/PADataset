> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../../../CONTEXT.md).

# Scripted Hero Figure Candidate S3

## Purpose

Candidate S3 is a fine-tuning revision of S2, not a high-level comparative-analysis round.

## User-requested changes

1. Add four explicit transforms after OTA RF Window:
   - Original IQ
   - FFT
   - DCT
   - Polar

2. Route those four transforms into a fusion block:
   - concatenate
   - adaptive average pooling
   - N = 8192

3. Add four backbone outputs/metrics:
   - closed-set logits z
   - softmax p
   - feature h
   - predicted PA y-hat

4. Draw one arrow from each metric into DQNGuard.

5. Improve math notation styling for variables and equations.

6. Fix unknown behavior pool text overflow.

7. Make color semantics more intentional:
   - upstream evidence path is neutral;
   - DQNGuard is blue;
   - known output is green;
   - unknown output is gold;
   - only branch-specific post-decision arrows use branch colors.

8. Produce two variants:
   - horizontal double-column candidate
   - vertical candidate

## Files

Generator:

- papers/milcom2026/composition/aspects/hero_figure/implementation/generate_hero_figure_s3.py

Generated outputs:

- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s3_horizontal.svg
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s3_horizontal.pdf
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s3_horizontal.png
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s3_vertical.svg
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s3_vertical.pdf
- papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s3_vertical.png

## Next step

Compare horizontal and vertical S3 candidates visually. Select one as the basis for paper integration, then insert the selected PDF into the Methodology section.
