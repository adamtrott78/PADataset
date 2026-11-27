from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_min_f1_telemetry_is_wired():
    e=(ROOT/"evaluate.py").read_text()
    d=(ROOT/"discriminate.py").read_text()
    assert '"min_class_f1"' in e
    assert '"val_min_class_f1": []' in d
    assert 'val_min_class_f1=float' in d

def test_cache_builder_never_materializes_target_test():
    s=(ROOT/"experiments/mth602_robustness_calibration_cache.py").read_text()
    assert '"target_test_materialized":False' in s
    assert 'test_open_loader' not in s
    assert 'val_open_loader' in s
    assert 'known_test.npz' in s

def test_pa_train_one_has_opt_in_post_train_cache_hook():
    s=(ROOT/"experiments/pa_train_one.py").read_text()
    assert 'post_train_osr_calibration_cache' in s
    assert 'build_calibration_cache' in s

def test_four_smoke_manifests_are_two_epochs_and_nonfinal():
    root=ROOT/"manifests/configs/mth602_robustness_smoke_v1"
    files=sorted(root.glob("*.json"))
    assert len(files)==4
    seen=[]
    for p in files:
        c=json.loads(p.read_text())
        assert c["epochs"]==2
        assert c["post_train_osr_calibration_cache"] is True
        assert c["robustness_replication"]["final_science_eligible"] is False
        seen.append((c["robustness_replication"]["smoke_wave"],c["robustness_replication"]["lane"]))
    assert sorted(seen)==[("A","G0"),("A","G1"),("B","G0"),("B","G1")]

def test_posttrain_bundle_freezes_before_target_materialization():
    s=(ROOT/"experiments/mth602_robustness_posttrain_bundle.py").read_text()
    assert s.index("freeze_methods(") < s.index("build_target_cache(")
    assert '"methods_frozen_before_target_test":True' in s
    assert '"target_test_consumed_before_method_fit":False' in s

def test_cached_consumer_never_touches_raw_dataset_or_backbone():
    s=(ROOT/"experiments/mth602_robustness_cached_all_osr.py").read_text()
    for forbidden in ["build_data_from_setup","_make_setup_from_run_config","load_backbone_run","test_open_loader","data_root"]:
        assert forbidden not in s
    assert '"raw_hdf5_reads":0' in s
    assert '"backbone_forward_passes":0' in s
