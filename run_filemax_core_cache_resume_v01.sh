#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-$HOME/adamArchives/Adam/varMax/PADataset}"
PY="${PY:-$(command -v python)}"

CORE_BANK="${CORE_BANK:-ota_core_high_run01}"
CORE_NOISE="${CORE_NOISE:-high_run01}"
CACHE_LEN="${CACHE_LEN:-16384}"
CACHE_ROOT="${CACHE_ROOT:-$REPO/_feature_cache_nvme/len${CACHE_LEN}/norm/ota__${CORE_BANK}__${CORE_NOISE}}"

PROTOCOLS="${PROTOCOLS:-wifi bluetooth zigbee}"
CORE_SHARDS="${CORE_SHARDS:-1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20}"

CACHE_FILE_JOBS="${CACHE_FILE_JOBS:-60}"

cd "$REPO"

mkdir -p results/cache_workers results/buh_logs "$CACHE_ROOT"

TS="$(date +%Y%m%d_%H%M%S)"
LOG="results/buh_logs/filemax_core_cache_resume_${TS}.log"
TASKS="results/cache_workers/filemax_core_cache_resume_tasks_${TS}.txt"
JOBLOG="results/cache_workers/filemax_core_cache_resume_joblog_${TS}.txt"

exec > >(tee -a "$LOG") 2>&1

echo "=== FILEMAX CORE CACHE RESUME $TS ==="
echo "REPO=$REPO"
echo "PY=$PY"
echo "CORE_BANK=$CORE_BANK"
echo "CORE_NOISE=$CORE_NOISE"
echo "CACHE_ROOT=$CACHE_ROOT"
echo "CACHE_FILE_JOBS=$CACHE_FILE_JOBS"
echo ""

LATEST_LOG="$(ls -t results/cache_workers/filemax_core_cache_*_all.log 2>/dev/null | head -n 1 || true)"
echo "Latest previous filemax log: ${LATEST_LOG:-NONE}"

python - <<'PY' > "$TASKS"
from pathlib import Path
import os, re, sys

repo = Path.cwd()
core_bank = os.environ.get("CORE_BANK", "ota_core_high_run01")
cache_root = repo / os.environ.get(
    "CACHE_ROOT",
    "_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01"
)

protocols = os.environ.get("PROTOCOLS", "wifi bluetooth zigbee").split()
shards = [int(x) for x in os.environ.get(
    "CORE_SHARDS",
    "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"
).split()]

logs = sorted((repo / "results/cache_workers").glob("filemax_core_cache_*_all.log"), key=lambda p: p.stat().st_mtime)
latest_log = logs[-1] if logs else None

done_stems = set()
if latest_log:
    for line in latest_log.read_text(errors="ignore").splitlines():
        m = re.search(r"FILECACHE DONE \| proto=([^|]+) \| shard=(\d{3}) \| src=([^|]+)", line)
        if not m:
            continue
        src = m.group(3).strip()
        stem = Path(src).name.replace(".mat", "")
        done_stems.add(stem)

all_tasks = []

for proto in protocols:
    for sh in shards:
        sh3 = f"{sh:03d}"
        bank_dir = repo / "data" / proto / "ota" / core_bank

        mats = []
        mats += sorted(bank_dir.glob(f"{core_bank}__shard_{sh3}__PA1__part_*_of_*.mat"))
        for pa in ["PA2", "PA3", "PA4", "PA8"]:
            mats += sorted(bank_dir.glob(f"{core_bank}__shard_{sh3}__{pa}.mat"))

        for mat in mats:
            stem = mat.name.replace(".mat", "")
            rel = mat.relative_to(repo / "data")

            if stem in done_stems:
                continue

            # Delete partial or unconfirmed h5 outputs for this stem.
            for h5 in cache_root.glob(f"*{stem}.h5"):
                try:
                    h5.unlink()
                except FileNotFoundError:
                    pass

            all_tasks.append((proto, sh3, str(rel)))

# Shuffle enough to avoid front-loading one protocol/shard forever.
# Deterministic sort by PA-ish item then protocol would be okay, but simple lexical output is stable.
# GNU parallel rolling pool handles this; shuf can be applied by shell if desired.
for proto, sh3, rel in all_tasks:
    print(proto, sh3, rel)

print(f"#RESUME_TASKS={len(all_tasks)}", file=sys.stderr)
print(f"#DONE_STEMS_FROM_LOG={len(done_stems)}", file=sys.stderr)
PY

TASK_COUNT="$(grep -v '^#' "$TASKS" | wc -l)"
echo "Resume task count: $TASK_COUNT"
echo "Expected if previous DONE=28: $((360 - 28))"

if [[ "$TASK_COUNT" -le 0 ]]; then
  echo "Nothing to resume."
  exit 0
fi

awk '
  NF != 3 {
    print "BAD TASK LINE", NR, $0;
    bad=1
  }
  END { exit bad }
' "$TASKS"

# Randomize task order so no protocol/PA bottleneck front-loads the queue.
shuf "$TASKS" > "${TASKS}.shuf"
mv "${TASKS}.shuf" "$TASKS"

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

export REPO PY CACHE_ROOT CACHE_LEN CORE_BANK CORE_NOISE TS

echo ""
echo "=== START RESUME FILE-LEVEL CACHE ==="

set +e
parallel --line-buffer --colsep ' ' \
  --joblog "$JOBLOG" \
  --tag --tagstring '{1}|shard={2}|{3}' \
  -j "$CACHE_FILE_JOBS" \
'
  set -euo pipefail

  proto={1}
  sh3={2}
  rel={3}
  stem=$(basename "$rel" .mat)

  echo "FILECACHE START | proto=${proto} | shard=${sh3} | src=${rel}"

  "$PY" "$REPO/cacheBuild.py" \
    --data-root "$REPO/data" \
    --cache-root "$CACHE_ROOT" \
    --cache-len "$CACHE_LEN" \
    --normalize \
    --source-type ota \
    --source-name "$CORE_BANK" \
    --dataset-tag "$CORE_BANK" \
    --noise-tag "$CORE_NOISE" \
    --source-glob "$rel" \
    2>&1 | tee "results/cache_workers/filemax_resume_${proto}_shard_${sh3}_${stem}_${TS}.log"

  h5=$(find "$CACHE_ROOT" -maxdepth 1 -type f -name "*${stem}.h5" | head -n 1 || true)
  if [[ -z "$h5" || ! -f "$h5" ]]; then
    echo "ERROR: h5 not found after cache | src=${rel} | stem=${stem}"
    exit 3
  fi

  bytes=$(stat -c%s "$h5")
  echo "FILECACHE DONE | proto=${proto} | shard=${sh3} | src=${rel} | h5=${h5} | bytes=${bytes}"
' :::: "$TASKS" \
  2>&1 | tee "results/cache_workers/filemax_core_cache_resume_${TS}_all.log"

PAR_STATUS=${PIPESTATUS[0]}
set -e

echo ""
echo "=== RESUME FINISHED ==="
echo "parallel status: $PAR_STATUS"
echo "Joblog: $JOBLOG"

echo ""
echo "=== COUNTS ==="
H5_COUNT="$(find "$CACHE_ROOT" -maxdepth 1 -type f -name '*.h5' | wc -l)"
echo "Visible h5 count: $H5_COUNT / 360"
du -sh "$CACHE_ROOT" || true

echo ""
echo "=== JOB FAILURES ==="
awk 'NR==1 || $7 != 0 {print}' "$JOBLOG" | column -t | tail -n 100 || true

if [[ "$PAR_STATUS" != "0" ]]; then
  echo "WARNING: one or more resume jobs failed. Inspect joblog above."
  exit "$PAR_STATUS"
fi

echo "DONE: resume completed."
