#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${REPO_URL:-https://github.com/adamtrott78/PADataset.git}"
BRANCH="${BRANCH:-mth602-stft-track-ablation-v1}"
CHECKOUT="${CHECKOUT:-$HOME/adamArchives/worktrees/PADataset-stft-track-ablation-v1}"

mkdir -p "$(dirname "$CHECKOUT")"

if [[ ! -d "$CHECKOUT/.git" ]]; then
  rm -rf "$CHECKOUT"
  git clone --no-checkout "$REPO_URL" "$CHECKOUT"
fi

git -C "$CHECKOUT" fetch --no-tags origin "$BRANCH"
HEAD_SHA="$(git -C "$CHECKOUT" rev-parse "origin/$BRANCH")"
git -C "$CHECKOUT" reset --hard "$HEAD_SHA"

echo "PERSISTENT_STFT_CHECKOUT=$CHECKOUT"
echo "PERSISTENT_STFT_HEAD=$HEAD_SHA"
echo "PERSISTENT_STFT_CACHE=$HOME/adamArchives/Adam/varMax/PADataset/_feature_cache_nvme/len16384/norm_stfttracks64_v1/ota__ota_core_high_run01__high_run01"

exec bash "$CHECKOUT/scripts/mth602/run_stft_track_ablation_local.sh"
