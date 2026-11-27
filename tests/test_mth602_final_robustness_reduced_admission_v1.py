from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ADM=ROOT/"manifests/mth602_final_robustness_reduced_admission_v1.json"
PLAN=ROOT/"manifests/mth602_final_robustness_reduced_v1.json"

PAIRS=["PA1-PA2","PA1-PA3","PA1-PA4","PA1-PA8","PA2-PA3","PA2-PA4","PA2-PA8","PA3-PA4","PA3-PA8","PA4-PA8"]

def test_exact_48_cell_remainder_and_balanced_lanes():
    a=json.loads(ADM.read_text())
    cells=a["cells"]
    assert a["status"]=="AUTHORIZED_FOR_BOUNDED_ADMISSION"
    assert len(cells)==48
    assert len({(c["canonical_pair"],c["partition_seed"],c["training_seed"]) for c in cells})==48
    assert Counter(c["lane"] for c in cells)=={"lambda-scientific":24,"lambda-scientific-2":24}
    assert all(not (c["partition_seed"]==0 and c["training_seed"]==0) for c in cells)

    expected={(pair,p,0) for pair in PAIRS for p in (1,2,3,4)}
    expected|={(pair,0,1) for pair in PAIRS if pair not in {"PA1-PA2","PA1-PA3"}}
    observed={(c["canonical_pair"],c["partition_seed"],c["training_seed"]) for c in cells}
    assert observed==expected

def test_every_admitted_config_matches_identity_and_frozen_contract():
    a=json.loads(ADM.read_text())
    for c in a["cells"]:
        p=ROOT/c["config_path"]
        assert p.is_file(), c["config_path"]
        cfg=json.loads(p.read_text())
        assert cfg["run_name"]==c["run_name"]
        assert cfg["partition_seed"]==c["partition_seed"]
        assert cfg["training_seed"]==c["training_seed"]
        assert cfg["seed"]==c["training_seed"]
        assert cfg["deterministic_training"] is True
        assert cfg["deterministic_profile"]=="strict_tf32"
        assert cfg["early_stopping_mode"]=="known_only"
        assert cfg["model_selection_metric"]=="val_macro_f1"
        assert cfg["open_val_frac"]==0.0
        assert cfg["quarantine_target_until_test"] is True
        rr=cfg["robustness_replication"]
        assert rr["canonical_pair"]==c["canonical_pair"]
        assert rr["partition_seed"]==c["partition_seed"]
        assert rr["training_seed"]==c["training_seed"]
        assert rr["dqn_seed"]==42
        assert rr["target_test_selection_feedback"] is False

def test_reduced_plan_gate_closed_and_existing_pilots_excluded():
    p=json.loads(PLAN.read_text())
    assert p["status"]=="FINAL_LAUNCH_AUTHORIZED_DETERMINISM_RESOLVED"
    assert p["final_launch_gate_resolution"]["status"]=="PASS"
    assert p["remaining_new_trainings"]==48
    assert p["already_completed_p00t01"]==["PA1-PA2","PA1-PA3"]
