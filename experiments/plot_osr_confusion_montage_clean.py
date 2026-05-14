#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def parse_matrix(x) -> np.ndarray:
    s = str(x).strip()
    try:
        arr = np.array(ast.literal_eval(s), dtype=int)
        if arr.ndim == 2:
            return arr
    except Exception:
        pass

    nums = list(map(int, re.findall(r"-?\d+", s)))
    n = int(round(len(nums) ** 0.5))
    if n * n != len(nums):
        raise ValueError(f"Could not reshape confusion matrix with {len(nums)} values")
    return np.array(nums, dtype=int).reshape(n, n)


def parse_listish(x):
    if x is None or pd.isna(x):
        return None
    s = str(x).strip()
    try:
        return list(ast.literal_eval(s))
    except Exception:
        try:
            return list(json.loads(s))
        except Exception:
            return None


def get_target(row) -> str:
    for col in ["target_unknown_pas", "unknown_pas"]:
        if col in row and pd.notna(row[col]):
            vals = parse_listish(row[col])
            if vals:
                return str(vals[0])
            return str(row[col]).replace("[", "").replace("]", "").replace('"', "")
    return "unknown"


def get_labels(row, n):
    if "label_names_with_unknown" in row and pd.notna(row["label_names_with_unknown"]):
        vals = parse_listish(row["label_names_with_unknown"])
        if vals and len(vals) == n:
            return [str(v) for v in vals]

    if "class_names" in row and pd.notna(row["class_names"]):
        vals = parse_listish(row["class_names"])
        if vals and len(vals) == n - 1:
            return [str(v) for v in vals] + ["unknown"]

    return [f"class_{i}" for i in range(n - 1)] + ["unknown"]


def row_normalize(cm):
    denom = cm.sum(axis=1, keepdims=True)
    return np.divide(cm, denom, out=np.zeros_like(cm, dtype=float), where=denom != 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-glob", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--out-name", default="paper_confusion_montage_clean.png")
    ap.add_argument("--metric", default="osr_macro_f1")
    args = ap.parse_args()

    paths = sorted(Path(".").glob(args.input_glob))
    if not paths:
        raise SystemExit(f"No files matched: {args.input_glob}")

    rows = []
    for p in paths:
        df = pd.read_csv(p)
        df["source_file"] = str(p)
        rows.append(df)

    df = pd.concat(rows, ignore_index=True)
    df["_target"] = df.apply(get_target, axis=1)

    # Pick best row per unknown PA if multiple runs exist.
    df = (
        df.sort_values(args.metric, ascending=False)
          .groupby("_target", dropna=False)
          .head(1)
          .copy()
    )

    order = {"PA2": 0, "PA3": 1, "PA4": 2, "PA8": 3}
    df["_order"] = df["_target"].map(lambda x: order.get(str(x), 999))
    df = df.sort_values("_order")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    axes = axes.ravel()

    summary = []

    for ax_i, (_, row) in enumerate(df.iterrows()):
        ax = axes[ax_i]
        cm = parse_matrix(row["osr_confusion_matrix"])
        norm = row_normalize(cm)
        labels = get_labels(row, cm.shape[0])
        target = row["_target"]

        im = ax.imshow(norm, vmin=0.0, vmax=1.0)

        ax.set_title(f"Unknown {target}", fontsize=13, pad=8)
        ax.set_xlabel("Predicted", fontsize=10)
        ax.set_ylabel("True", fontsize=10)

        ax.set_xticks(np.arange(len(labels)))
        ax.set_yticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9)
        ax.set_yticklabels(labels, fontsize=9)

        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                pct = norm[i, j] * 100.0
                count = cm[i, j]
                text = f"{pct:.1f}%\n{count}"
                ax.text(j, i, text, ha="center", va="center", fontsize=8)

        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

        summary.append({
            "target": target,
            "run_name": row.get("run_name"),
            "method": row.get("method"),
            "known_reject_rate": row.get("known_reject_rate"),
            "unknown_precision": row.get("unknown_precision"),
            "unknown_recall": row.get("unknown_recall"),
            "unknown_f1": row.get("unknown_f1"),
            "osr_acc": row.get("osr_acc"),
            "osr_macro_f1": row.get("osr_macro_f1"),
            "unknown_auroc": row.get("unknown_auroc"),
            "source_file": row.get("source_file"),
        })

    # Hide unused axes if fewer than 4.
    for k in range(len(df), len(axes)):
        axes[k].axis("off")

    fig.suptitle("DQNGuard PA1-Surrogate Known-Only OSR, Budget = 0.05", fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    out_png = out_dir / args.out_name
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    summary_path = out_dir / "paper_confusion_montage_clean_summary.csv"
    pd.DataFrame(summary).to_csv(summary_path, index=False)

    print("Wrote:", out_png)
    print("Wrote:", summary_path)
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    main()
