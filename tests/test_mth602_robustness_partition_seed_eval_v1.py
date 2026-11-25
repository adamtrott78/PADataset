from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_robustness_osr_reconstructs_partition_seed():
    e=(ROOT/"evaluate.py").read_text()
    assert 'seed=config.get("partition_seed", config.get("seed", 0))' in e
    assert '"partition_seed": handle.config.get("partition_seed", handle.config.get("seed"))' in e
    assert '"training_seed": handle.config.get("training_seed", handle.config.get("seed"))' in e

def test_control_calibration_caps_follow_partition_seed():
    c=(ROOT/"experiments/pa_eval_l2o_controls_v1.py").read_text()
    assert '"partition_seed": handle.config.get("partition_seed", handle.config.get("seed"))' in c
    assert 'calibration_payload.meta.get("partition_seed", calibration_payload.meta.get("seed", 0))' in c
