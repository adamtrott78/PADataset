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
from experiments.pa_experiment_catalog import (
    FAMILY_CONFIGS,
    RUN_GROUPS,
    catalog_training_config_overrides,
    get_run_group,
    grid_name_to_family_names,
    list_run_groups,
)


def parse_int_csv(s: str) -> list[int]:
    return [int(x) for x in split_csv(s)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="manifests/train_manifest.tsv")
    ap.add_argument("--run-group", choices=list_run_groups(), default=None)
    ap.add_argument("--grid", choices=sorted(FAMILY_GRIDS), default="baseline")
    ap.add_argument("--paper-sets", default="OG,DISTINCT,MASTER")
    ap.add_argument("--unknowns", default=None, help="Optional comma list; defaults to each PA in paper set.")
    ap.add_argument("--families", default=None, help="Optional comma list overriding run-group/grid families.")
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

    if args.run_group is not None:
        group = get_run_group(args.run_group)
        if group.get("status") == "no_rerun":
            raise ValueError(
                f"run_group={args.run_group} is metadata-only and should not generate training runs."
            )

        args.paper_sets = ",".join(group["paper_sets"])
        args.save_root = group["output_root"]
        args.seeds = ",".join(str(x) for x in group.get("seeds", [0]))

        run_group_name = args.run_group
        source_profile_name = group["source_profile"]
        family_names = list(group["families"])
    else:
        run_group_name = f"grid_{args.grid}"
        source_profile_name = "ota_core_high_run01"
        family_names = grid_name_to_family_names(args.grid)

    if args.families:
        family_names = split_csv(args.families)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    cfg_dir = out.parent / "configs" / out.stem
    cfg_dir.mkdir(parents=True, exist_ok=True)

    paper_sets = split_csv(args.paper_sets)
    seeds = parse_int_csv(args.seeds)
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

        for family_name in family_names:
            if family_name == "top_selected":
                raise ValueError(
                    "family_name=top_selected must be resolved after primary results exist."
                )
            if family_name not in FAMILY_CONFIGS:
                raise ValueError(
                    f"Unknown family_name={family_name}; valid={sorted(FAMILY_CONFIGS)}"
                )

            family = FAMILY_CONFIGS[family_name]

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

                    cfg.update(
                        catalog_training_config_overrides(
                            source_profile_name=source_profile_name,
                            family_name=family_name,
                        )
                    )
                    cfg["run_group"] = run_group_name

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
