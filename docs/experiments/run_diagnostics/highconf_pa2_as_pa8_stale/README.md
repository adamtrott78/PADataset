# High-confidence PA2-as-PA8 impostor diagnostic

Diagnostic source run:

`results_pa_ota_primary/og_ref_ent005_lr2e4_unkPA2_c16384_seed0`

Checkpoint:

`best_model`

Purpose:

Export the top PA2 open-set samples that the closed-set backbone predicts as PA8 with highest softmax confidence.

Important caveat:

The montage visualizes the 8-channel cached model input tensor, not a human-readable IQ spectrogram. The y-axis is model input channel, and the x-axis is cached feature/time index.
