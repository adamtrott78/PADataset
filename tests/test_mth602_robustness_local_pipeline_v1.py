from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]

def test_new_pipeline_sources_parse():
    for p in ["experiments/mth602_robustness_cached_all_osr.py","scripts/mth602_robustness_local_pipeline.py","scripts/mth602_robustness_local_dashboard.py"]:
        ast.parse((ROOT/p).read_text(),filename=p)

def test_cached_consumer_imports():
    import experiments.mth602_robustness_cached_all_osr as m
    assert callable(m.run_direction)

def test_cached_consumer_enforces_target_firewall_and_cpu_only():
    s=(ROOT/"experiments/mth602_robustness_cached_all_osr.py").read_text()
    assert 'methods_frozen_before_target_test' in s
    run=s[s.index("def run_direction"):]
    assert run.index('methods_frozen_before_target_test') < run.index('target_test=collect_target_test_once')
    assert 'CUDA_VISIBLE_DEVICES' in s
    assert 'target_test_consumed_before_method_fit' in s

def test_local_pipeline_is_bounded_and_provider_free():
    s=(ROOT/"scripts/mth602_robustness_local_pipeline.py").read_text()
    assert '--max-workers' in s
    assert 'CUDA_VISIBLE_DEVICES' in s
    assert 'provider_calls_per_refresh":0' in s
    for bad in ["gh api","gh run","api.github.com","graphql"]:
        assert bad not in s.lower()

def test_dashboard_is_zero_provider_and_ctrl_c_exits():
    s=(ROOT/"scripts/mth602_robustness_local_dashboard.py").read_text().lower()
    for bad in ["gh api","gh run","api.github.com","graphql","curl "]:
        assert bad not in s
    assert "keyboardinterrupt" in s
    assert "val_min_class_f1" in s
    assert "campaign eta" in s
    assert "projected finish" in s

def test_reduced_plan_is_5_partitions_plus_one_t1_rep_not_cartesian():
    p=json.loads((ROOT/"manifests/mth602_final_robustness_reduced_v1.json").read_text())
    assert p["partition_seeds"]==[0,1,2,3,4]
    assert p["training_seeds"]==[0,1]
    assert p["unique_cells_per_pair"]==6
    assert p["total_unique_cells"]==60
    assert p["new_trainings"]==50

def test_cached_policy_requires_pilot_parity():
    p=json.loads((ROOT/"manifests/mth602_robustness_cached_osr_policy_v1.json").read_text())
    assert p["status"]=="CANDIDATE_REQUIRES_PILOT_PARITY_BEFORE_FINAL_SCIENCE"
    assert p["parity_gate"]["required"] is True
    assert p["firewall"]["target_test_consumed_before_method_fit"] is False
    assert p["concurrency"]["max_cpu_consumers"]==2
