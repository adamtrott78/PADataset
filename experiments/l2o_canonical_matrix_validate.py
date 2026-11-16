#!/usr/bin/env python3
from __future__ import annotations

import argparse
import itertools
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PA_NAMES: Tuple[str, ...] = ("PA1", "PA2", "PA3", "PA4", "PA8")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_pairs() -> List[Tuple[str, str]]:
    return list(itertools.combinations(PA_NAMES, 2))


def validate_canonical_matrix(
    *,
    matrix_path: Path,
    request_root: Path | None = None,
) -> Dict[str, int]:
    matrix = _load(matrix_path)
    if matrix.get("schema") != "padataset.l2o-canonical-backbone-matrix.v1":
        raise ValueError("canonical matrix schema mismatch")
    if int(matrix.get("canonical_backbone_count", -1)) != 10:
        raise ValueError("canonical_backbone_count must be 10")
    if int(matrix.get("directed_cell_count", -1)) != 20:
        raise ValueError("directed_cell_count must be 20")

    rows = list(matrix.get("backbones") or [])
    if len(rows) != 10:
        raise ValueError(f"matrix must contain exactly 10 backbone rows, got {len(rows)}")

    expected_pairs = _expected_pairs()
    observed_pairs: List[Tuple[str, str]] = []
    directed_total = 0
    complete = 0

    for row in rows:
        pair = tuple(row.get("canonical_pair") or [])
        if len(pair) != 2 or pair != tuple(sorted(pair)):
            raise ValueError(f"canonical_pair must contain two sorted PAs: {pair!r}")
        if any(pa not in PA_NAMES for pa in pair):
            raise ValueError(f"canonical_pair contains unknown PA: {pair!r}")
        observed_pairs.append(pair)

        key = "-".join(pair)
        if row.get("canonical_key") != key:
            raise ValueError(f"canonical_key mismatch for {pair!r}")

        expected_known = [pa for pa in PA_NAMES if pa not in pair]
        if list(row.get("known_pas") or []) != expected_known:
            raise ValueError(f"known_pas complement/order mismatch for {key}")

        cells = list(row.get("directed_cells") or [])
        expected_cells = {
            (pair[0], pair[1]),
            (pair[1], pair[0]),
        }
        observed_cells = {
            (str(x.get("evaluation_target")), str(x.get("evaluation_surrogate")))
            for x in cells
        }
        if len(cells) != 2 or observed_cells != expected_cells:
            raise ValueError(f"directed cell coverage mismatch for {key}")
        directed_total += len(cells)

        status = row.get("status")
        if status == "COMPLETE":
            complete += 1
            training = row.get("training_direction") or {}
            if {
                str(training.get("target")),
                str(training.get("surrogate")),
            } != set(pair):
                raise ValueError(f"training direction mismatch for {key}")

            for field in ("workflow_run_id", "workflow_job_id", "artifact_id"):
                if int(row.get(field, 0)) <= 0:
                    raise ValueError(f"{field} missing for completed {key}")

            digest = str(row.get("artifact_digest", ""))
            if not digest.startswith("sha256:") or not SHA256_RE.fullmatch(digest[7:]):
                raise ValueError(f"artifact_digest invalid for completed {key}")
            if not GIT_SHA_RE.fullmatch(str(row.get("candidate_sha", ""))):
                raise ValueError(f"candidate_sha invalid for completed {key}")
            if not SHA256_RE.fullmatch(str(row.get("best_model_sha256", ""))):
                raise ValueError(f"best_model_sha256 invalid for completed {key}")
            if not SHA256_RE.fullmatch(str(row.get("config_sha256", ""))):
                raise ValueError(f"config_sha256 invalid for completed {key}")
            if row.get("target_test_consumed") not in (None, False):
                raise ValueError(f"target_test_consumed must not be true for completed {key}")

            if request_root is not None:
                for target, surrogate in sorted(expected_cells):
                    request_path = (
                        request_root
                        / f"{key}__target{target}__sur{surrogate}.json"
                    )
                    if not request_path.is_file():
                        raise ValueError(f"missing frozen directional request: {request_path.name}")
                    request = _load(request_path)
                    if request.get("schema") != "padataset.l2o-directional-eval-request.v1":
                        raise ValueError(f"request schema mismatch: {request_path.name}")
                    if request.get("canonical_key") != key:
                        raise ValueError(f"request canonical_key mismatch: {request_path.name}")
                    if int(request.get("artifact_id", -1)) != int(row["artifact_id"]):
                        raise ValueError(f"request artifact_id mismatch: {request_path.name}")
                    if request.get("artifact_digest") != row["artifact_digest"]:
                        raise ValueError(f"request artifact_digest mismatch: {request_path.name}")
                    if (
                        request.get("evaluation_target"),
                        request.get("evaluation_surrogate"),
                    ) != (target, surrogate):
                        raise ValueError(f"request direction mismatch: {request_path.name}")
                    if request.get("target_labels_used_for_tuning") is not False:
                        raise ValueError(f"request permits target tuning: {request_path.name}")

        elif status != "PENDING_BACKBONE":
            raise ValueError(f"unsupported backbone status for {key}: {status!r}")

    if sorted(observed_pairs) != expected_pairs:
        raise ValueError("canonical pair set is not exactly C(5,2)")
    if directed_total != 20:
        raise ValueError("observed directed cell total is not 20")
    if int(matrix.get("completed_backbone_count", -1)) != complete:
        raise ValueError("completed_backbone_count drift")
    if int(matrix.get("remaining_backbone_count", -1)) != 10 - complete:
        raise ValueError("remaining_backbone_count drift")

    return {
        "canonical_backbones": 10,
        "directed_cells": 20,
        "complete": complete,
        "remaining": 10 - complete,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--request-root", default=None)
    args = ap.parse_args()
    result = validate_canonical_matrix(
        matrix_path=Path(args.matrix),
        request_root=None if args.request_root is None else Path(args.request_root),
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
