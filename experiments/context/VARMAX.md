# VarMax calibration and evaluation

Read this to evaluate a saved PyTorch backbone with VarMax, compare calibration
regimes, or investigate a threshold sweep. The [experiment framework](../CONTEXT.md)
owns configs, manifests, GPU scheduling and run completion. The
[backbone context](BACKBONE.md) owns tensor and checkpoint contracts.

## Source and decision model

| Source | Responsibility |
|---|---|
| [varmax_osr.py](../../varmax_osr.py), `VarMaxOSR` | Evidence, class bands, surrogate construction, sweep selection and rejection |
| [pa_eval_osr_one.py](../pa_eval_osr_one.py) | CLI, fixed sweep policy and compact result CSV |
| [evaluate.py](../../evaluate.py) | Validation/test bundles and method execution |
| [osr_core.py](../../osr_core.py) | Backbone reload and OSR metrics |

This implementation accepts a window if **any** of these conditions passes:
top-two softmax probability gap reaches a global threshold; variance lies inside
the predicted class's band; or energy lies inside that class's band when energy
is enabled. A window is unknown only when all enabled acceptance tests fail.
This is distinct from DQNGuard's DQN decision plus guard or continuous-score cutoff.

Variance is variance of absolute logits, not embedding variance. Energy is
positive `T*logsumexp(logits/T)`; probability gap uses softmax at temperature T.
The CLI fixes T=1, energy enabled, and predicted-class band fitting. A class group
with fewer than five fit windows falls back to its true-class group, then to
pooled fit values. Band endpoints are inclusive.

The continuous unknown score combines normalized probability-gap deficit and,
only below the gap threshold, normalized distances outside variance/energy bands.
It supports AUROC ranking; the final decision still uses the acceptance rules.
An accepted window can have a positive unknown score. Do not replace the rule
with `score > 0` or import DQNGuard's 5% percentile cutoff.

## Choose a calibration regime

| CLI mode | Calibration evidence |
|---|---|
| `surrogate_all` | Each known class is considered as a pseudo-unknown in a validation score subset |
| `surrogate_aligned` | Only the mapped known-class pseudo-unknown |
| `surrogate_mismatched` | Known-class pseudo-unknowns other than the mapped class |
| `oracle` | Labeled target-open validation, preferably balanced with known validation |

For surrogate modes, known validation is split within each true class into
approximately 50% fit, 25% guard and 25% score, with at least one window in each
part. Fewer than three windows in a class is an error. Bands use the fit part,
known retention uses the guard part, and one class in the score part is treated
as open. That pseudo-unknown class remains in the backbone's training classes
and the fit/guard sets. This is not leave-one-class-out retraining, and it is
not external Scan-surrogate calibration as used by [DQNGuard](DQNGUARD.md).

The current alignment map is PA2↔PA8 and PA3↔PA4. PA1 has no mapped partner.
Aligned mode requires the mapped class in the backbone's known class names;
it errors otherwise. When no aligned class exists, mismatched/all can still
consider the available known classes. In `surrogate_all`, candidates from all
specifications compete for one selected result; the method does not average
their decisions into an ensemble.

The general CLI defaults to `oracle,surrogate_all`. Specify the mode explicitly.
Its oracle builder requires target validation; it does not deliberately use test
data. The lower-level VarMax API can fall back to `payload.test_open` when open
calibration is omitted, so custom callers must pass explicit validation splits.

## Run one surrogate evaluation

Use a completed, reviewed 8192-length PyTorch run and validated cache from the
framework workflow. The example below consumes its one-epoch demonstration run;
it checks execution rather than reproducing paper performance. Run in `(DNNs)`
from the repository root. Pick a free GPU and a new output directory.

```bash
cd ~/adamArchives/Adam/varMax/PADataset
export PA_VARMAX_RUN="results_pa_context_train01/context_og_ref_unkPA2_c8192_seed0"
export PA_VARMAX_OUT="results_pa_context_varmax01/og_PA2_surrogate_all"
python - <<'PY'
import json
import os
from pathlib import Path
run = Path(os.environ['PA_VARMAX_RUN'])
cfg = json.loads((run / 'config.json').read_text())
assert cfg['split_mode'] == 'open_pa' and cfg['unknown_pas'] == ['PA2']
assert cfg['cache_len'] == 8192 and cfg['skip_cache_build']
assert (run / 'best_model.pt').is_file()
assert not Path(os.environ['PA_VARMAX_OUT']).exists(), 'Choose a fresh output directory.'
PY
CUDA_VISIBLE_DEVICES=0 python experiments/pa_eval_osr_one.py \
  --run-dir "$PA_VARMAX_RUN" --checkpoint best_model \
  --out-dir "$PA_VARMAX_OUT" --method-family varmax \
  --modes surrogate_all --sweep-grid smoke \
  --device cuda --batch-size 64 --num-workers 0
```

The direct command acquires no shared GPU lock. For scheduled matrices use the
framework's evaluation manifest and wrapper. The target comes from saved
`unknown_pas`; there is no `--held-out` argument. Actual cache shape and data
identity still need the [preprocessing checks](../../scripts/preprocess/CONTEXT.md).

## Compare modes or increase the sweep

For a diagnostic comparison, rerun the command with
`--modes oracle,surrogate_all` and a fresh output directory. Expect two method
rows, and label the oracle's target-validation access explicitly. For aligned
versus mismatched tests, use `--modes surrogate_aligned,surrogate_mismatched`
only after checking the alignment map and saved known classes.

`--sweep-grid full` expands the search; it does not select an established paper
profile. Smoke has 3 gap thresholds × 9 variance bands × 9 energy bands = 243
candidates per surrogate specification. Full has 8 × 36 × 36 = 10,368.
Gap grid entries such as 0.95 are **absolute probability-gap thresholds**;
variance/energy grid entries are percentile endpoints.

The CLI fixes known accuracy and macro-F1 floors at 95% of the closed-set known
calibration baselines, per-class recall floors at 95% of the guard baselines,
and pseudo/open recall at least 0.60. These are feasibility constraints, not a
5% known-rejection budget. Feasible candidates rank by OSR macro F1, then smaller
absolute bias delta, then unknown F1. If none is feasible, the code still chooses
a fallback, ranked by unknown recall, known macro F1 and OSR macro F1. A successful
process therefore does not establish that the retention constraints were met.

The bare Python `VarMaxOSR.fit(payload)` instead fits fixed percentile settings
on known validation without this CLI sweep. Preserve which fitting path was used.

## Inspect outputs and diagnose fallback

The CLI writes `osr_summary.csv`, `osr_progress.json`, and
`osr_complete.json` on success; failures produce `osr_error.json`. Inspect the
process result and all requested method rows. Existing output paths can be
overwritten; an old marker alone cannot establish success for a new invocation.

Check `calibration_mode`, `best_spec_name`, `best_heldout_class_name`,
`no_feasible_solution`, `best_feasible`, selected gap/band settings, known
rejection, unknown precision/recall/F1, OSR macro F1 and AUROC. If fallback was
chosen, report that fact rather than claiming the configured floors held.

The CSV's `sweep_candidates` is misleading: it counts retained top feasible
plus top fallback entries (at most 20), not all candidates evaluated. Progress
uses `sweep_candidates` for the full count. These different generated fields
do not change the source-defined search. The CLI does not persist the entire
sweep history or fitted numeric class-band dictionary. Custom analysis can
inspect the returned fitted method and `get_params()`; preserve that information
explicitly if required, along with config, checkpoint, command, source and logs.

Interfaces checked against source at
`5541d7635bef987ee6d56b0d6b91521b1e439371`. Documentation examples were checked
statically; no backbone inference or threshold sweep was run during authoring.
