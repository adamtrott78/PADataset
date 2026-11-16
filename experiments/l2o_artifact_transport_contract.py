#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class ArtifactTransportBinding:
    canonical_key: str
    artifact_id: int
    artifact_digest: str
    workflow_run_id: int
    artifact_name: str


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_row(matrix: Dict[str, Any], canonical_key: str) -> Dict[str, Any]:
    rows = [x for x in matrix.get("backbones", []) if x.get("canonical_key") == canonical_key]
    if len(rows) != 1:
        raise ValueError(f"canonical_key must resolve exactly once: {canonical_key!r}")
    row = rows[0]
    if row.get("status") != "COMPLETE":
        raise ValueError(f"canonical backbone is not COMPLETE: {canonical_key}")
    return row


def validate_artifact_transport(
    *,
    request_path: Path,
    matrix_path: Path,
    artifact_metadata_path: Path,
) -> ArtifactTransportBinding:
    request = _load(request_path)
    matrix = _load(matrix_path)
    artifact = _load(artifact_metadata_path)

    if request.get("schema") != "padataset.l2o-directional-eval-request.v1":
        raise ValueError("directional eval request schema mismatch")
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("canonical matrix schema mismatch")

    row = _find_row(matrix, str(request.get("canonical_key")))
    manifest_id = int(row.get("artifact_id", -1))
    manifest_digest = str(row.get("artifact_digest", ""))
    manifest_run = int(row.get("workflow_run_id", -1))

    if int(request.get("artifact_id", -2)) != manifest_id:
        raise ValueError("request artifact ID differs from canonical matrix")
    if str(request.get("artifact_digest", "")) != manifest_digest:
        raise ValueError("request artifact digest differs from canonical matrix")

    if int(artifact.get("id", -3)) != manifest_id:
        raise ValueError("GitHub artifact ID mismatch")
    if str(artifact.get("digest", "")) != manifest_digest:
        raise ValueError("GitHub artifact digest mismatch")
    if artifact.get("expired") is not False:
        raise ValueError("GitHub artifact is expired or expiry state is unknown")

    name = str(artifact.get("name", ""))
    if not name.startswith("padataset-scientific"):
        raise ValueError("unexpected GitHub artifact name")

    workflow_run = artifact.get("workflow_run") or {}
    if int(workflow_run.get("id", -4)) != manifest_run:
        raise ValueError("GitHub artifact workflow run mismatch")

    return ArtifactTransportBinding(
        canonical_key=row["canonical_key"],
        artifact_id=manifest_id,
        artifact_digest=manifest_digest,
        workflow_run_id=manifest_run,
        artifact_name=name,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--artifact-metadata", required=True)
    args = ap.parse_args()

    binding = validate_artifact_transport(
        request_path=Path(args.request),
        matrix_path=Path(args.matrix),
        artifact_metadata_path=Path(args.artifact_metadata),
    )
    print(json.dumps({
        "canonical_key": binding.canonical_key,
        "artifact_id": binding.artifact_id,
        "artifact_digest": binding.artifact_digest,
        "workflow_run_id": binding.workflow_run_id,
        "artifact_name": binding.artifact_name,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
