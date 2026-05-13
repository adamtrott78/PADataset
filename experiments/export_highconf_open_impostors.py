#!/usr/bin/env python3
from pathlib import Path
import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import torch

from osr_core import load_backbone_run, _make_setup_from_config
from prepData import build_data_from_setup


def safe_meta_at(meta, i):
    """Handle metadata returned as list/tuple, dict-of-lists, scalar dict, or None."""
    if meta is None:
        return None

    if isinstance(meta, (list, tuple)):
        try:
            return meta[i]
        except Exception:
            return None

    if isinstance(meta, dict):
        out = {}
        for k, v in meta.items():
            try:
                if hasattr(v, "__len__") and not isinstance(v, (str, bytes, dict)):
                    out[k] = v[i]
                else:
                    out[k] = v
            except Exception:
                out[k] = str(v)
        return out

    return str(meta)



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--checkpoint", default="best_model")
    ap.add_argument("--target-class", default="PA8")
    ap.add_argument("--top-k", type=int, default=24)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    handle = load_backbone_run(args.run_dir, args.checkpoint, device=args.device)
    class_names = list(handle.class_names)

    if args.target_class not in class_names:
        raise SystemExit(f"target class {args.target_class!r} not in class_names={class_names}")

    target_idx = class_names.index(args.target_class)

    cfg = dict(handle.config)
    setup = _make_setup_from_config(cfg, return_metadata=True)
    data = build_data_from_setup(
        setup,
        batch_size=args.batch_size,
        num_workers=0,
        pin_memory=True,
    )

    loader = data["test_open_loader"]
    model = handle.model
    model.eval()

    records = []
    sample_counter = 0

    with torch.no_grad():
        for batch in loader:
            if len(batch) == 3:
                x, y, meta = batch
            else:
                x, y = batch
                meta = [None] * len(x)

            x_dev = x.to(args.device, non_blocking=True)
            logits = model(x_dev)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            pred = probs.argmax(axis=1)
            p1 = probs.max(axis=1)

            x_np = x.cpu().numpy()

            for i in range(len(x_np)):
                if int(pred[i]) != target_idx:
                    sample_counter += 1
                    continue

                records.append({
                    "global_i": sample_counter,
                    "p1": float(p1[i]),
                    "pred_idx": int(pred[i]),
                    "pred_name": class_names[int(pred[i])],
                    "probs": probs[i].tolist(),
                    "x": x_np[i],
                    "meta": safe_meta_at(meta, i),
                })
                sample_counter += 1

    records.sort(key=lambda r: r["p1"], reverse=True)
    records = records[: args.top_k]

    summary = []
    for rank, r in enumerate(records, 1):
        x = r["x"]

        # Expected shape is [channels, time]. Make this robust anyway.
        arr = np.asarray(x)
        if arr.ndim == 1:
            img = arr[None, :]
        elif arr.ndim == 2:
            img = arr
        else:
            img = arr.reshape(arr.shape[0], -1)

        fig = plt.figure(figsize=(12, 4))
        plt.imshow(img, aspect="auto", interpolation="nearest")
        plt.colorbar(label="feature value")
        plt.title(
            f"rank={rank} true_open={handle.unknown_pas} pred={r['pred_name']} "
            f"p1={r['p1']:.5f} idx={r['global_i']}"
        )
        plt.xlabel("time / feature index")
        plt.ylabel("channel")
        plt.tight_layout()

        png = out_dir / f"rank_{rank:03d}_p1_{r['p1']:.5f}_pred_{r['pred_name']}.png"
        fig.savefig(png, dpi=160)
        plt.close(fig)

        item = {
            "rank": rank,
            "global_i": r["global_i"],
            "p1": r["p1"],
            "pred_name": r["pred_name"],
            "probs_by_class": dict(zip(class_names, r["probs"])),
            "png": str(png),
            "meta": r.get("meta"),
        }
        summary.append(item)

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

    print(f"Wrote {len(summary)} high-confidence open impostors to {out_dir}")
    for s in summary[:10]:
        print(s["rank"], s["pred_name"], f"p1={s['p1']:.5f}", s["png"])


if __name__ == "__main__":
    main()
