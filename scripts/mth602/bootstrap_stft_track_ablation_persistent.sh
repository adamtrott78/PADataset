#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${REPO_URL:-https://github.com/adamtrott78/PADataset.git}"
EXPECTED_SHA="${EXPECTED_SHA:-}"
CHECKOUT="${CHECKOUT:-$HOME/adamArchives/worktrees/PADataset-stft-track-ablation-v1}"

[[ "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]] || {
  echo "EXPECTED_SHA must be an exact 40-character lowercase Git SHA" >&2
  exit 20
}

git_retry() {
  local attempt rc
  for attempt in 1 2 3 4 5; do
    if "$@"; then
      return 0
    fi
    rc=$?
    echo "Git operation failed (attempt $attempt/5, rc=$rc); retrying..." >&2
    sleep $((attempt * 2))
  done
  return "$rc"
}

mkdir -p "$(dirname "$CHECKOUT")"

if [[ ! -d "$CHECKOUT/.git" ]]; then
  rm -rf "$CHECKOUT"
  mkdir -p "$CHECKOUT"
  git -C "$CHECKOUT" init --quiet
  git -C "$CHECKOUT" remote add origin "$REPO_URL"
fi

git_retry git -C "$CHECKOUT" -c http.version=HTTP/1.1 fetch \
  --quiet --depth=1 --no-tags origin "$EXPECTED_SHA"
git -C "$CHECKOUT" reset --hard FETCH_HEAD

ACTUAL_SHA="$(git -C "$CHECKOUT" rev-parse HEAD)"
[[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]] || {
  echo "Persistent checkout SHA mismatch: $ACTUAL_SHA != $EXPECTED_SHA" >&2
  exit 21
}

echo "PERSISTENT_STFT_CHECKOUT=$CHECKOUT"
echo "PERSISTENT_STFT_HEAD=$ACTUAL_SHA"
echo "PERSISTENT_STFT_CACHE=$HOME/adamArchives/Adam/varMax/PADataset/_feature_cache_nvme/len16384/norm_stfttracks64_v1/ota__ota_core_high_run01__high_run01"

exec bash "$CHECKOUT/scripts/mth602/run_stft_track_ablation_local.sh"
