#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_archb_artifact_transport(
    *, request_path: Path, artifact_metadata_path: Path
) -> Dict[str, Any]:
    req = _load(request_path)
    artifact = _load(artifact_metadata_path)

    if req.get("schema") != "padataset.archb-cross-surrogate-eval-request.v1":
        raise ValueError("Architecture-B request schema mismatch")
    src = req.get("source_backbone") or {}

    if int(artifact.get("id", -1)) != int(src.get("artifact_id", -2)):
        raise ValueError("GitHub artifact ID mismatch")
    if artifact.get("digest") != src.get("artifact_digest"):
        raise ValueError("GitHub artifact digest mismatch")
    if artifact.get("name") != src.get("artifact_name"):
        raise ValueError("GitHub artifact name mismatch")
    if artifact.get("expired") is not False:
        raise ValueError("GitHub artifact is expired or expiry state is unknown")
    workflow_run = artifact.get("workflow_run") or {}
    if int(workflow_run.get("id", -1)) != int(src.get("workflow_run_id", -2)):
        raise ValueError("GitHub artifact workflow run mismatch")

    return {
        "artifact_id": int(src["artifact_id"]),
        "artifact_digest": str(src["artifact_digest"]),
        "artifact_name": str(src["artifact_name"]),
        "workflow_run_id": int(src["workflow_run_id"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--artifact-metadata", required=True)
    args = ap.parse_args()
    print(json.dumps(
        validate_archb_artifact_transport(
            request_path=Path(args.request),
            artifact_metadata_path=Path(args.artifact_metadata),
        ),
        sort_keys=True,
    ))


if __name__ == "__main__":
    main()
