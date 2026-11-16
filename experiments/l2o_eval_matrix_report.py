#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

PAS = ("PA1", "PA2", "PA3", "PA4", "PA8")
PAIR_SET = {(a, b) for a in PAS for b in PAS if a != b}


def _normalize_pair_frame(df: pd.DataFrame, *, metric: str) -> pd.DataFrame:
    if {"evaluation_target", "evaluation_surrogate", metric}.issubset(df.columns):
        out = df[["evaluation_target", "evaluation_surrogate", metric]].copy()
        out.columns = ["target", "surrogate", metric]
    elif {"target_unknown_pas", "surrogate_open_pa", metric}.issubset(df.columns):
        out = df[["target_unknown_pas", "surrogate_open_pa", metric]].copy()
        out.columns = ["target", "surrogate", metric]
        out["target"] = out["target"].astype(str).str.replace("[", "", regex=False).str.replace("]", "", regex=False).str.replace("'", "", regex=False).str.replace('"', "", regex=False).str.strip()
    elif {"target_name", "surrogate_name", metric}.issubset(df.columns):
        out = df[["target_name", "surrogate_name", metric]].copy()
        out.columns = ["target", "surrogate", metric]
    else:
        raise ValueError(f"unsupported pair table schema for metric {metric!r}")

    out["target"] = out["target"].astype(str)
    out["surrogate"] = out["surrogate"].astype(str)
    out[metric] = pd.to_numeric(out[metric], errors="raise")

    pairs = list(zip(out["target"], out["surrogate"]))
    if len(out) != 20:
        raise ValueError(f"pair table must contain exactly 20 rows, got {len(out)}")
    if len(set(pairs)) != 20:
        raise ValueError("pair table contains duplicate target/surrogate cells")
    if set(pairs) != PAIR_SET:
        missing = sorted(PAIR_SET - set(pairs))
        extra = sorted(set(pairs) - PAIR_SET)
        raise ValueError(f"pair table coverage mismatch; missing={missing}, extra={extra}")
    if not out[metric].between(0.0, 1.0).all():
        raise ValueError(f"{metric} contains values outside [0,1]")
    return out


def build_matrix_report(
    *,
    repaired_csv: Path,
    output_dir: Path,
    metric: str = "unknown_f1",
    baseline_csv: Path | None = None,
) -> Dict:
    repaired = _normalize_pair_frame(pd.read_csv(repaired_csv), metric=metric)
    output_dir.mkdir(parents=True, exist_ok=True)

    matrix = repaired.pivot(index="target", columns="surrogate", values=metric).reindex(index=PAS, columns=PAS)
    np.fill_diagonal(matrix.values, np.nan)
    matrix.to_csv(output_dir / f"{metric}_matrix.csv")

    target_rows = []
    for target in PAS:
        sub = repaired[repaired["target"] == target].sort_values(metric, ascending=False)
        best = sub.iloc[0]
        worst = sub.iloc[-1]
        target_rows.append({
            "target": target,
            "best_surrogate": best["surrogate"],
            f"best_{metric}": float(best[metric]),
            "worst_surrogate": worst["surrogate"],
            f"worst_{metric}": float(worst[metric]),
            f"mean_{metric}": float(sub[metric].mean()),
            f"std_{metric}": float(sub[metric].std(ddof=0)),
            f"range_{metric}": float(sub[metric].max() - sub[metric].min()),
        })
    target_df = pd.DataFrame(target_rows)
    target_df.to_csv(output_dir / f"{metric}_per_target.csv", index=False)

    report = {
        "schema": "padataset.l2o-directional-matrix-report.v1",
        "metric": metric,
        "cells": 20,
        "global": {
            f"mean_{metric}": float(repaired[metric].mean()),
            f"worst_{metric}": float(repaired[metric].min()),
            f"best_{metric}": float(repaired[metric].max()),
            f"std_{metric}": float(repaired[metric].std(ddof=0)),
        },
        "per_target": target_rows,
        "baseline_comparison": None,
    }

    if baseline_csv is not None:
        baseline = _normalize_pair_frame(pd.read_csv(baseline_csv), metric=metric)
        merged = repaired.merge(
            baseline,
            on=["target", "surrogate"],
            suffixes=("_repaired", "_baseline"),
            validate="one_to_one",
        )
        merged["delta"] = merged[f"{metric}_repaired"] - merged[f"{metric}_baseline"]
        merged.to_csv(output_dir / f"{metric}_repaired_vs_baseline.csv", index=False)

        delta_matrix = merged.pivot(index="target", columns="surrogate", values="delta").reindex(index=PAS, columns=PAS)
        np.fill_diagonal(delta_matrix.values, np.nan)
        delta_matrix.to_csv(output_dir / f"{metric}_delta_matrix.csv")

        report["baseline_comparison"] = {
            "mean_delta": float(merged["delta"].mean()),
            "median_delta": float(merged["delta"].median()),
            "worst_delta": float(merged["delta"].min()),
            "best_delta": float(merged["delta"].max()),
            "improved_cells": int((merged["delta"] > 0).sum()),
            "equal_cells": int((merged["delta"] == 0).sum()),
            "regressed_cells": int((merged["delta"] < 0).sum()),
        }

    (output_dir / "matrix_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repaired-csv", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--metric", default="unknown_f1")
    ap.add_argument("--baseline-csv", default=None)
    args = ap.parse_args()

    report = build_matrix_report(
        repaired_csv=Path(args.repaired_csv),
        output_dir=Path(args.output_dir),
        metric=args.metric,
        baseline_csv=None if args.baseline_csv is None else Path(args.baseline_csv),
    )
    print(json.dumps(report["global"], sort_keys=True))


if __name__ == "__main__":
    main()
