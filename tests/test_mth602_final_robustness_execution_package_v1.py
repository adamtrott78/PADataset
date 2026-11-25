from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = "3fd1454bc20b89580f14c2e319d9b33766ea14b5"

def test_execution_index_exact_factorial():
    idx=json.loads((ROOT/"manifests/mth602_final_robustness_execution_index_v1.json").read_text())
    assert idx["accepted_seed_freeze_candidate_sha"]==ACCEPTED
    assert idx["partition_seeds"]==[0,1,2,3,4]
    assert idx["training_seeds"]==list(range(10))
    assert idx["canonical_pair_count"]==10
    assert idx["total_backbone_cells"]==500
    assert len(idx["entries"])==500
    assert len({(e["canonical_pair"],e["partition_seed"],e["training_seed"]) for e in idx["entries"]})==500

def test_every_manifest_preserves_frozen_contract():
    idx=json.loads((ROOT/"manifests/mth602_final_robustness_execution_index_v1.json").read_text())
    for e in idx["entries"]:
        cfg=json.loads((ROOT/e["path"]).read_text())
        assert cfg["run_name"]==e["run_name"]
        assert cfg["partition_seed"]==e["partition_seed"]
        assert cfg["training_seed"]==e["training_seed"]
        assert cfg["seed"]==e["training_seed"]
        assert cfg["manifold_balance_seed"]==e["partition_seed"]
        assert cfg["deterministic_training"] is True
        assert cfg["deterministic_profile"]=="strict_tf32"
        assert cfg["early_stopping_mode"]=="known_only"
        assert cfg["model_selection_metric"]=="val_macro_f1"
        assert float(cfg["open_val_frac"])==0.0
        assert cfg["quarantine_target_until_test"] is True
        assert cfg["skip_cache_build"] is True
        assert cfg["force_rebuild_cache"] is False
        assert cfg["use_timestamped_run_dir"] is False
        assert cfg["overwrite_existing_run"] is False
        rr=cfg["robustness_replication"]
        assert rr["accepted_seed_freeze_candidate_sha"]==ACCEPTED
        assert rr["canonical_pair"]==e["canonical_pair"]
        assert rr["partition_seed"]==e["partition_seed"]
        assert rr["training_seed"]==e["training_seed"]
        assert rr["dqn_seed"]==42
        assert rr["target_test_selection_feedback"] is False
        assert rr["checkpoint_selection"]=="known_validation_only_best_model"
        assert rr["status"]=="READY_FOR_BOUNDED_TRAIN_BACKBONE"
