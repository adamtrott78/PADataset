#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class ControlArtifactTransportBinding:
    canonical_key: str
    artifact_id: int
    artifact_digest: str
    workflow_run_id: int
    artifact_name: str


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_control_artifact_transport(
    *,
    request_path: Path,
    matrix_path: Path,
    artifact_metadata_path: Path,
) -> ControlArtifactTransportBinding:
    request = _load(request_path)
    matrix = _load(matrix_path)
    artifact = _load(artifact_metadata_path)

    if request.get("schema") != "padataset.l2o-control-eval-request.v1":
        raise ValueError("control eval request schema mismatch")
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("canonical matrix schema mismatch")

    rows = [x for x in matrix.get("backbones", []) if x.get("canonical_key") == request.get("canonical_key")]
    if len(rows) != 1:
        raise ValueError("canonical_key must resolve exactly once")
    row = rows[0]
    if row.get("status") != "COMPLETE":
        raise ValueError("canonical backbone is not COMPLETE")

    manifest_id = int(row["artifact_id"])
    manifest_digest = str(row["artifact_digest"])
    manifest_run = int(row["workflow_run_id"])
    if int(request.get("artifact_id", -1)) != manifest_id:
        raise ValueError("request artifact ID differs from canonical matrix")
    if str(request.get("artifact_digest", "")) != manifest_digest:
        raise ValueError("request artifact digest differs from canonical matrix")
    if int(artifact.get("id", -1)) != manifest_id:
        raise ValueError("GitHub artifact ID mismatch")
    if str(artifact.get("digest", "")) != manifest_digest:
        raise ValueError("GitHub artifact digest mismatch")
    if artifact.get("expired") is not False:
        raise ValueError("GitHub artifact is expired or expiry state is unknown")
    name = str(artifact.get("name", ""))
    if not name.startswith("padataset-scientific"):
        raise ValueError("unexpected GitHub artifact name")
    workflow_run = artifact.get("workflow_run") or {}
    if int(workflow_run.get("id", -1)) != manifest_run:
        raise ValueError("GitHub artifact workflow run mismatch")

    return ControlArtifactTransportBinding(
        canonical_key=str(row["canonical_key"]),
        artifact_id=manifest_id,
        artifact_digest=manifest_digest,
        workflow_run_id=manifest_run,
        artifact_name=name,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--artifact-metadata", required=True)
    args = ap.parse_args()
    b = validate_control_artifact_transport(
        request_path=Path(args.request),
        matrix_path=Path(args.matrix),
        artifact_metadata_path=Path(args.artifact_metadata),
    )
    print(json.dumps({
        "canonical_key": b.canonical_key,
        "artifact_id": b.artifact_id,
        "artifact_digest": b.artifact_digest,
        "workflow_run_id": b.workflow_run_id,
        "artifact_name": b.artifact_name,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
