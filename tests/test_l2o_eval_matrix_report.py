from __future__ import annotations

import itertools

import pandas as pd
import pytest

from experiments.l2o_eval_matrix_report import PAS, build_matrix_report


def _frame(value_fn):
    rows = []
    for a in PAS:
        for b in PAS:
            if a == b:
                continue
            rows.append({
                "evaluation_target": a,
                "evaluation_surrogate": b,
                "unknown_f1": float(value_fn(a, b)),
            })
    return pd.DataFrame(rows)


def test_report_builds_complete_target_surrogate_outputs(tmp_path):
    repaired = tmp_path / "repaired.csv"
    _frame(lambda a, b: 0.5 + 0.01 * (PAS.index(b) + 1)).to_csv(repaired, index=False)

    report = build_matrix_report(
        repaired_csv=repaired,
        output_dir=tmp_path / "out",
    )

    assert report["cells"] == 20
    assert len(report["per_target"]) == 5
    assert (tmp_path / "out" / "unknown_f1_matrix.csv").is_file()
    assert (tmp_path / "out" / "unknown_f1_per_target.csv").is_file()
    assert (tmp_path / "out" / "matrix_report.json").is_file()


def test_report_baseline_comparison_is_cell_exact(tmp_path):
    repaired = tmp_path / "repaired.csv"
    baseline = tmp_path / "baseline.csv"
    _frame(lambda a, b: 0.8).to_csv(repaired, index=False)
    _frame(lambda a, b: 0.7).to_csv(baseline, index=False)

    report = build_matrix_report(
        repaired_csv=repaired,
        baseline_csv=baseline,
        output_dir=tmp_path / "out",
    )

    cmp = report["baseline_comparison"]
    assert cmp["mean_delta"] == pytest.approx(0.1)
    assert cmp["improved_cells"] == 20
    assert cmp["regressed_cells"] == 0


def test_report_rejects_missing_cell(tmp_path):
    repaired = tmp_path / "repaired.csv"
    df = _frame(lambda a, b: 0.8).iloc[:-1]
    df.to_csv(repaired, index=False)

    with pytest.raises(ValueError, match="exactly 20 rows"):
        build_matrix_report(
            repaired_csv=repaired,
            output_dir=tmp_path / "out",
        )


def test_report_rejects_duplicate_cell(tmp_path):
    repaired = tmp_path / "repaired.csv"
    df = _frame(lambda a, b: 0.8)
    df.iloc[-1] = df.iloc[0]
    df.to_csv(repaired, index=False)

    with pytest.raises(ValueError, match="duplicate"):
        build_matrix_report(
            repaired_csv=repaired,
            output_dir=tmp_path / "out",
        )
