#!/usr/bin/env bash
set -euo pipefail

REPO="adamtrott78/PADataset"
STATE_ROOT="$HOME/.cache/workspace-control/mth602-robustness-pipeline"
BACKBONES="$STATE_ROOT/backbones"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

command -v gh >/dev/null || { echo "RECOVERY=FAIL reason=gh-missing"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "RECOVERY=FAIL reason=gh-auth"; exit 1; }

echo "RECOVERY_PREPARE_SPOOL path=$BACKBONES"
sudo -v
sudo mkdir -p "$BACKBONES"
sudo chown -R "$USER:$(id -gn)" "$BACKBONES"

recover_one() {
  local run_id="$1"
  local artifact_name="$2"
  local run_name="$3"
  local slot="$4"
  local dl="$TMP/$slot"
  local src="$dl/scientific-results/backbone/$run_name"
  local dst="$BACKBONES/$run_name"
  local stage="$BACKBONES/.${run_name}.recovering"

  echo "RECOVERY_DOWNLOAD run=$run_id artifact=$artifact_name"
  mkdir -p "$dl"
  gh run download "$run_id" -R "$REPO" -n "$artifact_name" -D "$dl"

  for req in     config.json     train_complete.json     osr_calibration_cache/cache_complete.json     osr_calibration_cache/manifest.json     osr_posttrain_bundle/bundle_complete.json     osr_posttrain_bundle/frozen/frozen_methods.pt     osr_posttrain_bundle/frozen/methods_frozen.json     osr_posttrain_bundle/target_cache/manifest.json     osr_posttrain_bundle/target_cache/target_cache_complete.json
  do
    [[ -f "$src/$req" ]] || { echo "RECOVERY=FAIL run=$run_id missing=$req"; exit 1; }
  done

  python3 - "$src" <<'PY'
import json, pathlib, sys
p=pathlib.Path(sys.argv[1])
b=json.loads((p/"osr_posttrain_bundle/bundle_complete.json").read_text())
f=json.loads((p/"osr_posttrain_bundle/frozen/methods_frozen.json").read_text())
t=json.loads((p/"osr_posttrain_bundle/target_cache/manifest.json").read_text())
assert b["status"]=="SUCCESS"
assert b["methods_frozen_before_target_test"] is True
assert b["target_test_consumed_before_method_fit"] is False
assert f["status"]=="SUCCESS"
assert f["target_test_materialized_before_freeze"] is False
assert f["target_test_consumed_before_method_fit"] is False
assert t["status"]=="SUCCESS"
assert t["methods_frozen_before_target_test"] is True
assert t["target_labels_used_for_tuning"] is False
assert t["target_test_consumed_before_method_fit"] is False
assert b["methods_frozen_sha256"]==f["frozen_methods_sha256"]==t["methods_frozen_sha256"]
print("RECOVERY_FIREWALL=PASS run="+b["run_name"])
PY

  rm -rf "$stage"
  cp -a "$src" "$stage"
  rm -rf "$dst"
  mv "$stage" "$dst"
  echo "RECOVERY_SPOOLED run_name=$run_name"
}

recover_one 45860162828 padataset-scientific-45860162828 mth602_robust_smoke_A_PA1_PA2_p01_t00 g0
recover_one 45860165260 padataset-scientific-2-45860165260 mth602_robust_smoke_A_PA3_PA8_p01_t00 g1

echo "RECOVERY=PASS spooled=2"
