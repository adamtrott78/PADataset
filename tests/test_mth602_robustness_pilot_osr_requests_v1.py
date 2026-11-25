from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_pa1pa2_p00t01_pilot_matrix_and_requests_are_exact():
    m=json.loads((ROOT/"manifests/l2o_canonical_backbone_matrix_v1.json").read_text())
    e=next(x for x in m["backbones"] if x["canonical_key"]=="PA1-PA2")
    assert e["artifact_id"]==15063830452
    assert e["artifact_digest"]=="sha256:b3b53325080dd9da92425bfeb5e26c08b025ce3f2ab416ec4fa11bc5bae5bdc3"
    assert e["candidate_sha"]=="af4e2835b4e066a501b42e4b1558bee42cab9f8f"
    assert e["best_model_sha256"]=="18422631d8369bfdb184cf34b738caba8c252caea04c040788575440fb59d0e5"
    assert e["config_sha256"]=="0e3106a634b6c730e370e1ea9e629f875bbd765b9321c9b1d3c1878721d153da"
    assert e["partition_seed"]==0 and e["training_seed"]==1 and e["dqn_seed"]==42
    assert e["target_test_consumed"] is False
    roots=["manifests/configs/l2o_directional_eval_v1","manifests/configs/l2o_control_eval_v1"]
    for root in roots:
        for target,sur in [("PA1","PA2"),("PA2","PA1")]:
            p=ROOT/root/f"ROBUST_p00t01__PA1-PA2__target{target}__sur{sur}.json"
            r=json.loads(p.read_text())
            assert r["artifact_id"]==15063830452
            assert r["artifact_digest"]==e["artifact_digest"]
            assert r["evaluation_target"]==target and r["evaluation_surrogate"]==sur
            assert r["target_labels_used_for_tuning"] is False
            assert r["partition_seed"]==0 and r["training_seed"]==1 and r["dqn_seed"]==42
