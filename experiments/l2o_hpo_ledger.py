#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

TRIAL_TRANSITIONS = {
    "GENERATED": {"REQUESTED", "REJECTED"},
    "REQUESTED": {"QUEUED", "REJECTED"},
    "QUEUED": {"RUNNING", "TERMINAL", "REJECTED"},
    "RUNNING": {"TERMINAL", "REJECTED"},
    "TERMINAL": {"PROMOTED", "REJECTED"},
    "PROMOTED": set(),
    "REJECTED": set(),
}


def new_ledger(pairs: list[str], policy_id: str) -> dict[str, Any]:
    return {
        "schema": "padataset.l2o-hpo-pilot-ledger.v2",
        "policy_id": policy_id,
        "selection_evidence": "known_validation_only",
        "pairs": {
            pair: {
                "status": "ACTIVE",
                "frozen_trial_id": None,
                "frozen_instance_id": None,
                "frozen_config_sha256": None,
                "target_open_evaluated": False,
            }
            for pair in pairs
        },
        "trials": {},
        "events": [],
    }


def _pair_state(ledger: dict[str, Any], pair: str) -> dict[str, Any]:
    if pair not in ledger["pairs"]:
        raise ValueError(f"unknown canonical pair {pair}")
    return ledger["pairs"][pair]


def register_trial(
    ledger: dict[str, Any],
    pair: str,
    trial_id: str,
    config_sha256: str,
    stage: str,
    config_path: str,
) -> dict[str, Any]:
    out = copy.deepcopy(ledger)
    pair_state = _pair_state(out, pair)
    frozen = pair_state["frozen_trial_id"]
    if frozen is not None and trial_id != frozen:
        raise ValueError(f"{pair} is frozen to {frozen}; cannot register {trial_id}")
    instance_id = f"{trial_id}__{stage}"
    if instance_id in out["trials"]:
        existing = out["trials"][instance_id]
        exact = (
            existing["canonical_pair"] == pair
            and existing["trial_id"] == trial_id
            and existing["config_sha256"] == config_sha256
            and existing["stage"] == stage
            and existing["config_path"] == config_path
        )
        if not exact:
            raise ValueError(f"trial instance {instance_id} already registered with different provenance")
        return out
    out["trials"][instance_id] = {
        "trial_id": trial_id,
        "canonical_pair": pair,
        "config_sha256": config_sha256,
        "stage": stage,
        "config_path": config_path,
        "status": "GENERATED",
    }
    out["events"].append({"type": "REGISTER", "pair": pair, "trial_id": trial_id, "instance_id": instance_id})
    return out


def transition_trial(ledger: dict[str, Any], instance_id: str, to_status: str) -> dict[str, Any]:
    out = copy.deepcopy(ledger)
    if instance_id not in out["trials"]:
        raise ValueError(f"unknown trial instance {instance_id}")
    trial = out["trials"][instance_id]
    trial_id = trial["trial_id"]
    pair_state = _pair_state(out, trial["canonical_pair"])
    frozen = pair_state["frozen_trial_id"]
    if frozen is not None and trial_id != frozen:
        raise ValueError(f"{trial['canonical_pair']} is frozen to {frozen}; cannot mutate {trial_id}")
    current = trial["status"]
    if to_status not in TRIAL_TRANSITIONS.get(current, set()):
        raise ValueError(f"invalid trial transition {current} -> {to_status}")
    trial["status"] = to_status
    out["events"].append({"type": "TRANSITION", "trial_id": trial_id, "instance_id": instance_id, "from": current, "to": to_status})
    return out


def freeze_pair(ledger: dict[str, Any], pair: str, instance_id: str) -> dict[str, Any]:
    out = copy.deepcopy(ledger)
    pair_state = _pair_state(out, pair)
    if pair_state["target_open_evaluated"]:
        raise ValueError(f"{pair}: cannot alter freeze after target-open evaluation")
    if instance_id not in out["trials"]:
        raise ValueError(f"unknown trial instance {instance_id}")
    trial = out["trials"][instance_id]
    trial_id = trial["trial_id"]
    if trial["canonical_pair"] != pair:
        raise ValueError("trial/pair mismatch")
    if trial["stage"] != "finalist" or trial["status"] != "TERMINAL":
        raise ValueError("only a terminal finalist may freeze a pair")
    existing = pair_state["frozen_trial_id"]
    if existing is not None and existing != trial_id:
        raise ValueError(f"{pair} already frozen to {existing}")
    pair_state["status"] = "FROZEN"
    pair_state["frozen_trial_id"] = trial_id
    pair_state["frozen_instance_id"] = instance_id
    pair_state["frozen_config_sha256"] = trial["config_sha256"]
    out["events"].append({"type": "FREEZE_PAIR", "pair": pair, "trial_id": trial_id, "instance_id": instance_id})
    return out


def mark_target_open_evaluated(ledger: dict[str, Any], pair: str, instance_id: str) -> dict[str, Any]:
    out = copy.deepcopy(ledger)
    pair_state = _pair_state(out, pair)
    trial = out["trials"].get(instance_id)
    if trial is None or pair_state.get("frozen_instance_id") != instance_id:
        raise ValueError("target-open evaluation requires the exact frozen finalist instance")
    pair_state["target_open_evaluated"] = True
    out["events"].append({"type": "TARGET_OPEN_EVALUATED", "pair": pair, "trial_id": trial["trial_id"], "instance_id": instance_id})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--pair", action="append", required=True)
    init.add_argument("--policy-id", default="mth602_l2o_hpo_pilot_v2")
    init.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.command == "init":
        payload = new_ledger(args.pair, args.policy_id)
        Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"pairs": len(args.pair), "out": args.out}, sort_keys=True))


if __name__ == "__main__":
    main()
