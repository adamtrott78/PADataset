#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import h5py
import numpy as np
import torch
import torch.nn.functional as F
from scipy.fftpack import dct

from prepData import (
    DataSetup,
    OPTIONAL_SAMPLE_META_KEYS,
    _cache_file_name,
    _infer_x_layout,
    _load_iq_sample_from_h5,
    discover_raw_sources,
    joint_label,
)


FEATURE_MODE = "stft_tracks64_v1"


def _pool_1d(x: np.ndarray, out_len: int) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[None, :]
    if x.shape[-1] == out_len:
        return x.astype(np.float32, copy=False)
    xt = torch.from_numpy(x[None, ...])
    with torch.no_grad():
        yt = F.adaptive_avg_pool1d(xt, out_len)
    return yt[0].cpu().numpy().astype(np.float32, copy=False)


def _nearest_expand(values: np.ndarray, out_len: int) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32).reshape(-1)
    if values.size == 1:
        return np.full(out_len, float(values[0]), dtype=np.float32)
    idx = np.floor(np.arange(out_len, dtype=np.float64) * values.size / out_len).astype(np.int64)
    idx = np.minimum(idx, values.size - 1)
    return values[idx].astype(np.float32, copy=False)


def stft_frequency_tracks(complex_signal: np.ndarray, out_len: int, frame_count: int = 64) -> tuple[np.ndarray, np.ndarray]:
    """
    Lightweight STFT summary with non-overlapping frames.

    Returns two 1-D tracks of length out_len:
      1) normalized spectral centroid in [-1, 1]
      2) normalized spectral spread in [0, 1]

    The transform intentionally replaces the legacy global FFT real/imag pair
    while preserving the overall 8 x L feature tensor shape.
    """
    z = np.asarray(complex_signal, dtype=np.complex64).reshape(-1)
    n = int(z.size)
    if n < frame_count * 8:
        raise ValueError(f"Signal too short for {frame_count} STFT frames: n={n}")

    frame_len = n // frame_count
    usable = frame_len * frame_count
    frames = z[:usable].reshape(frame_count, frame_len)

    window = np.hanning(frame_len).astype(np.float32)
    spec = np.fft.fftshift(np.fft.fft(frames * window[None, :], axis=1), axes=1)
    power = (spec.real * spec.real + spec.imag * spec.imag).astype(np.float64)
    power += np.finfo(np.float64).eps

    freq = np.linspace(-1.0, 1.0, frame_len, endpoint=False, dtype=np.float64)
    total = power.sum(axis=1)
    centroid = (power * freq[None, :]).sum(axis=1) / total
    spread = np.sqrt(
        (power * (freq[None, :] - centroid[:, None]) ** 2).sum(axis=1) / total
    )

    centroid = np.clip(centroid, -1.0, 1.0).astype(np.float32)
    spread = np.clip(spread, 0.0, 1.0).astype(np.float32)

    return _nearest_expand(centroid, out_len), _nearest_expand(spread, out_len)


def compute_stft_track_feature_stack(
    iq: np.ndarray,
    out_len: int,
    normalize: bool = True,
    frame_count: int = 64,
) -> np.ndarray:
    """
    iq: [2, W]
    returns [8, out_len]:
      [I, Q, STFT-centroid-track, STFT-spread-track, DCT-I, DCT-Q, magnitude, phase]

    This preserves the legacy eight-branch model interface. Only the two
    legacy FFT real/imag channels are replaced.
    """
    if iq.ndim != 2 or iq.shape[0] != 2:
        raise ValueError(f"Expected iq shape [2, W], got {iq.shape}")

    xt = iq.astype(np.float32, copy=True)
    complex_signal = xt[0] + 1j * xt[1]

    centroid, spread = stft_frequency_tracks(complex_signal, out_len, frame_count=frame_count)

    xc0 = dct(xt[0], type=2, norm="ortho")
    xc1 = dct(xt[1], type=2, norm="ortho")
    xc = np.stack([xc0, xc1], axis=0).astype(np.float32)

    magnitude = np.abs(complex_signal).astype(np.float32)
    phase = np.angle(complex_signal).astype(np.float32)
    polar = np.stack([magnitude, phase], axis=0).astype(np.float32)

    if normalize:
        xt = np.tanh(xt)
        xc = np.tanh(xc)
        polar[0] = np.tanh(polar[0])
        polar[1] = np.sin(polar[1])

    xt = _pool_1d(xt, out_len)
    xc = _pool_1d(xc, out_len)
    polar = _pool_1d(polar, out_len)

    tf = np.stack([centroid, spread], axis=0).astype(np.float32)
    return np.vstack((xt, tf, xc, polar)).astype(np.float32)


def build_cache(setup: DataSetup, frame_count: int) -> dict:
    if setup.cache_root is None:
        raise ValueError("Explicit cache_root is required for STFT-track cache build")
    if setup.cache_len is None:
        raise ValueError("Finite cache_len is required for STFT-track cache build")

    cache_root = Path(os.path.expanduser(setup.cache_root))
    cache_root.mkdir(parents=True, exist_ok=True)
    raw_records = discover_raw_sources(setup)

    built = 0
    skipped = 0
    samples = 0

    for rec in raw_records:
        cache_path = cache_root / _cache_file_name(rec)
        if cache_path.is_file() and not setup.force_rebuild_cache:
            skipped += 1
            continue

        with h5py.File(rec.path, "r") as fin:
            if "X" not in fin or "y" not in fin or "proto" not in fin:
                raise KeyError(f"{rec.path} is missing one of required keys: X, y, proto")

            Xds = fin["X"]
            y = np.array(fin["y"]).reshape(-1).astype(np.int64)
            proto = np.array(fin["proto"]).reshape(-1).astype(np.int64)
            xshape = tuple(Xds.shape)
            ch_axis, sample_axis, time_axis = _infer_x_layout(xshape)
            n_samples = xshape[sample_axis]

            if n_samples != len(y) or n_samples != len(proto):
                raise ValueError(
                    f"Mismatch in {rec.path}: X.shape={xshape}, len(y)={len(y)}, len(proto)={len(proto)}"
                )

            first_iq = _load_iq_sample_from_h5(Xds, 0, ch_axis, sample_axis, time_axis)
            first_feat = compute_stft_track_feature_stack(
                first_iq,
                out_len=int(setup.cache_len),
                normalize=setup.normalize,
                frame_count=frame_count,
            )

            tmp_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
            if tmp_path.exists():
                tmp_path.unlink()

            with h5py.File(tmp_path, "w") as fout:
                fout.create_dataset(
                    "Xfeat",
                    shape=(n_samples, 8, int(setup.cache_len)),
                    dtype="float32",
                    chunks=(1, 8, int(setup.cache_len)),
                )
                fout.create_dataset("y_pa", data=y.astype(np.int64))
                fout.create_dataset("proto", data=proto.astype(np.int64))
                fout.create_dataset(
                    "y_joint",
                    data=np.array(
                        [joint_label(int(proto[i]), int(y[i])) for i in range(n_samples)],
                        dtype=np.int64,
                    ),
                )

                fout.attrs["source_path"] = rec.path
                fout.attrs["protocol_name"] = rec.protocol_name
                fout.attrs["source_type"] = rec.source_type
                fout.attrs["source_name"] = rec.source_name
                fout.attrs["dataset_tag"] = "" if rec.dataset_tag is None else str(rec.dataset_tag)
                fout.attrs["noise_tag"] = "" if rec.noise_tag is None else str(rec.noise_tag)
                fout.attrs["normalize"] = int(setup.normalize)
                fout.attrs["cache_len"] = int(setup.cache_len)
                fout.attrs["feature_mode"] = FEATURE_MODE
                fout.attrs["stft_frame_count"] = int(frame_count)
                fout.attrs["stft_track_0"] = "normalized_spectral_centroid"
                fout.attrs["stft_track_1"] = "normalized_spectral_spread"

                for key in OPTIONAL_SAMPLE_META_KEYS:
                    if key in fin:
                        arr = np.array(fin[key]).reshape(-1)
                        if len(arr) == n_samples:
                            fout.create_dataset(key, data=arr)

                fout["Xfeat"][0] = first_feat
                for i in range(1, n_samples):
                    iq = _load_iq_sample_from_h5(Xds, i, ch_axis, sample_axis, time_axis)
                    fout["Xfeat"][i] = compute_stft_track_feature_stack(
                        iq,
                        out_len=int(setup.cache_len),
                        normalize=setup.normalize,
                        frame_count=frame_count,
                    )

            os.replace(tmp_path, cache_path)
            built += 1
            samples += n_samples
            print(
                f"CACHE_FILE_DONE | path={cache_path} | samples={n_samples} | "
                f"feature_mode={FEATURE_MODE} | frames={frame_count}",
                flush=True,
            )

    manifest = {
        "schema": "padataset.stft-track-cache.v1",
        "feature_mode": FEATURE_MODE,
        "cache_root": str(cache_root),
        "cache_len": int(setup.cache_len),
        "frame_count": int(frame_count),
        "source_type": setup.source_type,
        "source_name": setup.source_name,
        "dataset_tag": setup.dataset_tag,
        "noise_tag": setup.noise_tag,
        "files_built": built,
        "files_skipped": skipped,
        "samples_built": samples,
    }
    (cache_root / "stft_track_cache_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--cache-root", required=True)
    ap.add_argument("--cache-len", type=int, default=16384)
    ap.add_argument("--source-type", default="ota")
    ap.add_argument("--source-name", default="ota_core_high_run01")
    ap.add_argument("--dataset-tag", default="ota_core_high_run01")
    ap.add_argument("--noise-tag", default="high_run01")
    ap.add_argument("--manifest-path", default=None)
    ap.add_argument("--source-glob", default=None)
    ap.add_argument("--frame-count", type=int, default=64)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--probe-only", action="store_true", help="Validate source discovery and one real STFT transform, then exit.")
    args = ap.parse_args()

    setup = DataSetup(
        root=os.path.expanduser(args.data_root),
        task="pa",
        split_mode="closed",
        normalize=True,
        cache_len=int(args.cache_len),
        cache_root=os.path.expanduser(args.cache_root),
        force_rebuild_cache=bool(args.force),
        source_type=args.source_type,
        source_name=args.source_name,
        source_glob=args.source_glob,
        manifest_path=os.path.expanduser(args.manifest_path) if args.manifest_path else None,
        dataset_tag=args.dataset_tag,
        noise_tag=args.noise_tag,
    )
    if args.probe_only:
        records = discover_raw_sources(setup)
        if not records:
            raise RuntimeError("No raw OTA source records discovered")
        rec = records[0]
        with h5py.File(rec.path, "r") as fin:
            Xds = fin["X"]
            xshape = tuple(Xds.shape)
            ch_axis, sample_axis, time_axis = _infer_x_layout(xshape)
            iq = _load_iq_sample_from_h5(Xds, 0, ch_axis, sample_axis, time_axis)
            feat = compute_stft_track_feature_stack(
                iq,
                out_len=int(setup.cache_len),
                normalize=setup.normalize,
                frame_count=int(args.frame_count),
            )
        if feat.shape != (8, int(setup.cache_len)):
            raise RuntimeError(f"Unexpected STFT feature shape: {feat.shape}")
        if not np.isfinite(feat).all():
            raise RuntimeError("Non-finite values in STFT feature probe")
        print(json.dumps({
            "probe": "PASS",
            "source_records": len(records),
            "first_source": rec.path,
            "raw_iq_shape": list(iq.shape),
            "feature_shape": list(feat.shape),
            "feature_mode": FEATURE_MODE,
            "frame_count": int(args.frame_count),
        }, indent=2, sort_keys=True))
        return

    result = build_cache(setup, frame_count=int(args.frame_count))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
