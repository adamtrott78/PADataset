#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


OUT_DIR = Path("docs/experiments")
RUN_CSV = OUT_DIR / "legacy_run_inventory.csv"
CKPT_CSV = OUT_DIR / "legacy_checkpoint_inventory.csv"
TABLE_CSV = OUT_DIR / "legacy_generated_table_inventory.csv"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def norm_str(x):
    if pd.isna(x):
        return ""
    return str(x)


def parse_unknown_pas(x):
    s = norm_str(x)
    if not s:
        return []
    try:
        v = json.loads(s)
        if isinstance(v, list):
            return [str(a) for a in v]
    except Exception:
        pass
    return re.findall(r"PA\d+", s)


def infer_family(row):
    fam = norm_str(row.get("family_tag", ""))
    if fam:
        return fam

    rn = norm_str(row.get("run_name", ""))
    low = rn.lower()

    # Known historical backbone labels.
    known = [
        "ref_base_ent005",
        "ref_base_lr2e4",
        "ref_pms_drop040",
        "confman_baseline_knownonly",
        "confman_baseline_openconf",
        "confman_refined",
        "ota_btzb",
    ]
    for k in known:
        if k in low:
            return k

    # Older cache/baseline encoding.
    m = re.search(r"(c\d+_bs\d+_lr[^_]+(?:_lc[^_]+)?(?:_wd[^_]+)?)", rn)
    if m:
        return m.group(1)

    return ""


def score_cols(df):
    preferred = [
        "test_dqn_proxy_expanded5",
        "best_val_dqn_proxy_expanded5",
        "test_known_macro_f1",
        "best_val_macro_f1",
        "test_energy_auroc",
    ]
    return [c for c in preferred if c in df.columns]



def df_to_markdown_simple(df: pd.DataFrame) -> str:
    """Dependency-free Markdown table renderer."""
    if df is None or df.empty:
        return "- No rows."

    df = df.copy()
    df = df.fillna("")
    cols = list(df.columns)

    def cell(x):
        text = str(x)
        text = text.replace("\n", " ").replace("|", "\\|")
        return text

    rows = []
    rows.append("| " + " | ".join(cols) + " |")
    rows.append("| " + " | ".join(["---"] * len(cols)) + " |")

    for _, row in df.iterrows():
        rows.append("| " + " | ".join(cell(row[c]) for c in cols) + " |")

    return "\n".join(rows)


def top_table(df, cols, sort_col, n=20):
    if df.empty or sort_col not in df.columns:
        return pd.DataFrame()
    tmp = df.copy()
    tmp[sort_col] = pd.to_numeric(tmp[sort_col], errors="coerce")
    return tmp.sort_values(sort_col, ascending=False, na_position="last")[cols].head(n)


def main():
    run = read_csv(RUN_CSV)
    ckpt = read_csv(CKPT_CSV)
    tables = read_csv(TABLE_CSV)

    if run.empty:
        raise SystemExit(f"Missing or empty {RUN_CSV}")

    run["unknown_fold"] = run.get("unknown_pas", "").map(lambda x: ",".join(parse_unknown_pas(x)))
    run["inferred_family"] = run.apply(infer_family, axis=1)

    for c in [
        "test_dqn_proxy_expanded5",
        "best_val_dqn_proxy_expanded5",
        "test_known_macro_f1",
        "best_val_macro_f1",
        "test_known_acc",
        "best_val_acc",
    ]:
        if c in run:
            run[c] = pd.to_numeric(run[c], errors="coerce")

    # The old digital-noisy profile.
    digital = run[
        (run.get("source_type", "").fillna("") == "digital")
        & (run.get("source_name", "").fillna("") == "pilot_noisy_torch")
    ].copy()

    digital_complete = digital[digital.get("has_summary", False) == True].copy()
    digital_missing = digital[digital.get("has_summary", False) != True].copy()

    # Useful subsets.
    conf = digital[digital["result_root"].fillna("").str.contains("confmanifold", na=False)].copy()
    osr_bank = digital[digital["result_root"].fillna("").str.contains("osr_bank", na=False)].copy()
    baseline = run[run["result_root"].fillna("").isin(["results_pa_baseline", "results_pa_cache_sweep"])].copy()

    # Save machine-readable slices.
    digital.to_csv(OUT_DIR / "legacy_digital_noisy_runs.csv", index=False)
    digital_complete.to_csv(OUT_DIR / "legacy_digital_noisy_complete_runs.csv", index=False)
    digital_missing.to_csv(OUT_DIR / "legacy_digital_noisy_missing_summaries.csv", index=False)

    top_cols = [
        "result_root",
        "run_name",
        "inferred_family",
        "unknown_fold",
        "cache_len",
        "batch_size",
        "epochs",
        "seed",
        "lr",
        "label_smoothing",
        "entropy_loss_weight",
        "mlp_dropout",
        "early_stopping_mode",
        "open_conf_selection_metric",
        "best_epoch",
        "best_val_dqn_proxy_expanded5",
        "test_dqn_proxy_expanded5",
        "test_known_macro_f1",
        "test_known_acc",
        "summary_path",
    ]
    top_cols = [c for c in top_cols if c in run.columns]

    if "test_dqn_proxy_expanded5" in digital_complete:
        top_proxy = top_table(digital_complete, top_cols, "test_dqn_proxy_expanded5", 50)
        top_proxy.to_csv(OUT_DIR / "legacy_top_digital_by_proxy5.csv", index=False)

    if "test_known_macro_f1" in digital_complete:
        top_f1 = top_table(digital_complete, top_cols, "test_known_macro_f1", 50)
        top_f1.to_csv(OUT_DIR / "legacy_top_digital_by_known_f1.csv", index=False)

    # Group summaries.
    lines = []
    lines.append("# Legacy Digital-Noisy Experiment Reconstruction")
    lines.append("")
    lines.append("This report is generated from local metadata inventories only. It does not include raw checkpoints, tensors, H5 cache contents, or MAT files.")
    lines.append("")
    lines.append("## Inventory counts")
    lines.append("")
    lines.append(f"- Total inventoried run dirs: {len(run)}")
    lines.append(f"- Digital `pilot_noisy_torch` run dirs: {len(digital)}")
    lines.append(f"- Digital complete summaries: {len(digital_complete)}")
    lines.append(f"- Digital missing summaries: {len(digital_missing)}")
    lines.append(f"- Checkpoint metadata rows: {len(ckpt)}")
    lines.append(f"- Generated table rows: {len(tables)}")
    lines.append("")

    lines.append("## Result roots")
    lines.append("")
    vc = run["result_root"].value_counts(dropna=False)
    for k, v in vc.items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")

    lines.append("## Digital-noisy result roots")
    lines.append("")
    if len(digital):
        vc = digital["result_root"].value_counts(dropna=False)
        for k, v in vc.items():
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- No digital `pilot_noisy_torch` rows found.")
    lines.append("")

    lines.append("## Unknown folds observed in digital-noisy runs")
    lines.append("")
    if len(digital):
        vc = digital["unknown_fold"].replace("", "(none)").value_counts(dropna=False)
        for k, v in vc.items():
            lines.append(f"- `{k}`: {v}")
    lines.append("")

    lines.append("## Inferred backbone/family labels")
    lines.append("")
    vc = digital["inferred_family"].replace("", "(unlabeled)").value_counts(dropna=False)
    for k, v in vc.head(50).items():
        lines.append(f"- `{k}`: {v}")
    lines.append("")

    lines.append("## Top digital-noisy rows by deployable proxy5")
    lines.append("")
    if "test_dqn_proxy_expanded5" in digital_complete and len(digital_complete):
        top = top_table(digital_complete, top_cols, "test_dqn_proxy_expanded5", 15)
        lines.append(df_to_markdown_simple(top))
    else:
        lines.append("- No `test_dqn_proxy_expanded5` available.")
    lines.append("")

    lines.append("## Top digital-noisy rows by known macro-F1")
    lines.append("")
    if "test_known_macro_f1" in digital_complete and len(digital_complete):
        top = top_table(digital_complete, top_cols, "test_known_macro_f1", 15)
        lines.append(df_to_markdown_simple(top))
    else:
        lines.append("- No `test_known_macro_f1` available.")
    lines.append("")

    lines.append("## First reconstruction conclusion")
    lines.append("")
    lines.append("The old digital-noisy experiment program can be reconstructed from committed metadata inventories. The next step is to map the inferred families and source profile into `pa_experiment_catalog.py`, then rerun only missing/ambiguous cells rather than repeating the entire historical search.")
    lines.append("")

    (OUT_DIR / "legacy_digital_reconstruction.md").write_text("\n".join(lines))

    print("Wrote:")
    for p in [
        OUT_DIR / "legacy_digital_reconstruction.md",
        OUT_DIR / "legacy_digital_noisy_runs.csv",
        OUT_DIR / "legacy_digital_noisy_complete_runs.csv",
        OUT_DIR / "legacy_digital_noisy_missing_summaries.csv",
        OUT_DIR / "legacy_top_digital_by_proxy5.csv",
        OUT_DIR / "legacy_top_digital_by_known_f1.csv",
    ]:
        print(" ", p)


if __name__ == "__main__":
    main()
