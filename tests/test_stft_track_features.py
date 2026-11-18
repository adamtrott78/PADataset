from pathlib import Path

import h5py
import numpy as np

from experiments.pa_build_stft_track_cache import stft_frequency_tracks
from experiments.pa_build_stft_track_cache_gpu import (
    _build_legacy_cache_index,
    _resolve_legacy_base,
)
from prepData import RawSourceRecord
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


def test_legacy_cache_resolver_uses_stored_source_provenance(tmp_path):
    dedicated = tmp_path / "data" / "bluetooth" / "ota" / "ota_pa1_run01"
    core = tmp_path / "data" / "bluetooth" / "ota" / "ota_core_high_run01"
    dedicated.mkdir(parents=True)
    core.mkdir(parents=True)

    raw_real = dedicated / "ota_pa1_run01__shard_001__PA1.mat"
    raw_real.write_bytes(b"raw")
    raw_link = core / raw_real.name
    raw_link.symlink_to(raw_real)

    cache_root = tmp_path / "cache-pa1"
    cache_root.mkdir()
    cache_path = cache_root / "historical-name-does-not-matter.h5"
    with h5py.File(cache_path, "w") as fout:
        fout.attrs["source_path"] = str(raw_real)
        fout.attrs["protocol_name"] = "bluetooth"

    index = _build_legacy_cache_index(cache_root)
    rec = RawSourceRecord(
        path=str(raw_link),
        protocol_name="bluetooth",
        source_type="ota",
        source_name="ota_core_high_run01",
        dataset_tag="ota_core_high_run01",
        noise_tag="high_run01",
    )

    resolved = _resolve_legacy_base(rec, legacy_index=index)
    assert resolved.resolve() == cache_path.resolve()


def test_legacy_cache_resolver_prefers_exact_source_path(tmp_path):
    raw = tmp_path / "data" / "wifi" / "ota" / "ota_core_high_run01" / "core.mat"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"raw")

    cache_root = tmp_path / "cache-core"
    cache_root.mkdir()
    cache_path = cache_root / "arbitrary-cache-name.h5"
    with h5py.File(cache_path, "w") as fout:
        fout.attrs["source_path"] = str(raw)
        fout.attrs["protocol_name"] = "wifi"

    index = _build_legacy_cache_index(cache_root)
    rec = RawSourceRecord(
        path=str(raw),
        protocol_name="wifi",
        source_type="ota",
        source_name="ota_core_high_run01",
        dataset_tag="ota_core_high_run01",
        noise_tag="high_run01",
    )

    assert _resolve_legacy_base(rec, legacy_index=index).resolve() == cache_path.resolve()


def test_legacy_cache_resolver_uses_unique_basename_when_protocol_metadata_missing(tmp_path):
    raw = (
        tmp_path
        / "data"
        / "bluetooth"
        / "ota"
        / "ota_core_high_run01"
        / "ota_pa1_run01__shard_001__PA1.mat"
    )
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"raw")

    cache_root = tmp_path / "cache-pa1"
    cache_root.mkdir()
    cache_path = cache_root / "historical-pa1.h5"
    with h5py.File(cache_path, "w") as fout:
        fout.attrs["source_path"] = str(
            tmp_path
            / "legacy"
            / "ota_pa1_run01"
            / raw.name
        )

    index = _build_legacy_cache_index(cache_root)
    rec = RawSourceRecord(
        path=str(raw),
        protocol_name="bluetooth",
        source_type="ota",
        source_name="ota_core_high_run01",
        dataset_tag="ota_core_high_run01",
        noise_tag="high_run01",
    )

    assert _resolve_legacy_base(rec, legacy_index=index).resolve() == cache_path.resolve()


def test_legacy_cache_resolver_unique_basename_fails_closed_on_ambiguity(tmp_path):
    raw = (
        tmp_path
        / "data"
        / "bluetooth"
        / "ota"
        / "ota_core_high_run01"
        / "ota_pa1_run01__shard_001__PA1.mat"
    )
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"raw")

    cache_root = tmp_path / "cache"
    cache_root.mkdir()
    for i in (1, 2):
        cache_path = cache_root / f"historical-{i}.h5"
        with h5py.File(cache_path, "w") as fout:
            fout.attrs["source_path"] = str(
                tmp_path / f"legacy-{i}" / raw.name
            )

    index = _build_legacy_cache_index(cache_root)
    rec = RawSourceRecord(
        path=str(raw),
        protocol_name="bluetooth",
        source_type="ota",
        source_name="ota_core_high_run01",
        dataset_tag="ota_core_high_run01",
        noise_tag="high_run01",
    )

    import pytest

    with pytest.raises(RuntimeError, match="Ambiguous legacy cache provenance via unique basename"):
        _resolve_legacy_base(rec, legacy_index=index)
