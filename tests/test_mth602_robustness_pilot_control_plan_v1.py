from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_pilot_control_plan_matches_pilot_matrix_artifacts():
    m=json.loads((ROOT/"manifests/l2o_canonical_backbone_matrix_v1.json").read_text())
    p=json.loads((ROOT/"manifests/l2o_control_matrix_plan_v1.json").read_text())
    by={x["canonical_key"]:x for x in m["backbones"]}
    for pair in ("PA1-PA2","PA1-PA3"):
        row=by[pair]
        cells=[x for x in p["cells"] if x["canonical_key"]==pair]
        assert len(cells)==2
        for c in cells:
            assert c["backbone_artifact_id"]==row["artifact_id"]
            assert c["backbone_artifact_digest"]==row["artifact_digest"]
            assert c["backbone_candidate_sha"]==row["candidate_sha"]
            assert c["best_model_sha256"]==row["best_model_sha256"]
            assert c["partition_seed"]==0
            assert c["training_seed"]==1
            assert c["target_test_consumed_before_final_eval"] is False
