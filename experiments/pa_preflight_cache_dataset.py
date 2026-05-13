#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from experiments.pa_constants import DEFAULT_CACHE_ROOT, DATA_ROOT, PA_ALL
from prepData import DataSetup, build_data_from_setup


def precheck_cache(cache_root: Path, require_complete: bool = True) -> None:
    expected = {
        "PA1": 120,
        "PA2": 60,
        "PA3": 60,
        "PA4": 60,
        "PA8": 60,
    }

    print("=== CACHE PRECHECK ===")
    print("cache_root:", cache_root)

    counts = {}
    pa1 = sorted(cache_root.glob("*ota_core_high_run01__shard_*__PA1__part_*_of_02.h5"))
    counts["PA1"] = len(pa1)

    for pa in ["PA2", "PA3", "PA4", "PA8"]:
        counts[pa] = len(sorted(cache_root.glob(f"*ota_core_high_run01__shard_*__{pa}.h5")))

    for pa, n in counts.items():
        print(f"{pa}: {n} / expected {expected[pa]}")

    total = len(glob.glob(str(cache_root / "*.h5")))
    print("total h5:", total)

    if require_complete:
        bad = [pa for pa, n in counts.items() if n < expected[pa]]
        if bad:
            raise RuntimeError(f"Incomplete cache counts for: {bad}; counts={counts}")

    print("OK: cache precheck passed.")
    print()


def _close_dataset_bundle(data):
    try:
        ds = data.get("dataset")
        if hasattr(ds, "close"):
            ds.close()
    except Exception:
        pass


def smoke_dataset(data_root: Path, cache_root: Path, unknown_pa: str, full: bool) -> None:
    print("=== DATASET SMOKE CHECK ===")
    print("data_root:", data_root)

    unknowns = PA_ALL if full else [unknown_pa]

    for unk in unknowns:
        setup = DataSetup(
            root=str(data_root),
            task="pa",
            split_mode="open_pa",
            unknown_pas=(unk,),
            normalize=True,
            cache_len=16384,
            cache_root=str(cache_root),
            force_rebuild_cache=False,
            source_type="ota",
            source_name="ota_core_high_run01",
            dataset_tag="ota_core_high_run01",
            noise_tag="high_run01",
            open_val_frac=0.15,
            build_balanced_val_open=True,
            manifold_balance_seed=0,
        )

        data = build_data_from_setup(
            setup,
            batch_size=16,
            num_workers=0,
            pin_memory=True,
        )

        print(f"\nopen_pa unknown={unk}:")
        print(json.dumps(data["meta"], indent=2, default=str))
        _close_dataset_bundle(data)

    print("\nOK: dataset smoke complete.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(DATA_ROOT))
    ap.add_argument("--cache-root", default=str(DEFAULT_CACHE_ROOT))
    ap.add_argument("--unknown-pa", default="PA1")
    ap.add_argument("--full-smoke", action="store_true")
    ap.add_argument("--skip-dataset-smoke", action="store_true")
    ap.add_argument("--allow-incomplete-cache", action="store_true")
    args = ap.parse_args()

    data_root = Path(args.data_root).expanduser()
    cache_root = Path(args.cache_root).expanduser()

    precheck_cache(
        cache_root=cache_root,
        require_complete=not args.allow_incomplete_cache,
    )

    if not args.skip_dataset_smoke:
        smoke_dataset(
            data_root=data_root,
            cache_root=cache_root,
            unknown_pa=args.unknown_pa,
            full=args.full_smoke,
        )


if __name__ == "__main__":
    main()
