import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "manifests" / "l2o_canonical_backbone_matrix_v1.json"

def test_pa2_pa3_t007_frozen_artifact_binding():
    matrix = json.loads(MATRIX.read_text())
    rows = [r for r in matrix["backbones"] if r["canonical_key"] == "PA2-PA3"]
    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "COMPLETE"
    assert row["artifact_id"] == 14736363148
    assert row["artifact_digest"] == "sha256:3419dd982709fccdfccce0a044260542a904ce9c86e1c4ef4e8e8bcb76c96b4d"
    assert row["candidate_sha"] == "da521eaee997c56012290c9c261ee1831432ebbc"
    assert row["best_model_sha256"] == "39d919f1203c76358fded8e67cd85fc2047a7d4cc884d14eb516ff1e08995341"
    assert row["config_sha256"] == "2886a7c76591b362c98e7956071a5fff57b455314a1a239ac1524f869ac46926"
