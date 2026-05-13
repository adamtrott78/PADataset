#!/usr/bin/env bash
set -euo pipefail

REPO="$HOME/adamArchives/Adam/varMax/PADataset"
cd "$REPO"

APPLY=0
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
fi

say() {
  printf '%s\n' "$*"
}

run() {
  if [[ "$APPLY" == "1" ]]; then
    say "+ $*"
    eval "$@"
  else
    say "[DRY RUN] $*"
  fi
}

tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

move_path() {
  local src="$1"
  local dst="$2"

  if [[ ! -e "$src" && ! -L "$src" ]]; then
    say "[SKIP missing] $src"
    return 0
  fi

  local dstdir
  dstdir="$(dirname "$dst")"
  run "mkdir -p \"${dstdir}\""

  if tracked "$src"; then
    run "git mv \"${src}\" \"${dst}\""
  else
    run "mv \"${src}\" \"${dst}\""
  fi
}

copy_note() {
  local path="$1"
  local text="$2"
  if [[ "$APPLY" == "1" ]]; then
    mkdir -p "$(dirname "$path")"
    printf '%s\n' "$text" > "$path"
    say "+ wrote $path"
  else
    say "[DRY RUN] write $path"
  fi
}

append_gitignore_once() {
  local line="$1"
  if grep -qxF "$line" .gitignore 2>/dev/null; then
    say "[OK gitignore already has] $line"
  else
    if [[ "$APPLY" == "1" ]]; then
      printf '%s\n' "$line" >> .gitignore
      say "+ appended to .gitignore: $line"
    else
      say "[DRY RUN] append to .gitignore: $line"
    fi
  fi
}

say "=== PADataset spring clean ==="
say "REPO=$REPO"
say "MODE=$([[ "$APPLY" == "1" ]] && echo APPLY || echo DRY_RUN)"
say ""

say "=== Safety precheck ==="
git status --short || true
say ""

if [[ "$APPLY" == "1" ]]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    say "ERROR: You have tracked modifications already."
    say "Commit/stash them first, or run on a cleanup branch after reviewing git status."
    exit 2
  fi

  branch="cleanup/final-experiment-system"
  current="$(git branch --show-current || true)"
  if [[ "$current" != "$branch" ]]; then
    if git rev-parse --verify "$branch" >/dev/null 2>&1; then
      git checkout "$branch"
    else
      git checkout -b "$branch"
    fi
  fi
fi

say ""
say "=== Create final structure ==="
for d in \
  legacy/notebooks/pa_cnn_osr \
  legacy/notebooks/non_pa \
  legacy/preprocessing/buh_pipeline \
  legacy/scratch/root \
  legacy/txrx_debug \
  legacy/txrx_old_versions \
  scripts/preprocess \
  scripts/train \
  scripts/osr \
  experiments \
  docs/cleanup \
  local_artifacts/audits \
  local_artifacts/handoffs \
  local_artifacts/generated_tables \
  local_artifacts/logs \
  local_artifacts/large_data_exports \
  local_artifacts/matlab_workspace \
  local_artifacts/system_specs
do
  run "mkdir -p \"$d\""
done

say ""
say "=== Move PA CNN/OSR notebooks to legacy ==="
move_path "PADiscriminate.ipynb" "legacy/notebooks/pa_cnn_osr/PADiscriminate.ipynb"
move_path "PAEvaluate.ipynb" "legacy/notebooks/pa_cnn_osr/PAEvaluate.ipynb"
move_path "PAValidate.ipynb" "legacy/notebooks/pa_cnn_osr/PAValidate.ipynb"

say ""
say "=== Move unrelated/non-PA notebooks to legacy ==="
move_path "CNN_CICIDS_runtime.ipynb" "legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb"
move_path "DQN_CICIDS_Part_v2.ipynb" "legacy/notebooks/non_pa/DQN_CICIDS_Part_v2.ipynb"
move_path "DQN_UNSW.ipynb" "legacy/notebooks/non_pa/DQN_UNSW.ipynb"
move_path "cnn_unsw.ipynb" "legacy/notebooks/non_pa/cnn_unsw.ipynb"

say ""
say "=== Preserve buh preprocessing pipeline artifacts ==="
move_path "buh_orchestrate.sh" "legacy/preprocessing/buh_pipeline/buh_orchestrate.sh"
move_path "run_buh.sh" "legacy/preprocessing/buh_pipeline/run_buh.sh"
move_path "buh_capture.m" "legacy/preprocessing/buh_pipeline/buh_capture.m"
move_path "buh.m" "legacy/preprocessing/buh_pipeline/buh.m"
move_path "buh.txt" "legacy/preprocessing/buh_pipeline/buh.txt"
move_path "pipeline_status_buh.sh" "legacy/preprocessing/buh_pipeline/pipeline_status_buh.sh"

say ""
say "=== Move root scratch/test files ==="
move_path "tiny_plot_test.m" "legacy/scratch/root/tiny_plot_test.m"
move_path "untitled.m" "legacy/scratch/root/untitled.m"

say ""
say "=== Move txrx debug utilities and old versions ==="
move_path "txrx/seek.m" "legacy/txrx_debug/seek.m"
move_path "txrx/seek.py" "legacy/txrx_debug/seek.py"
move_path "txrx/seek_debug_once.m" "legacy/txrx_debug/seek_debug_once.m"
move_path "txrx/seek_pretty_one.m" "legacy/txrx_debug/seek_pretty_one.m"
move_path "txrx/tiny_plot_test.m" "legacy/txrx_debug/tiny_plot_test.m"
move_path "txrx/splice.ipynb" "legacy/txrx_debug/splice.ipynb"
move_path "txrx/rx_capture_tape_old.m" "legacy/txrx_old_versions/rx_capture_tape_old.m"
move_path "txrx/tx_stream_tape_old.m" "legacy/txrx_old_versions/tx_stream_tape_old.m"

say ""
say "=== Move preprocessing orchestration shell scripts ==="
move_path "run_filemax_core_cache_v01.sh" "scripts/preprocess/run_filemax_core_cache_v01.sh"
move_path "run_filemax_core_cache_resume_v01.sh" "scripts/preprocess/run_filemax_core_cache_resume_v01.sh"
move_path "run_missing_h5_cache_v01.sh" "scripts/preprocess/run_missing_h5_cache_v01.sh"
move_path "run_pa1_split_bank_v01.sh" "scripts/preprocess/run_pa1_split_bank_v01.sh"
move_path "run_unified_core_splitpa1_cache_v01.sh" "scripts/preprocess/run_unified_core_splitpa1_cache_v01.sh"
move_path "run_unified_core_splitpa1_cache_v02.sh" "scripts/preprocess/run_unified_core_splitpa1_cache_v02.sh"
move_path "run_unified_core_splitpa1_cache_v03.sh" "scripts/preprocess/run_unified_core_splitpa1_cache_v03.sh"
move_path "merge_relabel_cache_all_now.sh" "scripts/preprocess/merge_relabel_cache_all_now.sh"
move_path "pipeline_status.sh" "scripts/preprocess/pipeline_status.sh"

say ""
say "=== Move local generated artifacts out of repo root ==="
move_path "bluetooth_pilot_noisy_torch.tar.gz" "local_artifacts/large_data_exports/bluetooth_pilot_noisy_torch.tar.gz"
move_path "wifi_pilot_noisy_torch.tar.gz" "local_artifacts/large_data_exports/wifi_pilot_noisy_torch.tar.gz"
move_path "zigbee_pilot_noisy_torch.tar.gz" "local_artifacts/large_data_exports/zigbee_pilot_noisy_torch.tar.gz"

move_path "matlab.mat" "local_artifacts/matlab_workspace/matlab.mat"

move_path "confmanifold_coarse_leaderboard.csv" "local_artifacts/generated_tables/confmanifold_coarse_leaderboard.csv"
move_path "confmanifold_refined_leaderboard.csv" "local_artifacts/generated_tables/confmanifold_refined_leaderboard.csv"
move_path "experiment_leaderboard.csv" "local_artifacts/generated_tables/experiment_leaderboard.csv"
move_path "osr_backbone_bank_leaderboard.csv" "local_artifacts/generated_tables/osr_backbone_bank_leaderboard.csv"
move_path "ota_btzb_leaderboard_pa8.csv" "local_artifacts/generated_tables/ota_btzb_leaderboard_pa8.csv"
move_path "ota_btzb_varmax_oracle_eval.csv" "local_artifacts/generated_tables/ota_btzb_varmax_oracle_eval.csv"
move_path "top_backbone_osr_eval.csv" "local_artifacts/generated_tables/top_backbone_osr_eval.csv"
move_path "varmax_final_setup_eval.csv" "local_artifacts/generated_tables/varmax_final_setup_eval.csv"

move_path "ota_core_build.log" "local_artifacts/logs/ota_core_build.log"
move_path "ota_expanded_wifi_only_build.log" "local_artifacts/logs/ota_expanded_wifi_only_build.log"
move_path "validate_smoke.log" "local_artifacts/logs/validate_smoke.log"

move_path "pipeline_refactor_inputs.tgz" "local_artifacts/handoffs/pipeline_refactor_inputs.tgz"
move_path "resplice_patch_inputs.tar.gz" "local_artifacts/handoffs/resplice_patch_inputs.tar.gz"
move_path "PADataset_training_handoff_20260512_035606.tar.gz" "local_artifacts/handoffs/PADataset_training_handoff_20260512_035606.tar.gz"
move_path "PADataset_training_handoff_20260512_035606" "local_artifacts/handoffs/PADataset_training_handoff_20260512_035606"

move_path "lambda_specs_screen.sh" "local_artifacts/system_specs/lambda_specs_screen.sh"
move_path "lambda_specs_screen_L1F6NMTVSM_2026-05-13_002844.txt" "local_artifacts/system_specs/lambda_specs_screen_L1F6NMTVSM_2026-05-13_002844.txt"

move_path "make_cleanup_audit_lean.sh" "local_artifacts/audits/make_cleanup_audit_lean.sh"
move_path "make_cleanup_audit_safe.sh" "local_artifacts/audits/make_cleanup_audit_safe.sh"
move_path "PADataset_cleanup_audit_LEAN_20260513_022556.tgz" "local_artifacts/audits/PADataset_cleanup_audit_LEAN_20260513_022556.tgz"

say ""
say "=== Add README placeholders for new final system ==="
copy_note "experiments/README.md" "# PADataset final experiment system

This directory is reserved for the replacement CNN/OSR experiment control plane.

Target design:
- manifest-driven training
- one run per worker process
- GPU-aware launch scripts
- artifact-verified completion
- dashboarded progress
- resumable sweeps
- post-run aggregation
- OSR evaluation from saved run artifacts

The old notebook UI has been moved to legacy/notebooks/pa_cnn_osr.
"

copy_note "scripts/train/README.md" "# Training launch scripts

This directory is reserved for GNU-parallel based training launchers.

Expected future files:
- run_pa_train_parallel.sh
- resume_pa_train_parallel.sh
"

copy_note "scripts/osr/README.md" "# OSR evaluation launch scripts

This directory is reserved for manifest-driven OSR evaluation launchers.

Expected future files:
- run_pa_osr_parallel.sh
- resume_pa_osr_parallel.sh
"

copy_note "scripts/preprocess/README.md" "# Preprocessing orchestration scripts

This directory contains preserved preprocessing/cache orchestration scripts.

These scripts are artifacts of the OTA banking/caching pipeline and remain useful as references for the final experiment runner design.
"

copy_note "legacy/README.md" "# Legacy material

This directory contains preserved historical notebooks, scratch files, old txrx versions, and preprocessing artifacts.

Nothing here is deleted; the goal is to remove obsolete operating interfaces from the repo root while keeping provenance.
"

copy_note "docs/cleanup/spring_clean.md" "# Spring clean

This cleanup pass preserves core dataset generation and CNN/OSR library code while moving notebook-era interfaces and local artifacts out of the active repo root.

Preserved as core:
- prepData.py
- discriminate.py
- evaluate.py
- osr_core.py
- varmax_osr.py
- dqn_osr.py
- cacheBuild.py
- manifestBuild.py
- core/
- protocol/
- txrx/ current capture/splice files
- tools/
- config/

Preserved as historical artifacts:
- buh_orchestrate.sh
- run_buh.sh
- buh_capture.m
- buh.m
- buh.txt
- pipeline_status_buh.sh

New intended operating model:
manifest -> parallel launcher -> one-run worker -> verified artifacts -> dashboard -> reducer -> OSR evaluation.
"

say ""
say "=== Update .gitignore for local-only artifacts ==="
append_gitignore_once "/local_artifacts/"
append_gitignore_once "/PADataset_cleanup_audit_*.tgz"
append_gitignore_once "/make_cleanup_audit_*.sh"

say ""
say "=== Optional: remove ignored Jupyter checkpoint dirs from active source tree ==="
say "Not deleting automatically. After review, you may run:"
say "find . -path './.git' -prune -o -type d -name '.ipynb_checkpoints' -print -exec rm -rf {} +"

say ""
say "=== Final status ==="
git status --short || true

if [[ "$APPLY" == "0" ]]; then
  say ""
  say "DRY RUN complete. No changes were made."
  say "To apply:"
  say "  bash spring_clean_padataset_v01.sh --apply"
else
  say ""
  say "APPLY complete."
  say "Review with:"
  say "  git status --short"
  say "  find . -maxdepth 2 -type d | sort | sed -n '1,120p'"
  say ""
  say "Then commit if it looks good:"
  say "  git add .gitignore experiments scripts legacy docs"
  say "  git commit -m 'Reorganize PADataset for final parallel experiment system'"
fi
