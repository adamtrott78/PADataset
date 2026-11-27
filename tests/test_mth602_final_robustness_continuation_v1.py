import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
M=ROOT/"manifests/mth602_final_robustness_continuation_v1.json"
TRAIN=ROOT/"experiments/pa_train_one.py"

def test_continuation_membership():
    m=json.loads(M.read_text())
    assert m["status"]=="PREPARED_NOT_ADMITTED"
    assert m["remaining_trainings"]==46
    assert m["lane_counts"]=={"lambda-scientific":23,"lambda-scientific-2":23}
    assert len(m["cells"])==46
    ids={(c["canonical_pair"],c["partition_seed"],c["training_seed"]) for c in m["cells"]}
    assert ("PA1-PA2",1,0) not in ids
    assert ("PA1-PA2",2,0) not in ids

def test_runner_enables_posttrain_bundle_for_final_family_only():
    s=TRAIN.read_text()
    assert 'cfg.get("family_tag") == "mth602_final_robustness_v1"' in s
    assert 'cfg.setdefault("post_train_osr_calibration_cache", True)' in s
    assert 'cfg.setdefault("post_train_osr_cache_num_workers"' in s
    assert '"deterministic_frozen_method_bundle": True' in s
    assert '"target_labels_used_for_tuning": False' in s

def test_science_horizon_unchanged():
    m=json.loads(M.read_text())
    assert m["training_policy"]=={
        "epochs_max":60,
        "early_stopping_mode":"known_only",
        "early_stopping_patience":10,
        "horizon_change":False,
    }
    for c in m["cells"]:
        cfg=json.loads((ROOT/c["config_path"]).read_text())
        assert cfg["epochs"]==60
        assert cfg["early_stopping_mode"]=="known_only"
        assert cfg["early_stopping_patience"]==10

def test_head_freeze_contract():
    m=json.loads(M.read_text())
    assert m["head_freeze_policy"]["exact_head_pin_required"] is True
    assert m["head_freeze_policy"]["no_pr_head_mutation_after_admission"] is True
    assert m["head_freeze_policy"]["explicit_execution_authority_required"] is True
