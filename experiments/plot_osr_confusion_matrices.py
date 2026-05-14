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

    # Try literal eval first for normal "[[1, 2], [3, 4]]" strings.
    try:
        arr = np.array(ast.literal_eval(s), dtype=int)
        if arr.ndim == 2:
            return arr
    except Exception:
        pass

    # Robust fallback for numpy-style strings like:
    # [[ 4214     0     0   286]
    #  [    0  4230     0   270]]
    nums = list(map(int, re.findall(r"-?\d+", s)))
    n = int(round(len(nums) ** 0.5))
    if n * n != len(nums):
        raise ValueError(f"Could not reshape confusion matrix with {len(nums)} numbers")
    return np.array(nums, dtype=int).reshape(n, n)


def parse_listish(x):
    if x is None or pd.isna(x):
        return None
    s = str(x).strip()
    if not s:
        return None
    try:
        return list(ast.literal_eval(s))
    except Exception:
        try:
            return list(json.loads(s))
        except Exception:
            return None


def target_name(row) -> str:
    for col in ["target_unknown_pas", "unknown_pas"]:
        if col in row and pd.notna(row[col]):
            vals = parse_listish(row[col])
            if vals:
                return str(vals[0])
            return str(row[col]).strip().replace('"', "").replace("[", "").replace("]", "")
    return "unknownPA"


def label_names(row, n: int):
    if "label_names_with_unknown" in row and pd.notna(row["label_names_with_unknown"]):
        vals = parse_listish(row["label_names_with_unknown"])
        if vals and len(vals) == n:
            return [str(v) for v in vals]

    if "class_names" in row and pd.notna(row["class_names"]):
        vals = parse_listish(row["class_names"])
        if vals and len(vals) == n - 1:
            return [str(v) for v in vals] + ["unknown"]

    return [f"class_{i}" for i in range(n - 1)] + ["unknown"]


def clean_filename(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(s)).strip("_")


def plot_confusion(cm: np.ndarray, labels: list[str], title: str, out_png: Path, normalize: bool):
    if normalize:
        denom = cm.sum(axis=1, keepdims=True)
        values = np.divide(cm, denom, out=np.zeros_like(cm, dtype=float), where=denom != 0)
        display = values
        number_fmt = "{:.1%}"
        suffix = "row-normalized"
    else:
        display = cm
        number_fmt = "{:d}"
        suffix = "counts"

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(display)

    ax.set_title(f"{title}\n{suffix}")
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_yticklabels(labels)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            if normalize:
                txt = number_fmt.format(display[i, j])
                raw = cm[i, j]
                ax.text(j, i, f"{txt}\n({raw})", ha="center", va="center", fontsize=8)
            else:
                ax.text(j, i, number_fmt.format(int(cm[i, j])), ha="center", va="center", fontsize=9)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-glob", required=True, help="Glob for osr_summary.csv files")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--select-best-per-target", action="store_true")
    ap.add_argument("--metric", default="osr_macro_f1")
    ap.add_argument("--title-prefix", default="DQNGuard PA1-surrogate known-only")
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

    if "target_unknown_pas" not in df.columns and "unknown_pas" in df.columns:
        df["target_unknown_pas"] = df["unknown_pas"]

    df["_target_pa"] = df.apply(target_name, axis=1)

    if args.select_best_per_target:
        if args.metric not in df.columns:
            raise SystemExit(f"Metric column not found: {args.metric}")
        df = (
            df.sort_values(args.metric, ascending=False)
              .groupby("_target_pa", dropna=False)
              .head(1)
              .sort_values("_target_pa")
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    made = []
    summary_rows = []

    for _, row in df.iterrows():
        cm = parse_matrix(row["osr_confusion_matrix"])
        labels = label_names(row, cm.shape[0])
        target = row["_target_pa"]
        run_name = row.get("run_name", "run")
        method = row.get("method", "method")

        title_bits = [
            args.title_prefix,
            f"unknown={target}",
            f"run={run_name}",
        ]
        for metric in ["known_reject_rate", "unknown_f1", "osr_macro_f1", "unknown_auroc"]:
            if metric in row and pd.notna(row[metric]):
                title_bits.append(f"{metric}={float(row[metric]):.4f}")

        title = " | ".join(title_bits)
        stem = clean_filename(f"{target}_{run_name}_{method}")

        raw_png = out_dir / f"confusion_{stem}_counts.png"
        norm_png = out_dir / f"confusion_{stem}_row_normalized.png"

        plot_confusion(cm, labels, title, raw_png, normalize=False)
        plot_confusion(cm, labels, title, norm_png, normalize=True)

        made.extend([raw_png, norm_png])

        summary_rows.append({
            "target_pa": target,
            "run_name": run_name,
            "method": method,
            "known_reject_rate": row.get("known_reject_rate"),
            "unknown_precision": row.get("unknown_precision"),
            "unknown_recall": row.get("unknown_recall"),
            "unknown_f1": row.get("unknown_f1"),
            "osr_acc": row.get("osr_acc"),
            "osr_macro_f1": row.get("osr_macro_f1"),
            "unknown_auroc": row.get("unknown_auroc"),
            "counts_png": str(raw_png),
            "row_normalized_png": str(norm_png),
            "source_file": row.get("source_file"),
        })

    summary = pd.DataFrame(summary_rows)
    summary_path = out_dir / "confusion_matrix_plot_summary.csv"
    summary.to_csv(summary_path, index=False)

    print("\nMade figures:")
    for p in made:
        print(p)

    print("\nSummary:")
    print(summary.to_string(index=False))
    print("\nWrote:", summary_path)


if __name__ == "__main__":
    main()
