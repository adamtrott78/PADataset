#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import h5py
import numpy as np
import torch

from prepData import (
    DataSetup,
    OPTIONAL_SAMPLE_META_KEYS,
    RawSourceRecord,
    _cache_file_name,
    _infer_x_layout,
    discover_raw_sources,
)
from experiments.pa_build_stft_track_cache import (
    FEATURE_MODE,
    stft_frequency_tracks,
)


def _load_iq_batch(
    Xds: h5py.Dataset,
    start: int,
    end: int,
    ch_axis: int,
    sample_axis: int,
    time_axis: int,
) -> np.ndarray:
    sl = [slice(None)] * 3
    sl[sample_axis] = slice(start, end)
    x = np.asarray(Xds[tuple(sl)], dtype=np.float32)
    x = np.transpose(x, (sample_axis, ch_axis, time_axis))
    if x.ndim != 3 or x.shape[1] != 2:
        raise ValueError(f"Expected batched IQ [B,2,W], got {x.shape}")
    return x


def stft_tracks_gpu(
    iq_batch: np.ndarray,
    *,
    frame_count: int,
    device: str,
) -> np.ndarray:
    """
    iq_batch: [B,2,W] float32
    returns [B,2,frame_count] float32:
      channel 0 spectral centroid in normalized frequency [-1,1]
      channel 1 spectral spread in [0,1]
    """
    if iq_batch.ndim != 3 or iq_batch.shape[1] != 2:
        raise ValueError(f"Expected [B,2,W], got {iq_batch.shape}")

    dev = torch.device(device)
    x = torch.from_numpy(np.ascontiguousarray(iq_batch)).to(dev, non_blocking=True)
    z = torch.complex(x[:, 0], x[:, 1])

    n = int(z.shape[-1])
    frame_len = n // int(frame_count)
    if frame_len < 8:
        raise ValueError(f"Signal too short for {frame_count} frames: n={n}")
    usable = frame_len * int(frame_count)
    frames = z[:, :usable].reshape(z.shape[0], int(frame_count), frame_len)

    # Match np.hanning used by the scalar reference path.
    window = torch.from_numpy(np.hanning(frame_len).astype(np.float32)).to(dev)
    spec = torch.fft.fft(frames * window.view(1, 1, -1), dim=-1)
    spec = torch.fft.fftshift(spec, dim=-1)

    power = spec.real.square() + spec.imag.square()
    power = power + torch.finfo(power.dtype).eps

    freq = (
        torch.arange(frame_len, device=dev, dtype=power.dtype)
        * (2.0 / float(frame_len))
        - 1.0
    )
    total = power.sum(dim=-1)
    centroid = (power * freq.view(1, 1, -1)).sum(dim=-1) / total
    spread = torch.sqrt(
        (
            power
            * (freq.view(1, 1, -1) - centroid.unsqueeze(-1)).square()
        ).sum(dim=-1)
        / total
    )

    tracks = torch.stack(
        [centroid.clamp(-1.0, 1.0), spread.clamp(0.0, 1.0)],
        dim=1,
    )
    return tracks.to(torch.float32).cpu().numpy()


def _make_virtual_cache(
    *,
    out_path: Path,
    base_path: Path,
    track_path: Path,
    n_samples: int,
    out_len: int,
    base_file: h5py.File,
    frame_count: int,
) -> None:
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()

    with h5py.File(tmp, "w", libver="latest") as fout:
        layout = h5py.VirtualLayout(shape=(n_samples, 8, out_len), dtype=np.float32)
        base_src = h5py.VirtualSource(
            str(base_path),
            "Xfeat",
            shape=(n_samples, 8, out_len),
        )
        track_src = h5py.VirtualSource(
            str(track_path),
            "Xtrack",
            shape=(n_samples, 2, out_len),
        )
        layout[:, 0:2, :] = base_src[:, 0:2, :]
        layout[:, 2:4, :] = track_src[:, :, :]
        layout[:, 4:8, :] = base_src[:, 4:8, :]
        fout.create_virtual_dataset("Xfeat", layout, fillvalue=np.float32(0.0))

        for key in ("y_pa", "proto", "y_joint"):
            fout.create_dataset(key, data=np.asarray(base_file[key]))

        for key in OPTIONAL_SAMPLE_META_KEYS:
            if key in base_file:
                fout.create_dataset(key, data=np.asarray(base_file[key]))

        for key, value in base_file.attrs.items():
            fout.attrs[key] = value

        fout.attrs["feature_mode"] = FEATURE_MODE
        fout.attrs["stft_frame_count"] = int(frame_count)
        fout.attrs["stft_track_0"] = "normalized_spectral_centroid"
        fout.attrs["stft_track_1"] = "normalized_spectral_spread"
        fout.attrs["legacy_base_cache"] = str(base_path)
        fout.attrs["stft_track_sidecar"] = str(track_path)
        fout.attrs["virtual_feature_cache"] = 1

    os.replace(tmp, out_path)


def _is_pa1_record(rec) -> bool:
    source_name = str(getattr(rec, "source_name", "") or "")
    dataset_tag = str(getattr(rec, "dataset_tag", "") or "")
    noise_tag = str(getattr(rec, "noise_tag", "") or "")
    raw_name = Path(rec.path).name
    path_parts = set(Path(rec.path).parts)
    return (
        source_name == "ota_pa1_run01"
        or dataset_tag == "ota_pa1_run01"
        or noise_tag == "pa1_run01"
        or "ota_pa1_run01" in path_parts
        or raw_name.startswith("ota_pa1_run01__")
    )


def _legacy_lookup_record(rec):
    if not _is_pa1_record(rec):
        return rec
    return RawSourceRecord(
        path=rec.path,
        protocol_name=rec.protocol_name,
        source_type="ota",
        source_name="ota_pa1_run01",
        dataset_tag="ota_pa1_run01",
        noise_tag="pa1_run01",
    )


def _resolve_legacy_base(
    rec,
    *,
    core_cache_root: Path,
    pa1_cache_root: Path,
) -> Path:
    is_pa1 = _is_pa1_record(rec)
    root = pa1_cache_root if is_pa1 else core_cache_root
    lookup_rec = _legacy_lookup_record(rec)
    path = root / _cache_file_name(lookup_rec)
    if not path.is_file():
        source_kind = "pa1" if is_pa1 else "core"
        raise FileNotFoundError(
            f"Matching {source_kind} legacy cache missing: {path}"
        )
    return path


def _probe(
    setup: DataSetup,
    *,
    base_cache_root: Path,
    pa1_base_cache_root: Path,
    frame_count: int,
    batch_size: int,
    device: str,
) -> None:
    records = discover_raw_sources(setup)
    if not records:
        raise RuntimeError("No raw OTA records discovered")

    rec = records[0]
    name = _cache_file_name(rec)
    base_path = _resolve_legacy_base(
        rec,
        core_cache_root=base_cache_root,
        pa1_cache_root=pa1_base_cache_root,
    )

    with h5py.File(rec.path, "r") as fin:
        Xds = fin["X"]
        ch_axis, sample_axis, time_axis = _infer_x_layout(tuple(Xds.shape))
        iq = _load_iq_batch(
            Xds, 0, min(int(batch_size), 2), ch_axis, sample_axis, time_axis
        )

    gpu = stft_tracks_gpu(
        iq,
        frame_count=int(frame_count),
        device=device,
    )
    cpu_centroid, cpu_spread = stft_frequency_tracks(
        iq[0, 0] + 1j * iq[0, 1],
        out_len=int(frame_count),
        frame_count=int(frame_count),
    )
    cpu = np.stack([cpu_centroid, cpu_spread], axis=0)
    max_abs_err = float(np.max(np.abs(gpu[0] - cpu)))
    if not np.isfinite(gpu).all():
        raise RuntimeError("GPU STFT probe produced non-finite values")
    if max_abs_err > 2e-4:
        raise RuntimeError(
            f"GPU/CPU STFT probe mismatch: max_abs_err={max_abs_err:.6g}"
        )

    print(
        json.dumps(
            {
                "probe": "PASS",
                "device": device,
                "source_records": len(records),
                "first_source": rec.path,
                "legacy_base_cache": str(base_path),
                "iq_batch_shape": list(iq.shape),
                "track_shape": list(gpu.shape),
                "frame_count": int(frame_count),
                "gpu_cpu_max_abs_error": max_abs_err,
            },
            indent=2,
            sort_keys=True,
        )
    )


def build(
    setup: DataSetup,
    *,
    base_cache_root: Path,
    frame_count: int,
    batch_size: int,
    device: str,
) -> dict:
    if setup.cache_root is None or setup.cache_len is None:
        raise ValueError("Explicit cache_root and finite cache_len are required")

    cache_root = Path(os.path.expanduser(setup.cache_root))
    cache_root.mkdir(parents=True, exist_ok=True)
    tracks_root = cache_root / "_stft_tracks"
    tracks_root.mkdir(parents=True, exist_ok=True)

    records = discover_raw_sources(setup)
    built = 0
    skipped = 0
    total_samples = 0

    if not torch.cuda.is_available() and device.startswith("cuda"):
        raise RuntimeError("CUDA requested but unavailable")

    for rec_i, rec in enumerate(records, start=1):
        name = _cache_file_name(rec)
        out_path = cache_root / name
        track_path = tracks_root / (name + ".tracks.h5")
        base_path = _resolve_legacy_base(
            rec,
            core_cache_root=base_cache_root,
            pa1_cache_root=pa1_base_cache_root,
        )

        if out_path.is_file() and track_path.is_file() and not setup.force_rebuild_cache:
            skipped += 1
            print(
                f"CACHE_FILE_SKIP | record={rec_i}/{len(records)} | path={out_path}",
                flush=True,
            )
            continue

        with h5py.File(rec.path, "r") as fin, h5py.File(base_path, "r") as base:
            Xds = fin["X"]
            xshape = tuple(Xds.shape)
            ch_axis, sample_axis, time_axis = _infer_x_layout(xshape)
            n_samples = int(xshape[sample_axis])
            out_len = int(setup.cache_len)

            expected = (n_samples, 8, out_len)
            if tuple(base["Xfeat"].shape) != expected:
                raise ValueError(
                    f"Legacy cache shape mismatch for {base_path}: "
                    f"got={tuple(base['Xfeat'].shape)} expected={expected}"
                )

            y_raw = np.asarray(fin["y"]).reshape(-1).astype(np.int64)
            proto_raw = np.asarray(fin["proto"]).reshape(-1).astype(np.int64)
            if not np.array_equal(y_raw, np.asarray(base["y_pa"]).reshape(-1)):
                raise ValueError(f"Raw/base y mismatch: {rec.path}")
            if not np.array_equal(proto_raw, np.asarray(base["proto"]).reshape(-1)):
                raise ValueError(f"Raw/base proto mismatch: {rec.path}")

            tmp_track = track_path.with_suffix(track_path.suffix + ".tmp")
            if tmp_track.exists():
                tmp_track.unlink()

            with h5py.File(tmp_track, "w") as tf:
                ds = tf.create_dataset(
                    "Xtrack",
                    shape=(n_samples, 2, out_len),
                    dtype="float32",
                    chunks=(1, 2, out_len),
                    compression="lzf",
                    shuffle=True,
                )
                tf.attrs["feature_mode"] = FEATURE_MODE
                tf.attrs["frame_count"] = int(frame_count)
                tf.attrs["source_path"] = rec.path
                tf.attrs["legacy_base_cache"] = str(base_path)

                for start in range(0, n_samples, int(batch_size)):
                    end = min(start + int(batch_size), n_samples)
                    iq = _load_iq_batch(
                        Xds, start, end, ch_axis, sample_axis, time_axis
                    )
                    tracks64 = stft_tracks_gpu(
                        iq,
                        frame_count=int(frame_count),
                        device=device,
                    )
                    if out_len % int(frame_count) == 0:
                        expanded = np.repeat(
                            tracks64,
                            out_len // int(frame_count),
                            axis=2,
                        )
                    else:
                        idx = np.floor(
                            np.arange(out_len, dtype=np.float64)
                            * (float(frame_count) / float(out_len))
                        ).astype(np.int64)
                        idx = np.minimum(idx, int(frame_count) - 1)
                        expanded = tracks64[:, :, idx]
                    ds[start:end] = expanded.astype(np.float32, copy=False)

                    print(
                        f"CACHE_BATCH | record={rec_i}/{len(records)} | "
                        f"sample={end}/{n_samples} | batch={end-start} | "
                        f"gpu={device}",
                        flush=True,
                    )

            os.replace(tmp_track, track_path)
            _make_virtual_cache(
                out_path=out_path,
                base_path=base_path,
                track_path=track_path,
                n_samples=n_samples,
                out_len=out_len,
                base_file=base,
                frame_count=int(frame_count),
            )

        built += 1
        total_samples += n_samples
        print(
            f"CACHE_FILE_DONE | record={rec_i}/{len(records)} | "
            f"path={out_path} | samples={n_samples}",
            flush=True,
        )

    manifest = {
        "schema": "padataset.stft-track-cache.v2",
        "feature_mode": FEATURE_MODE,
        "cache_root": str(cache_root),
        "legacy_base_cache_root": str(base_cache_root),
        "legacy_pa1_base_cache_root": str(pa1_base_cache_root),
        "cache_len": int(setup.cache_len),
        "frame_count": int(frame_count),
        "batch_size": int(batch_size),
        "device": device,
        "files_built": built,
        "files_skipped": skipped,
        "samples_built": total_samples,
        "source_records": len(records),
        "virtual_cache": True,
    }
    (cache_root / "stft_track_cache_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--cache-root", required=True)
    ap.add_argument("--base-cache-root", required=True)
    ap.add_argument("--pa1-base-cache-root", required=True)
    ap.add_argument("--cache-len", type=int, default=16384)
    ap.add_argument("--source-type", default="ota")
    ap.add_argument("--source-name", default="ota_core_high_run01")
    ap.add_argument("--dataset-tag", default="ota_core_high_run01")
    ap.add_argument("--noise-tag", default="high_run01")
    ap.add_argument("--frame-count", type=int, default=64)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--probe-only", action="store_true")
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
        dataset_tag=args.dataset_tag,
        noise_tag=args.noise_tag,
    )
    base_cache_root = Path(os.path.expanduser(args.base_cache_root))
    pa1_base_cache_root = Path(os.path.expanduser(args.pa1_base_cache_root))

    if args.probe_only:
        _probe(
            setup,
            base_cache_root=base_cache_root,
            pa1_base_cache_root=pa1_base_cache_root,
            frame_count=int(args.frame_count),
            batch_size=int(args.batch_size),
            device=args.device,
        )
        return

    build(
        setup,
        base_cache_root=base_cache_root,
        pa1_base_cache_root=pa1_base_cache_root,
        frame_count=int(args.frame_count),
        batch_size=int(args.batch_size),
        device=args.device,
    )


if __name__ == "__main__":
    main()
