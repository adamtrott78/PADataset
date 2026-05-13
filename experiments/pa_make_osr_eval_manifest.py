#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-leaderboard", required=True)
    ap.add_argument("--out", default="manifests/osr_eval_manifest.tsv")
    ap.add_argument("--gpus", default="0,1")
    ap.add_argument("--checkpoint", default="best_model")
    ap.add_argument("--modes", default="oracle,surrogate_all")
    ap.add_argument("--sweep-grid", choices=["smoke", "full"], default="smoke")
    ap.add_argument("--out-root", default="results_pa_osr_eval")
    args = ap.parse_args()

    df = pd.read_csv(args.train_leaderboard)
    gpus = [x.strip() for x in args.gpus.split(",") if x.strip()]
    if not gpus:
        raise ValueError("Need at least one GPU.")

    rows = []
    for i, row in df.iterrows():
        run_name = str(row["run_name"])
        run_dir = str(row["run_dir"])
        gpu = gpus[i % len(gpus)]
        out_dir = str(Path(args.out_root) / f"{run_name}__{args.checkpoint}__{args.sweep_grid}")

        rows.append({
            "run_name": run_name,
            "run_dir": run_dir,
            "checkpoint": args.checkpoint,
            "gpu": gpu,
            "modes": args.modes,
            "sweep_grid": args.sweep_grid,
            "out_dir": out_dir,
        })

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cfg_dir = out.parent / "configs" / out.stem
    cfg_dir.mkdir(parents=True, exist_ok=True)

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["run_name", "run_dir", "checkpoint", "gpu", "modes", "sweep_grid", "out_dir"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    print("Wrote manifest:", out)
    print("Rows:", len(rows))
    for r in rows[:20]:
        print(r)


if __name__ == "__main__":
    main()
