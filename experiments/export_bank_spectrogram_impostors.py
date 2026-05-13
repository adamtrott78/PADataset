#!/usr/bin/env python3
from pathlib import Path
import argparse
import csv
import json
import re
import sys

import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def clean_int(v):
    if v is None:
        return None
    if isinstance(v, (int, np.integer)):
        return int(v)
    s = str(v)
    m = re.fullmatch(r"tensor\(([-0-9]+)\)", s)
    if m:
        return int(m.group(1))
    return int(float(s))


def load_provenance(path):
    path = Path(path)
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        for k in ["rank", "shard_id", "local_idx", "record_id", "window_id"]:
            if r.get(k) not in [None, ""]:
                r[k] = clean_int(r[k])
        if r.get("p1") not in [None, ""]:
            r["p1"] = float(r["p1"])
    return rows


def source_path_from_cache(cache_path):
    with h5py.File(cache_path, "r") as f:
        src = f.attrs.get("source_path")
    if isinstance(src, bytes):
        src = src.decode("utf-8", errors="replace")
    return Path(str(src))


def read_bank_window(source_path, local_idx):
    with h5py.File(source_path, "r") as f:
        X = f["X"]
        idx = int(local_idx)

        # Raw OTA bank layout confirmed:
        # X = [time, IQ, window] = [400000, 2, 500]
        win = np.asarray(X[:, :, idx], dtype=np.float32)

        meta = {}
        for name in ["proto", "record_id", "shard_id", "source_id", "window_id", "y"]:
            if name in f:
                arr = np.asarray(f[name])
                if arr.ndim == 2 and arr.shape[0] == 1:
                    meta[name] = int(arr[0, idx])
                elif arr.ndim == 1:
                    meta[name] = int(arr[idx])
                else:
                    meta[name] = str(arr.shape)

    return win, meta


def win_to_complex(win):
    if win.ndim == 2 and win.shape[1] == 2:
        return (win[:, 0] + 1j * win[:, 1]).astype(np.complex64)
    if win.ndim == 2 and win.shape[0] == 2:
        return (win[0, :] + 1j * win[1, :]).astype(np.complex64)
    raise ValueError(f"Cannot convert window shape={win.shape} to complex IQ")


def plot_window(iq, out_png, title, fs):
    iq = np.asarray(iq, dtype=np.complex64).ravel()
    n = len(iq)
    t = np.arange(n) / float(fs)

    f, tt, S = signal.spectrogram(
        iq,
        fs=float(fs),
        window="hann",
        nperseg=2048,
        noverlap=1536,
        nfft=4096,
        return_onesided=False,
        mode="magnitude",
        scaling="spectrum",
    )

    f = np.fft.fftshift(f)
    S = np.fft.fftshift(S, axes=0)
    Sdb = 20.0 * np.log10(S + 1e-12)
    lo, hi = np.percentile(Sdb, [5, 99.5])
    Sdb = np.clip(Sdb, lo, hi)

    stride = max(1, n // 20000)
    ts = t[::stride] * 1e3
    iq_s = iq[::stride]

    fig = plt.figure(figsize=(13, 8))

    ax1 = fig.add_subplot(3, 1, 1)
    ax1.plot(ts, np.real(iq_s), linewidth=0.6, label="I")
    ax1.plot(ts, np.imag(iq_s), linewidth=0.6, label="Q")
    ax1.set_ylabel("I/Q")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    ax2 = fig.add_subplot(3, 1, 2)
    ax2.plot(ts, np.abs(iq_s), linewidth=0.7)
    ax2.set_ylabel("|IQ|")
    ax2.grid(True, alpha=0.3)

    ax3 = fig.add_subplot(3, 1, 3)
    im = ax3.imshow(
        Sdb,
        aspect="auto",
        origin="lower",
        extent=[tt[0] * 1e3, tt[-1] * 1e3, f[0] / 1e6, f[-1] / 1e6],
    )
    ax3.set_xlabel("Time (ms)")
    ax3.set_ylabel("Freq offset (MHz)")
    fig.colorbar(im, ax=ax3, label="dB")

    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(out_png, dpi=160)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provenance", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--top-k", type=int, default=12)
    ap.add_argument("--fs", type=float, default=12.5e6)
    args = ap.parse_args()

    rows = load_provenance(args.provenance)[: args.top_k]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    exported = []

    for r in rows:
        source_path = source_path_from_cache(r["cache_path"])
        win, source_meta = read_bank_window(source_path, r["local_idx"])
        iq = win_to_complex(win)

        out_png = out_dir / (
            f"rank_{int(r['rank']):03d}"
            f"_shard_{int(r['shard_id']):03d}"
            f"_idx_{int(r['local_idx']):03d}"
            f"_win_{int(r['window_id']):05d}"
            f"_p1_{float(r['p1']):.5f}.png"
        )

        title = (
            f"rank={r['rank']} true={r['proto_name']}:{r['pa_name']} "
            f"pred={r['pred_name']} p1={float(r['p1']):.5f} "
            f"shard={r['shard_id']} local_idx={r['local_idx']} window_id={r['window_id']}"
        )

        plot_window(iq, out_png, title, fs=args.fs)

        exported.append({
            **r,
            "source_path": str(source_path),
            "source_meta": source_meta,
            "window_shape": list(win.shape),
            "n_iq": int(len(iq)),
            "spectrogram_png": str(out_png),
        })

        print("WROTE", out_png)
        print("  source:", source_path)
        print("  shape:", win.shape, "meta:", source_meta)

    (out_dir / "exported.json").write_text(json.dumps(exported, indent=2))
    print("DONE:", out_dir)


if __name__ == "__main__":
    main()
