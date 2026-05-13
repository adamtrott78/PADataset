#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", default="results_pa_osr_eval")
    ap.add_argument("--out", default="results/osr_leaderboard.csv")
    args = ap.parse_args()

    root = Path(args.results_root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    frames = []
    for p in sorted(root.glob("*/osr_summary.csv")):
        try:
            df = pd.read_csv(p)
            df["osr_summary_path"] = str(p)
            df["osr_run_dir"] = str(p.parent)
            frames.append(df)
        except Exception as e:
            frames.append(pd.DataFrame([{
                "osr_summary_path": str(p),
                "osr_run_dir": str(p.parent),
                "error": repr(e),
            }]))

    final = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    final.to_csv(out, index=False)

    print("Wrote:", out)
    print("Rows:", len(final))

    show = [
        "run_name",
        "method",
        "calibration_mode",
        "known_osr_macro_f1",
        "unknown_f1",
        "unknown_recall",
        "osr_macro_f1",
        "bias_delta",
        "no_feasible_solution",
        "best_top2_threshold",
        "best_var_percentiles",
        "best_energy_percentiles",
    ]
    cols = [c for c in show if c in final.columns]
    if len(final) and cols:
        print(final[cols].to_string(index=False))


if __name__ == "__main__":
    main()
