#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def normalize_cell(x):
    if isinstance(x, (list, dict)):
        return json.dumps(x, sort_keys=True)
    return x


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-root", default="results_pa_final")
    ap.add_argument("--out", default="results/final_train_leaderboard.csv")
    args = ap.parse_args()

    results_root = Path(args.results_root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for p in sorted(results_root.glob("*/summary.json")):
        try:
            row = json.loads(p.read_text())
            row["summary_path"] = str(p)
            row["run_dir"] = str(p.parent)
            rows.append(row)
        except Exception as e:
            rows.append({
                "summary_path": str(p),
                "run_dir": str(p.parent),
                "error": repr(e),
            })

    df = pd.DataFrame(rows)
    for col in df.columns:
        df[col] = df[col].map(normalize_cell)

    df.to_csv(out, index=False)
    print("Wrote:", out)
    print("Rows:", len(df))

    if len(df):
        sort_cols = [
            "paper_set",
            "family_tag",
            "unknown_pas",
            "seed",
            "best_val_dqn_proxy_expanded5",
            "test_dqn_proxy_expanded5",
            "test_known_macro_f1",
        ]
        shown = [c for c in sort_cols if c in df.columns]
        print(df[shown].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
