#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import math
import pandas as pd


ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "results/og_method_comparison/og_dqnguard_vs_varmax_vs_shreyash_full.csv"
OUTDIR = ROOT / "papers/milcom2026/tables/main_results"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUT_TEX = OUTDIR / "main_osr_results_table.tex"
OUT_CSV = OUTDIR / "main_osr_results_table_summary.csv"

METRICS = [
    ("known_reject_rate", "Known rej."),
    ("unknown_f1", "Unknown F1"),
    ("osr_macro_f1", "OSR macro F1"),
    ("unknown_auroc", "AUROC"),
]

METHOD_ORDER = {
    "DQNGuard_PA1_surrogate_knownonly_005": 0,
    "ShreyashCNN_DQNGuard_PA1_surrogate_005": 1,
    "VarMax_surrogate_all_smoke": 2,
}

METHOD_LABEL = {
    "DQNGuard_PA1_surrogate_knownonly_005": "DQNGuard",
    "ShreyashCNN_DQNGuard_PA1_surrogate_005": "Shreyash CNN + DQNGuard head",
    "VarMax_surrogate_all_smoke": "VarMax surrogate-all",
}


def fmt(mean: float, std: float) -> str:
    if pd.isna(mean):
        return "--"
    if pd.isna(std) or math.isclose(float(std), 0.0, abs_tol=1e-12):
        return f"{mean:.3f}"
    return f"{mean:.3f} $\\pm$ {std:.3f}"


def main() -> None:
    df = pd.read_csv(SRC)

    required = {"comparison_method", *[m for m, _ in METRICS]}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    rows = []
    for key, sub in df.groupby("comparison_method", dropna=False):
        rec = {
            "comparison_method": key,
            "method": METHOD_LABEL.get(key, key.replace("_", "\\_")),
            "folds": len(sub),
            "order": METHOD_ORDER.get(key, 99),
        }
        for m, _ in METRICS:
            rec[f"{m}_mean"] = sub[m].mean()
            rec[f"{m}_std"] = sub[m].std(ddof=1)
        rows.append(rec)

    summary = pd.DataFrame(rows).sort_values("order")
    summary.to_csv(OUT_CSV, index=False)

    lines = []
    lines.append(r"\begin{table}[t]")
    lines.append(r"\centering")
    lines.append(r"\caption{Main open-set recognition comparison under fixed PA1-surrogate known-budget calibration. Values are mean $\pm$ standard deviation across held-out preliminary-action folds.}")
    lines.append(r"\label{tab:main_osr_results}")
    lines.append(r"\scriptsize")
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(r"\begin{tabular}{lcccc}")
    lines.append(r"\hline")
    lines.append(r"Method & Known rej. $\downarrow$ & Unknown F1 $\uparrow$ & OSR macro F1 $\uparrow$ & AUROC $\uparrow$ \\")
    lines.append(r"\hline")

    for _, row in summary.iterrows():
        vals = [fmt(row[f"{m}_mean"], row[f"{m}_std"]) for m, _ in METRICS]
        lines.append(
            f"{row['method']} & {vals[0]} & {vals[1]} & {vals[2]} & {vals[3]} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")
    lines.append("")

    OUT_TEX.write_text("\n".join(lines))

    print(f"Wrote: {OUT_TEX}")
    print(f"Wrote: {OUT_CSV}")
    print(summary[["method", "folds"] + [f"{m}_mean" for m, _ in METRICS]].to_string(index=False))


if __name__ == "__main__":
    main()
