from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.l2o_control_eval_result_record import build_control_result_record


def test_result_record_accepts_two_frozen_controls(tmp_path: Path):
    matrix = {
        "schema": "padataset.l2o-canonical-backbone-matrix.v1",
        "backbones": [{
            "canonical_key": "PA1-PA2",
            "canonical_pair": ["PA1", "PA2"],
            "known_pas": ["PA3", "PA4", "PA8"],
            "status": "COMPLETE",
            "artifact_id": 1,
            "artifact_digest": "sha256:abc",
            "workflow_run_id": 10,
            "workflow_job_id": 11,
            "candidate_sha": "a" * 40,
            "best_model_sha256": "b" * 64,
            "config_sha256": "c" * 64,
        }],
    }
    policy = {
        "schema": "padataset.l2o-control-eval-policy.v1",
        "policy_id": "l2o_repaired_controls_frozen_v1",
        "controls": {
            "dqn_ids_style": {"method_id": "dqn_ids_style_softmax3_external_surrogate_cap625_v1"},
            "varmax": {"method_id": "varmax_surrogate_all_smoke_matched_l2o_v1"},
        },
    }
    request = {
        "schema": "padataset.l2o-control-eval-request.v1",
        "policy_id": policy["policy_id"],
        "canonical_key": "PA1-PA2",
        "artifact_id": 1,
        "artifact_digest": "sha256:abc",
        "evaluation_target": "PA1",
        "evaluation_surrogate": "PA2",
        "checkpoint": "best_model",
    }
    metadata = {
        "schema": "padataset.l2o-control-eval-metadata.v1",
        "policy_id": policy["policy_id"],
        "target": "PA1",
        "external_surrogate": "PA2",
        "controls_fitted_before_target_test": True,
        "target_labels_used_for_tuning": False,
        "target_test_consumed_before_final_eval": False,
    }
    paths = {}
    for name, payload in [("matrix", matrix), ("policy", policy), ("request", request), ("metadata", metadata)]:
        p = tmp_path / f"{name}.json"
        p.write_text(json.dumps(payload), encoding="utf-8")
        paths[name] = p

    base = dict(
        policy_id=policy["policy_id"],
        target_unknown_pas=json.dumps(["PA1"]),
        external_surrogate="PA2",
        target_labels_used_for_tuning=False,
        target_test_consumed_before_final_eval=False,
        known_reject_rate=0.1,
        unknown_precision=0.8,
        unknown_recall=0.7,
        unknown_f1=0.746,
        osr_acc=0.8,
        osr_macro_f1=0.79,
        unknown_auroc=0.9,
    )
    rows = [
        {
            **base,
            "control_id": policy["controls"]["dqn_ids_style"]["method_id"],
            "calibration_source": "external_surrogate_validation",
            "external_surrogate_consumed": True,
            "known_calibration_n": 625,
            "open_calibration_n": 625,
            "varmax_calibration_mode": "",
            "varmax_sweep_grid": "",
        },
        {
            **base,
            "control_id": policy["controls"]["varmax"]["method_id"],
            "calibration_source": "known_validation_surrogate_all",
            "external_surrogate_consumed": False,
            "known_calibration_n": 1000,
            "open_calibration_n": 0,
            "varmax_calibration_mode": "surrogate_all",
            "varmax_sweep_grid": "smoke",
        },
    ]
    csv = tmp_path / "control_summary.csv"
    pd.DataFrame(rows).to_csv(csv, index=False)
    out = tmp_path / "result.json"
    record = build_control_result_record(
        request_path=paths["request"],
        matrix_path=paths["matrix"],
        policy_path=paths["policy"],
        summary_csv=csv,
        metadata_path=paths["metadata"],
        output_path=out,
    )
    assert record["status"] == "COMPLETE"
    assert set(record["controls"]) == {
        policy["controls"]["dqn_ids_style"]["method_id"],
        policy["controls"]["varmax"]["method_id"],
    }
    assert record["provenance"]["controls_fitted_before_target_test"] is True
