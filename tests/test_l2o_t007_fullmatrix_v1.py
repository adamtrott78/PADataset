import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALL={"PA1","PA2","PA3","PA4","PA8"}
EXPECTED={
    "lr": 0.0000704567293035,
    "weight_decay": 0,
    "lambda_center": 0.1,
    "label_smoothing": 0.1,
    "entropy_loss_weight": 0.1,
    "mlp_dropout": 0.3,
    "grad_clip_norm": 0.5,
    "scheduler_name": "plateau",
    "batch_size": 8,
}
PAIRS=["PA1-PA2","PA1-PA3","PA1-PA4","PA1-PA8","PA2-PA4","PA3-PA4","PA4-PA8"]

def test_t007_fullmatrix_configs_are_uniform_and_quarantined():
    root=ROOT/"manifests/configs/l2o_t007_fullmatrix_v1"
    files=sorted(root.glob("*.json"))
    assert len(files)==7
    seen=[]
    for p in files:
        cfg=json.loads(p.read_text())
        meta=cfg["hpo_trial"]
        pair=meta["canonical_pair"]
        seen.append(pair)
        a,b=pair.split("-")
        assert set(cfg["known_pas_l2o"]) == ALL-{a,b}
        assert cfg["target_unknown_pa"] == a
        assert cfg["surrogate_open_pa"] == b
        assert cfg["unknown_pas"] == [a]
        assert set(cfg["pas"]) == (ALL-{b})
        assert cfg["open_val_frac"] == 0
        assert cfg["build_balanced_val_open"] is False
        assert cfg["require_true_val_open"] is False
        assert cfg["early_stopping_mode"] == "known_only"
        assert cfg["quarantine_target_until_test"] is True
        assert cfg["epochs"] == 60
        assert meta["stage"] == "fullmatrix"
        assert meta["trial_index"] == 7
        assert meta["selection_evidence"] == "known_validation_only"
        assert meta["target_metrics_allowed_for_selection"] is False
        assert meta["test_metrics_allowed_for_selection"] is False
        assert meta["params"] == EXPECTED
    assert sorted(seen)==sorted(PAIRS)

def test_t007_fullmatrix_manifest_is_complete():
    m=json.loads((ROOT/"manifests/l2o_t007_fullmatrix_v1.json").read_text())
    assert m["schema"]=="padataset.l2o-t007-fullmatrix.v1"
    assert m["recipe"]["id"]=="t007"
    assert m["recipe"]["osr_metrics_allowed_for_selection"] is False
    assert len(m["existing_pilot_pairs"])==3
    assert len(m["remaining_pairs"])==7
