#!/usr/bin/env bash
set -euo pipefail

REPO="adamtrott78/PADataset"
STATE_ROOT="${HOME}/.cache/workspace-control/mth602-robustness-pipeline"
BACKBONES="${STATE_ROOT}/backbones"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

command -v gh >/dev/null || { echo "FINAL_RECOVERY=FAIL reason=gh-missing"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "FINAL_RECOVERY=FAIL reason=gh-auth"; exit 1; }

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

  if [[ -f "$dst/osr_posttrain_bundle/bundle_complete.json" ]]; then
    echo "FINAL_RECOVERY_SKIP run_name=$run_name reason=already-spooled"
    return
  fi

  echo "FINAL_RECOVERY_DOWNLOAD run=$run_id artifact=$artifact_name"
  mkdir -p "$dl"
  gh run download "$run_id" -R "$REPO" -n "$artifact_name" -D "$dl"

  for req in \
    config.json \
    summary.json \
    train_complete.json \
    best_model.pt \
    osr_calibration_cache/cache_complete.json \
    osr_calibration_cache/manifest.json \
    osr_posttrain_bundle/bundle_complete.json \
    osr_posttrain_bundle/frozen/frozen_methods.pt \
    osr_posttrain_bundle/frozen/methods_frozen.json \
    osr_posttrain_bundle/target_cache/manifest.json \
    osr_posttrain_bundle/target_cache/target_cache_complete.json
  do
    [[ -f "$src/$req" ]] || { echo "FINAL_RECOVERY=FAIL run=$run_id missing=$req"; exit 1; }
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
print("FINAL_RECOVERY_FIREWALL=PASS run="+b["run_name"])
PY

  rm -rf "$stage"
  cp -a "$src" "$stage"
  rm -rf "$dst"
  mv "$stage" "$dst"
  echo "FINAL_RECOVERY_SPOOLED run_name=$run_name"
}

recover_one 45967790240 padataset-scientific-45967790240 mth602_final_robust_PA1_PA3_p01_t00 g0a
recover_one 45967794463 padataset-scientific-45967794463 mth602_final_robust_PA1_PA3_p03_t00 g0b
recover_one 45967800409 padataset-scientific-45967800409 mth602_final_robust_PA1_PA4_p01_t00 g0c
recover_one 45967920737 padataset-scientific-2-45967920737 mth602_final_robust_PA1_PA2_p04_t00 g1a
recover_one 45967925080 padataset-scientific-2-45967925080 mth602_final_robust_PA1_PA3_p02_t00 g1b
recover_one 45967929365 padataset-scientific-2-45967929365 mth602_final_robust_PA1_PA3_p04_t00 g1c
recover_one 45967934043 padataset-scientific-2-45967934043 mth602_final_robust_PA1_PA4_p02_t00 g1d

echo "FINAL_RECOVERY=PASS attempted=7"
