#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[4]

OUTDIR = ROOT / "papers/milcom2026/figures/target_surrogate_matrix"
OUTDIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    ROOT / "results/target_surrogate_selection/ts_matrix_surrogate_selection_rules_full.csv",
    ROOT / "results/target_surrogate_selection/ruleD_confusion_route_alignment_full.csv",
    ROOT / "results/l2o_surrogate_selection/l2o_surrogate_selection_diagnostics.csv",
]

PA_NAME = {
    "PA1": "Scan",
    "PA2": "Burst",
    "PA3": "Sustain",
    "PA4": "Hop",
    "PA8": "Replay",
}


def clean_target(value: object) -> str:
    s = str(value).strip()
    if s.startswith("["):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list) and parsed:
                s = str(parsed[0])
        except Exception:
            pass
    s = s.strip().strip('"').strip("'")
    return PA_NAME.get(s, s)


def clean_surrogate(value: object) -> str:
    s = str(value).strip().strip('"').strip("'")
    return PA_NAME.get(s, s)


def load_matrix_source() -> pd.DataFrame:
    for path in CANDIDATES:
        if path.exists():
            df = pd.read_csv(path)
            print(f"Using source: {path}")
            return df
    raise FileNotFoundError(
        "No target-surrogate CSV found. Expected one of:\n"
        + "\n".join(str(p) for p in CANDIDATES)
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = set(df.columns)

    if {"target_name", "surrogate_name", "unknown_f1"}.issubset(cols):
        out = df[["target_name", "surrogate_name", "unknown_f1"]].copy()
        out.columns = ["target", "surrogate", "unknown_f1"]
        out["target"] = out["target"].map(clean_target)
        out["surrogate"] = out["surrogate"].map(clean_surrogate)
        return out

    if {"target_unknown_pas", "surrogate_open_pa", "unknown_f1"}.issubset(cols):
        out = df[["target_unknown_pas", "surrogate_open_pa", "unknown_f1"]].copy()
        out.columns = ["target", "surrogate", "unknown_f1"]
        out["target"] = out["target"].map(clean_target)
        out["surrogate"] = out["surrogate"].map(clean_surrogate)
        return out

    raise ValueError(
        "Could not recognize target/surrogate columns. Columns were:\n"
        + ", ".join(df.columns)
    )


def main() -> None:
    raw = load_matrix_source()
    df = normalize_columns(raw)

    class_order = ["Scan", "Burst", "Sustain", "Hop", "Replay"]
    present = sorted(set(df["target"]) | set(df["surrogate"]))
    order = [c for c in class_order if c in present] + [c for c in present if c not in class_order]

    mat = pd.DataFrame(np.nan, index=order, columns=order)
    for _, row in df.iterrows():
        mat.loc[row["target"], row["surrogate"]] = float(row["unknown_f1"])

    # Hide diagonal if present; target cannot be its own surrogate.
    for c in order:
        mat.loc[c, c] = np.nan

    fig, ax = plt.subplots(figsize=(3.45, 2.75))

    data = mat.to_numpy(dtype=float)
    masked = np.ma.masked_invalid(data)

    im = ax.imshow(masked, vmin=0.0, vmax=1.0, aspect="auto")

    ax.set_xticks(np.arange(len(order)))
    ax.set_yticks(np.arange(len(order)))
    ax.set_xticklabels(order, rotation=35, ha="right", fontsize=8)
    ax.set_yticklabels(order, fontsize=8)

    ax.set_xlabel("Surrogate-open calibration class", fontsize=8)
    ax.set_ylabel("Target unknown class", fontsize=8)
    ax.set_title("Target--Surrogate Unknown-F1 Transfer", fontsize=9, fontweight="bold")

    # Annotate cells and bold the best surrogate in each row.
    for i, target in enumerate(order):
        row_vals = mat.loc[target].dropna()
        best_col = row_vals.idxmax() if len(row_vals) else None
        for j, surrogate in enumerate(order):
            val = mat.iloc[i, j]
            if np.isnan(val):
                ax.text(j, i, "—", ha="center", va="center", fontsize=7)
            else:
                weight = "bold" if surrogate == best_col else "normal"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7, fontweight=weight)

    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    cbar.set_label("Unknown F1", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    ax.set_xticks(np.arange(-0.5, len(order), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(order), 1), minor=True)
    ax.grid(which="minor", linewidth=0.4)
    ax.tick_params(which="minor", bottom=False, left=False)

    fig.tight_layout(pad=0.2)

    pdf = OUTDIR / "target_surrogate_unknown_f1_matrix.pdf"
    png = OUTDIR / "target_surrogate_unknown_f1_matrix.png"
    csv = OUTDIR / "target_surrogate_unknown_f1_matrix.csv"

    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    mat.to_csv(csv)

    print(f"Wrote: {pdf}")
    print(f"Wrote: {png}")
    print(f"Wrote: {csv}")


if __name__ == "__main__":
    main()
