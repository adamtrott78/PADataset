#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from experiments.pa_constants import (
    DEFAULT_CACHE_ROOT,
    FAMILY_GRIDS,
    PAPER_SETS,
    base_training_config,
    split_csv,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="manifests/train_manifest.tsv")
    ap.add_argument("--grid", choices=sorted(FAMILY_GRIDS), default="baseline")
    ap.add_argument("--paper-sets", default="OG,DISTINCT,MASTER")
    ap.add_argument("--unknowns", default=None, help="Optional comma list; defaults to each PA in paper set.")
    ap.add_argument("--seeds", default="0")
    ap.add_argument("--gpus", default="0,1")
    ap.add_argument("--cache-root", default=str(DEFAULT_CACHE_ROOT))
    ap.add_argument("--save-root", default="results_pa_final")
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--num-workers", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--patience", type=int, default=None)
    ap.add_argument("--protocols", default="all", help="'all' or comma list such as wifi,bluetooth,zigbee")
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    cfg_dir = out.parent / "configs" / out.stem
    cfg_dir.mkdir(parents=True, exist_ok=True)

    paper_sets = split_csv(args.paper_sets)
    seeds = [int(x) for x in split_csv(args.seeds)]
    gpus = split_csv(args.gpus)
    if not gpus:
        raise ValueError("At least one GPU id must be provided.")

    protocols = None if args.protocols == "all" else split_csv(args.protocols)
    protocol_tag = "all" if protocols is None else "-".join(protocols)

    rows = []
    gpu_i = 0

    for paper_set in paper_sets:
        if paper_set not in PAPER_SETS:
            raise ValueError(f"Unknown paper_set={paper_set}; valid={sorted(PAPER_SETS)}")

        pas = PAPER_SETS[paper_set]
        unknowns = split_csv(args.unknowns) if args.unknowns else list(pas)

        for family in FAMILY_GRIDS[args.grid]:
            for unknown_pa in unknowns:
                if unknown_pa not in pas:
                    print(f"SKIP unknown {unknown_pa} not in {paper_set} PAs {pas}")
                    continue

                for seed in seeds:
                    gpu = gpus[gpu_i % len(gpus)]
                    gpu_i += 1

                    run_name = (
                        f"{paper_set.lower()}_"
                        f"{family['family_tag']}_"
                        f"unk{unknown_pa}_"
                        f"c16384_"
                        f"seed{seed}"
                    )
                    if protocol_tag != "all":
                        run_name = f"{protocol_tag}_{run_name}"

                    cfg = base_training_config(
                        run_name=run_name,
                        paper_set=paper_set,
                        pas=pas,
                        unknown_pa=unknown_pa,
                        family=family,
                        seed=seed,
                        cache_root=Path(args.cache_root).expanduser(),
                        save_root=args.save_root,
                        batch_size=args.batch_size,
                        protocols=protocols,
                        epochs_override=args.epochs,
                        patience_override=args.patience,
                        num_workers=args.num_workers,
                    )

                    cfg_path = cfg_dir / f"{run_name}.json"
                    cfg_path.write_text(json.dumps(cfg, indent=2))

                    rows.append({
                        "run_name": run_name,
                        "paper_set": paper_set,
                        "family_tag": family["family_tag"],
                        "unknown_pa": unknown_pa,
                        "seed": seed,
                        "gpu": gpu,
                        "cfg_path": str(cfg_path),
                        "save_root": args.save_root,
                    })

    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "run_name",
                "paper_set",
                "family_tag",
                "unknown_pa",
                "seed",
                "gpu",
                "cfg_path",
                "save_root",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    print("Wrote manifest:", out)
    print("Wrote configs:", cfg_dir)
    print("Rows:", len(rows))
    for row in rows[:20]:
        print(row)
    if len(rows) > 20:
        print(f"... {len(rows) - 20} more rows")


if __name__ == "__main__":
    main()
