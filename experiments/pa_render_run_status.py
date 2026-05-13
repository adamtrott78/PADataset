#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def fmt_time(sec):
    if sec is None:
        return "?"
    try:
        sec = max(0, int(float(sec)))
    except Exception:
        return "?"
    if sec >= 3600:
        return f"{sec // 3600:d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"
    return f"{sec // 60:02d}:{sec % 60:02d}"


def fmt_float(x, nd=4):
    if x is None:
        return "?"
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return "?"


def tqdm_line(progress, summary):
    if not progress:
        if summary:
            return "Epoch done: 100%|██████████| ?/? [?<00:00, ?it/s]"
        return "Epoch ?/?:   0%|          | 0/? [00:00<?, ?it/s]"

    phase = progress.get("phase", "?")
    epoch = int(progress.get("epoch", 0) or 0)
    epochs = int(progress.get("epochs", 0) or 0)
    step = int(progress.get("step", 0) or 0)
    steps = int(progress.get("steps", 0) or 0)
    pct = float(progress.get("pct", 0.0) or 0.0)
    sps = float(progress.get("steps_per_sec", 0.0) or 0.0)

    # If the run completed, older progress files may have sps=0 at epoch_done.
    if summary and phase == "epoch_done" and (sps <= 0 or step == 0):
        step = steps
        pct = 100.0

    bar_width = 10
    filled = max(0, min(bar_width, int(bar_width * pct / 100.0)))
    bar = "█" * filled + " " * (bar_width - filled)

    elapsed = None
    eta = None
    if sps > 0 and step > 0:
        elapsed = step / sps
        eta = max(0, steps - step) / sps

    if phase == "validation":
        return f"Epoch {epoch}/{epochs}: 100%|{'█' * bar_width}| {steps}/{steps} [{fmt_time(elapsed)}<?, ?it/s] validating"

    if phase == "epoch_done" or (summary and step == steps and steps > 0):
        speed = f"{sps:.2f}it/s" if sps > 0 else "?it/s"
        return f"Epoch {epoch}/{epochs}: 100%|{'█' * bar_width}| {steps}/{steps} [{fmt_time(elapsed)}<00:00, {speed}]"

    return f"Epoch {epoch}/{epochs}: {pct:3.0f}%|{bar}| {step}/{steps} [{fmt_time(elapsed)}<{fmt_time(eta)}, {sps:.2f}it/s]"


def metric_line(progress, summary):
    parts = []

    loss = None
    phase = "?"
    if progress:
        phase = progress.get("phase", "?")
        loss = progress.get("loss_so_far", progress.get("train_loss"))

    if loss is not None:
        parts.append(f"loss {fmt_float(loss)}")
    else:
        parts.append(f"phase {phase}")

    if summary:
        parts.append(f"best_ep {summary.get('best_epoch', '?')}")
        parts.append(f"val_acc {fmt_float(summary.get('best_val_acc'))}")
        parts.append(f"val_f1 {fmt_float(summary.get('best_val_macro_f1'))}")

        if "test_known_acc" in summary:
            parts.append(f"test_acc {fmt_float(summary.get('test_known_acc'))}")
        if "test_known_macro_f1" in summary:
            parts.append(f"test_f1 {fmt_float(summary.get('test_known_macro_f1'))}")
        if "test_dqn_proxy_expanded5" in summary:
            parts.append(f"proxy5 {fmt_float(summary.get('test_dqn_proxy_expanded5'))}")
    else:
        parts.append("val pending")

    parts.append("eval pending")
    return " | ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    progress = load_json(run_dir / "train_progress.json")
    summary = load_json(run_dir / "summary.json")

    print(tqdm_line(progress, summary))
    print(metric_line(progress, summary))


if __name__ == "__main__":
    main()
