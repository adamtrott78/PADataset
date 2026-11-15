import numpy as np

from experiments.pa_build_stft_track_cache import stft_frequency_tracks
from experiments.pa_stft_track_diagnostic import trajectory_features


def _piecewise_tone(freqs, frame_len=256):
    chunks = []
    n = np.arange(frame_len, dtype=np.float64)
    for f in freqs:
        chunks.append(np.exp(2j * np.pi * float(f) * n))
    return np.concatenate(chunks).astype(np.complex64)


def test_stft_centroid_preserves_monotone_vs_revisit_structure():
    scan_freqs = [-0.30, -0.20, -0.10, 0.00, 0.10, 0.20, 0.30, 0.40]
    hop_freqs = [-0.25, 0.25, 0.00, -0.25, 0.25, 0.00, -0.25, 0.25]

    scan, scan_spread = stft_frequency_tracks(
        _piecewise_tone(scan_freqs), out_len=8, frame_count=8
    )
    hop, hop_spread = stft_frequency_tracks(
        _piecewise_tone(hop_freqs), out_len=8, frame_count=8
    )

    assert np.all(np.diff(scan) > 0)
    assert np.max(scan_spread) < 0.10
    assert np.max(hop_spread) < 0.10

    scan_features = trajectory_features(scan, scan_spread, quant_step=0.05)
    hop_features = trajectory_features(hop, hop_spread, quant_step=0.05)

    assert scan_features["revisit_fraction"] == 0.0
    assert scan_features["monotonic_fraction"] == 1.0
    assert hop_features["revisit_fraction"] > scan_features["revisit_fraction"]
    assert hop_features["direction_change_rate"] > scan_features["direction_change_rate"]
