#!/usr/bin/env python3
from pathlib import Path
import argparse
import csv
import json
import random
import sys

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from osr_core import load_backbone_run, _make_setup_from_config
from prepData import build_data_from_setup


def clean_scalar(v):
    if hasattr(v, "detach"):
        v = v.detach().cpu()
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    return v


def safe_meta_at(meta, i):
    if meta is None:
        return {}

    if isinstance(meta, (list, tuple)):
        try:
            return meta[i] or {}
        except Exception:
            return {}

    if isinstance(meta, dict):
        out = {}
        for k, v in meta.items():
            try:
                if hasattr(v, "__len__") and not isinstance(v, (str, bytes, dict)):
                    out[k] = clean_scalar(v[i])
                else:
                    out[k] = clean_scalar(v)
            except Exception:
                out[k] = str(v)
        return out

    return {"meta": str(meta)}


def get_loader(data, split):
    if split == "test_known":
        return data["test_known_loader"]
    if split == "test_open":
        return data["test_open_loader"]
    if split == "val_known":
        return data["val_loader"]
    if split == "val_open":
        return data["val_open_loader"]
    raise ValueError(f"Unsupported split: {split}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--checkpoint", default="best_model")
    ap.add_argument("--split", choices=["test_known", "test_open", "val_known", "val_open"], required=True)
    ap.add_argument("--selection", choices=["highconf_true_pa8_as_pa8", "random_true_pa2", "highconf_true_pa2_as_pa8"], required=True)
    ap.add_argument("--top-k", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    handle = load_backbone_run(args.run_dir, args.checkpoint, device=args.device)
    class_names = list(handle.class_names)

    cfg = dict(handle.config)
    setup = _make_setup_from_config(cfg, return_metadata=True)
    data = build_data_from_setup(
        setup,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=True,
    )

    loader = get_loader(data, args.split)

    model = handle.model
    model.eval()

    rows = []
    global_i = 0

    with torch.no_grad():
        for batch in loader:
            if len(batch) >= 3:
                x, y, meta = batch[:3]
            else:
                x, y = batch[:2]
                meta = None

            x_dev = x.to(args.device, non_blocking=True)
            logits = model(x_dev)
            probs = torch.softmax(logits, dim=1).detach().cpu().numpy()
            pred_idx = probs.argmax(axis=1)
            p1 = probs.max(axis=1)

            for i in range(len(x)):
                m = safe_meta_at(meta, i)
                pa_name = str(m.get("pa_name", ""))
                pred_name = class_names[int(pred_idx[i])]

                keep = False
                if args.selection == "highconf_true_pa8_as_pa8":
                    keep = (pa_name == "PA8" and pred_name == "PA8")
                elif args.selection == "random_true_pa2":
                    keep = (pa_name == "PA2")
                elif args.selection == "highconf_true_pa2_as_pa8":
                    keep = (pa_name == "PA2" and pred_name == "PA8")

                if keep:
                    rows.append({
                        "rank": None,
                        "p1": float(p1[i]),
                        "pred_name": pred_name,
                        "proto_name": m.get("proto_name"),
                        "pa_name": m.get("pa_name"),
                        "shard_id": m.get("shard_id"),
                        "source_id": m.get("source_id"),
                        "window_id": m.get("window_id"),
                        "record_id": m.get("record_id"),
                        "local_idx": m.get("local_idx"),
                        "dataset_index": m.get("dataset_index", global_i),
                        "cache_path": m.get("path"),
                    })

                global_i += 1

    if args.selection.startswith("highconf"):
        rows.sort(key=lambda r: r["p1"], reverse=True)
        rows = rows[:args.top_k]
    else:
        rng = random.Random(args.seed)
        rng.shuffle(rows)
        rows = rows[:args.top_k]

    for j, r in enumerate(rows, 1):
        r["rank"] = j

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise SystemExit("No rows matched selection.")

    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("Wrote:", out)
    print("Rows:", len(rows))
    for r in rows[:5]:
        print(r)


if __name__ == "__main__":
    main()
