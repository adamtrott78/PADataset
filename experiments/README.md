# PADataset final experiment system

This directory is reserved for the replacement CNN/OSR experiment control plane.

Target design:
- manifest-driven training
- one run per worker process
- GPU-aware launch scripts
- artifact-verified completion
- dashboarded progress
- resumable sweeps
- post-run aggregation
- OSR evaluation from saved run artifacts

The old notebook UI has been moved to legacy/notebooks/pa_cnn_osr.

