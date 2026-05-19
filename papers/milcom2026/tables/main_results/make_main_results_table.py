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
    ("unknown_f1", "Unk. F1"),
    ("osr_macro_f1", "OSR F1"),
    ("unknown_auroc", "AUROC"),
]

METHOD_ORDER = {
    "DQNGuard_PA1_surrogate_knownonly_005": 0,
    "ShreyashCNN_DQNGuard_PA1_surrogate_005": 1,
    "VarMax_surrogate_all_smoke": 2,
}

METHOD_LABEL = {
    "DQNGuard_PA1_surrogate_knownonly_005": "DQNGuard",
    "ShreyashCNN_DQNGuard_PA1_surrogate_005": "Shreyash CNN head",
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
    lines.append(r"\begin{center}")
    lines.append(r"\refstepcounter{table}\label{tab:main_osr_results}")
    lines.append(r"{\footnotesize TABLE~\thetable}\\[-1pt]")
    lines.append(r"{\footnotesize\scshape Main OSR comparison under fixed PA1-surrogate known-budget calibration}\\[-2pt]")
    lines.append(r"{\scriptsize Values are mean $\pm$ standard deviation across held-out PA folds.}\\[2pt]")
    lines.append(r"\scriptsize")
    lines.append(r"\resizebox{\columnwidth}{!}{%")
    lines.append(r"\begin{tabular}{lcccc}")
    lines.append(r"\hline")
    lines.append(r"Method & Known rej. $\downarrow$ & Unk. F1 $\uparrow$ & OSR F1 $\uparrow$ & AUROC $\uparrow$ \\")
    lines.append(r"\hline")

    for _, row in summary.iterrows():
        vals = [fmt(row[f"{m}_mean"], row[f"{m}_std"]) for m, _ in METRICS]
        lines.append(
            f"{row['method']} & {vals[0]} & {vals[1]} & {vals[2]} & {vals[3]} \\\\"
        )

    lines.append(r"\hline")
    lines.append(r"\end{tabular}%")
    lines.append(r"}")
    lines.append(r"\end{center}")
    lines.append("")

    OUT_TEX.write_text("\n".join(lines))
    print(f"Wrote: {OUT_TEX}")
    print(f"Wrote: {OUT_CSV}")
    print(summary[["method", "folds"] + [f"{m}_mean" for m, _ in METRICS]].to_string(index=False))


if __name__ == "__main__":
    main()
