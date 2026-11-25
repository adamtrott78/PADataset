from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_rehydrator_supports_replica_run_name_and_independent_seed_axes():
    s=(ROOT/"experiments/l2o_artifact_rehydrate.py").read_text()
    assert 'row.get("run_name")' in s
    assert 'row.get("training_seed", matrix.get("seed", -2))' in s
    assert 'row.get("partition_seed", matrix.get("seed", -2))' in s
    assert 'cfg.get("training_seed", cfg.get("seed", -1))' in s
    assert 'cfg.get("partition_seed", cfg.get("seed", -1))' in s

def test_pa1pa2_pilot_matrix_binds_replica_run_name():
    import json
    m=json.loads((ROOT/"manifests/l2o_canonical_backbone_matrix_v1.json").read_text())
    e=next(x for x in m["backbones"] if x["canonical_key"]=="PA1-PA2")
    assert e["run_name"]=="mth602_final_robust_PA1_PA2_p00_t01"
    assert e["partition_seed"]==0 and e["training_seed"]==1
