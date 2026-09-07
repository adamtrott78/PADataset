# Results, analysis and paper assets

Read this to collect run summaries, build a Target–Surrogate Matrix, regenerate
the main comparison table, or resolve disagreement between generated artifacts.
The [experiment framework](../CONTEXT.md) owns run lifecycle. Method contracts
are in [DQNGuard](DQNGUARD.md), [VarMax](VARMAX.md) and
[DQN-IDS adaptation](DQN_IDS.md).

## Source ownership and evidence boundary

| Tracked source | Responsibility |
|---|---|
| [pa_reduce_train_summaries.py](../pa_reduce_train_summaries.py) | Collect training summaries with source paths |
| [pa_reduce_osr_summaries.py](../pa_reduce_osr_summaries.py) | Collect evaluation rows with source paths |
| [make_target_surrogate_matrix.py](../../papers/milcom2026/figures/target_surrogate_matrix/make_target_surrogate_matrix.py) | Existing pair metrics → paper matrix PDF/PNG/CSV |
| [make_main_results_table.py](../../papers/milcom2026/tables/main_results/make_main_results_table.py) | Comparison rows → fold statistics and LaTeX table |

Generated CSVs, figures, tables and runtime indexes describe particular
executions; they do not define algorithms or establish final-paper provenance.
Preserve the chain: source revision/diff → data/cache identity → saved config
and checkpoint → evaluator command/calibration → per-run summary → selected
rows → aggregate → paper asset. Record the reason for each inclusion/exclusion.

Large datasets, checkpoints and results can exist only on Lambda through ignored
paths or symlinks. A GitHub checkout lacking them cannot reproduce experiments
merely by running a plot script. Rendering existing CSVs needs pandas, NumPy and
Matplotlib; it does not need radios, caches or trained models.

The author confirms 8192 pooled length for final paper experiments and identifies
16384 runs as exploratory. Supplied historical comparison/matrix CSVs were traced
to 16384 run configs and sampled caches. Rendering those CSVs verifies their
data-to-asset path, not their identity as the final 8192 paper evidence. Do not
rewrite measurements or relabel run provenance to remove that distinction.

## Collect a scoped set of summaries

Run from the repository root in the existing environment. Replace these roots
with the intended campaign; the defaults below continue the framework examples.

```bash
python experiments/pa_reduce_train_summaries.py \
  --results-root results_pa_context_train01 \
  --out results/context_analysis01/train_rows.csv
python experiments/pa_reduce_osr_summaries.py \
  --results-root results_pa_context_osr01 \
  --out results/context_analysis01/osr_rows.csv
```

Both reducers search exactly one child-directory level:
`*/summary.json` or `*/osr_summary.csv`. They concatenate, not recompute metrics
or aggregate seeds. A general OSR summary may contain multiple method rows.
Malformed files become error rows; empty searches can still write an empty CSV.
Neither successful exit nor row count alone establishes campaign completeness.
Existing output files are overwritten.

Training rows add `summary_path` and `run_dir`; evaluation rows add
`osr_summary_path` and `osr_run_dir`. Keep these provenance columns. Compare rows
to the reviewed manifest and saved configs, reject errors and duplicates, and
retain checkpoint, backbone, target, surrogate/calibration, budget, seed and
cache identity before combining results. Different methods expose different
target columns; do not silently infer missing identities solely from filenames.

For a DQNGuard matrix, scope the input root to a single reviewed regime/seed.
The expected set is all 20 ordered pairs of distinct PA1/PA2/PA3/PA4/PA8 classes,
with three known classes per trained cell. See DQNGuard for executing cells.
For multiple seeds, validate the 20 pairs within each seed before deliberately
aggregating; do not let a plotting routine choose among duplicates.

## Regenerate a validated Target–Surrogate Matrix

The paper generator has no CLI flags. It selects the **first existing** input:

1. `results/target_surrogate_selection/ts_matrix_surrogate_selection_rules_full.csv`
2. `results/target_surrogate_selection/ruleD_confusion_route_alignment_full.csv`
3. `results/l2o_surrogate_selection/l2o_surrogate_selection_diagnostics.csv`

It does not choose the newest or compare their contents. Accepted columns are
`target_name,surrogate_name,unknown_f1` or
`target_unknown_pas,surrogate_open_pa,unknown_f1`. Targets may be list strings.
Names map PA1/2/3/4/8 to Scan/Burst/Sustain/Hop/Replay. Rows are targets, columns
surrogates; the diagonal is masked. The last duplicate pair wins; missing
off-diagonal cells remain blank. The first maximal cell in each row is bold,
so ties do not imply a unique optimum.

Use the following workflow to select the input explicitly, reject incomplete or
duplicated pairs, and write assets in a fresh directory. The input can instead
be a reviewed DQNGuard reducer CSV with the second schema above. A reducer's
`target_unknown,surrogate_open` schema from some local utilities is not accepted
without an explicit column conversion.

```bash
export PA_MATRIX_SOURCE="results/target_surrogate_selection/ts_matrix_surrogate_selection_rules_full.csv"
export PA_MATRIX_STAGE="results/context_matrix01"
python - <<'PY'
import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd

source = Path(os.environ['PA_MATRIX_SOURCE']).resolve()
stage = Path(os.environ['PA_MATRIX_STAGE']).resolve()
script = Path('papers/milcom2026/figures/target_surrogate_matrix/make_target_surrogate_matrix.py')
assert source.is_file(), source
assert not stage.exists(), 'Choose a fresh staging directory.'
dest_script = stage / script
dest_script.parent.mkdir(parents=True)
shutil.copy2(script, dest_script)
module = runpy.run_path(str(dest_script))
raw = pd.read_csv(source)
assert 'error' not in raw or raw['error'].fillna('').eq('').all()
df = module['normalize_columns'](raw)
names = {'Scan', 'Burst', 'Sustain', 'Hop', 'Replay'}
expected = {(t, s) for t in names for s in names if t != s}
pairs = list(zip(df['target'], df['surrogate']))
assert len(pairs) == len(set(pairs)) == 20, 'Duplicate pairs or wrong row count.'
assert set(pairs) == expected, 'Missing/unexpected target-surrogate pair.'
values = pd.to_numeric(df['unknown_f1'], errors='raise').to_numpy()
assert np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all()
# The highest-priority staging filename is an adapter for this generator.
# Copying here does not compute or assert any surrogate-selection-rule diagnostics.
dest_input = stage / 'results/target_surrogate_selection/ts_matrix_surrogate_selection_rules_full.csv'
dest_input.parent.mkdir(parents=True)
shutil.copy2(source, dest_input)
record = {
    'input': str(source), 'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'generator': str(script), 'generator_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
    'pairs': 20,
}
(stage / 'asset_provenance.json').write_text(json.dumps(record, indent=2) + '\n')
subprocess.run([sys.executable, str(dest_script)], check=True,
               env={**os.environ, 'MPLBACKEND': 'Agg'})
out = stage / script.parent
matrix = pd.read_csv(out / 'target_surrogate_unknown_f1_matrix.csv', index_col=0)
assert matrix.shape == (5, 5) and int(matrix.notna().sum().sum()) == 20
for _, row in df.iterrows():
    assert np.isclose(matrix.loc[row['target'], row['surrogate']], row['unknown_f1'])
print('Review matrix PDF, PNG and CSV in:', out)
PY
```

The copied generator derives its root from its own path, so preserving the
`papers/milcom2026/figures/target_surrogate_matrix/` directory nesting is required.
Validation failure may leave a partial stage; inspect it and choose a new name.
Outputs are `target_surrogate_unknown_f1_matrix.pdf`, `.png` and `.csv`.
Inspect labels, orientation, missing cells and values visually before promotion.

After reviewing source provenance and the staged result, running
`MPLBACKEND=Agg python papers/milcom2026/figures/target_surrogate_matrix/make_target_surrogate_matrix.py`
writes those assets into the manuscript tree using its normal input priority.
That command overwrites existing outputs. Do not promote exploratory metrics as
final-paper results merely because the renderer succeeded.

## Regenerate the main comparison table

The tracked generator reads
`results/og_method_comparison/og_dqnguard_vs_varmax_vs_shreyash_full.csv`
and groups by `comparison_method`. It computes unweighted row means and sample
standard deviations (`ddof=1`) for known rejection, unknown F1, OSR macro F1 and
unknown AUROC. The inspected comparison has four target folds per method
(PA2/3/4/8), not four independent seeds. It is not a pooled confusion-matrix
metric or a confidence interval. NaNs are skipped by pandas; reject them first.

| Comparison key | Implemented track |
|---|---|
| `DQNGuard_PA1_surrogate_knownonly_005` | PyTorch backbone + external-PA1 guard with 5% cutoff |
| `ShreyashCNN_DQNGuard_PA1_surrogate_005` | RF-adapted DQN-IDS Keras backbone + guard |
| `VarMax_surrogate_all_smoke` | VarMax with internal known-class pseudo-unknown calibration |

The tracked generator labels the Keras row “Shreyash CNN head”; the recovered
Lambda manuscript source instead uses “DQN-IDS-style head.” Its historical
caption describes the comparison under fixed PA1-surrogate known-budget
calibration, which does not describe the actual VarMax calibration. Preserve
these as presentation/provenance issues; do not infer experimental equivalence
from the caption or silently edit the manuscript during a documentation pass.

Stage and validate the existing four-fold comparison. The recipe also requires
its referenced per-run evaluator summaries: it checks matching metrics and reads
missing target identities from those records. Restore missing summaries from
the prepared environment before proceeding; do not fill targets from filenames:

```bash
export PA_TABLE_SOURCE="results/og_method_comparison/og_dqnguard_vs_varmax_vs_shreyash_full.csv"
export PA_TABLE_STAGE="results/context_table01"
python - <<'PY'
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np
import pandas as pd

source = Path(os.environ['PA_TABLE_SOURCE']).resolve()
stage = Path(os.environ['PA_TABLE_STAGE']).resolve()
script = Path('papers/milcom2026/tables/main_results/make_main_results_table.py')
df = pd.read_csv(source)
methods = {
    'DQNGuard_PA1_surrogate_knownonly_005',
    'ShreyashCNN_DQNGuard_PA1_surrogate_005',
    'VarMax_surrogate_all_smoke',
}
assert set(df['comparison_method']) == methods and len(df) == 12
assert 'error' not in df or df['error'].fillna('').eq('').all()
metrics = ['known_reject_rate', 'unknown_f1', 'osr_macro_f1', 'unknown_auroc']
source_hashes = {}
def target(row):
    path = Path(row['source_file'])
    assert path.is_file(), f'Restore referenced evaluator summary: {path}'
    original = pd.read_csv(path)
    matched = original[(original['run_name'] == row['run_name']) &
                       (original['method'] == row['method'])]
    assert len(matched) == 1, f'Ambiguous source row: {path}'
    evidence = matched.iloc[0]
    assert np.allclose(evidence[metrics].astype(float), row[metrics].astype(float))
    value = evidence.get('target_unknown_pas')
    if pd.isna(value):
        value = evidence.get('unknown_pas')
    parsed = ast.literal_eval(str(value))
    assert isinstance(parsed, list) and len(parsed) == 1
    supplied = row.get('target_unknown_pas')
    if pd.notna(supplied):
        assert ast.literal_eval(str(supplied)) == parsed
    source_hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return parsed[0]
df['_target'] = df.apply(target, axis=1)
for _, sub in df.groupby('comparison_method'):
    assert len(sub) == 4 and set(sub['_target']) == {'PA2', 'PA3', 'PA4', 'PA8'}
metrics = ['known_reject_rate', 'unknown_f1', 'osr_macro_f1', 'unknown_auroc']
values = df[metrics].apply(pd.to_numeric, errors='raise').to_numpy()
assert np.isfinite(values).all() and ((values >= 0) & (values <= 1)).all()
assert not stage.exists(), 'Choose a fresh staging directory.'
dest_script = stage / script
dest_script.parent.mkdir(parents=True)
shutil.copy2(script, dest_script)
dest_input = stage / 'results/og_method_comparison/og_dqnguard_vs_varmax_vs_shreyash_full.csv'
dest_input.parent.mkdir(parents=True)
shutil.copy2(source, dest_input)
(stage / 'asset_provenance.json').write_text(json.dumps({
    'input': str(source), 'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'generator': str(script), 'generator_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
    'methods': 3, 'folds_per_method': 4, 'evaluator_summary_sha256': source_hashes,
}, indent=2) + '\n')
subprocess.run([sys.executable, str(dest_script)], check=True)
out = stage / script.parent
summary = pd.read_csv(out / 'main_osr_results_table_summary.csv').set_index('comparison_method')
assert len(summary) == 3 and summary['folds'].eq(4).all()
for key, sub in df.groupby('comparison_method'):
    for metric in metrics:
        assert np.isclose(summary.loc[key, metric + '_mean'], sub[metric].mean())
        assert np.isclose(summary.loc[key, metric + '_std'], sub[metric].std(ddof=1))
print('Review main_osr_results_table.tex and summary CSV in:', out)
PY
```

Preserve the original source rows and their `source_file` paths. Building a new
comparison CSV requires an explicit selection of one reviewed evaluator row per
method/target, with the keys above; generic reducers do not create this comparison
schema or select scientifically equivalent settings for you. For multiple seeds,
design that aggregation separately instead of passing additional rows to this
four-fold recipe.

Direct `python papers/milcom2026/tables/main_results/make_main_results_table.py`
overwrites `main_osr_results_table.tex` and `main_osr_results_table_summary.csv`
in the paper tree. The staged LaTeX is a fragment requiring the paper's LaTeX
context, not a standalone document. Table regeneration does not compile the paper.

## Use recovered Lambda analysis tools deliberately

The following source was recovered from Lambda but is not tracked at the source
revision below. These filenames are local entry points, not promised fresh-clone
capabilities. Preserve and inspect the matching source before use; do not invent
a catalog command or silently substitute another script. They run from the
repository root with `python experiments/NAME.py` and hardcode their paths.

| Local script | Inputs and behavior |
|---|---|
| `summarize_l2o_dqnguard.py` | Globs named 5%-budget L2O summaries under `results_pa_osr_eval`; writes full rows, per-metric pivots and target/surrogate summaries under `results/l2o_dqnguard` |
| `plot_l2o_heatmaps.py` | Reads those pivots; writes four PNG heatmaps under `results/figures/l2o_dqnguard`; skips missing metric files |
| `analyze_ts_matrix_surrogate_rules.py` | Reads selection diagnostics (or Rule A input fallback); reloads backbones/caches on CUDA to compute geometry; writes rule diagnostics under `results/target_surrogate_selection` |
| `analyze_ts_matrix_ruleD_route_alignment.py` | Reloads models and compares target-test routing with surrogate-validation routing; writes route-alignment diagnostics |
| `analyze_ts_matrix_ruleE_pseudotarget.py` | Reloads models and evaluates pseudo-target selection diagnostics; requires its reviewed cell/run inputs |
| `plot_l2o_oracle_delta_heatmaps.py` | Requires the existing oracle-comparison delta CSV; plots deltas, does not compute or validate their provenance |
| `make_paper_facing_tables.py` | Formats existing comparison/summary/best-worst CSVs into named CSV/Markdown under `results/paper_tables`; silently skips missing input tables |

The L2O summarizer and oracle-delta plotter use `pivot_table(..., aggfunc="max")`.
Repeated cells select the best value rather than average seeds; validate
duplicates before interpreting their images. The summarizer's compact output
also omits some calibration settings: retain original summaries.

Rules and route diagnostics are not required to redraw an existing matrix.
They can perform substantial inference and guard fitting, and their run-name
fallbacks include historical 16384 conventions. Rule D explicitly observes
target-test behavior; selecting a surrogate with that evidence is retrospective,
not a validated target-blind selection procedure. Best/worst cells based on test
F1 are descriptive oracle comparisons unless a separate selection protocol was
established. Historical `oracle_trueopen` filenames also need the zero-cap
limitation in DQNGuard checked before interpreting the claimed calibration.

## Resolve conflicting artifacts and verify success

Use current source to establish executable mechanics, author-confirmed intended
settings to establish scientific intent, and saved config/cache/checkpoint and
commands to establish what a particular run actually did. Keep disagreement
visible until the correct evidence chain is recovered.

Examples: an old high-priority matrix CSV can shadow a newer CSV; a Keras method
string can contain PA1 even when its explicit surrogate field differs; a VarMax
CSV candidate count can count only retained candidates while progress counts
the full search. Consult the owning code/context, identify the run and fields,
and regenerate the affected derived artifact from reviewed inputs. Do not edit
raw metrics, rename exploratory runs as final runs, or let a generated index
override normative documentation.

Success requires correct input identities and coverage, matching numerical
outputs, reviewed presentation labels, and preserved provenance. A command
exit, file existence, attractive heatmap or successful LaTeX fragment generation
alone is insufficient.

Interfaces checked against source at
`a12ad5851b90b37b9f8868e940af16b8a379748b`. Staging examples were exercised with
the supplied historical CSVs in an isolated copy; no models or experiments were
run, and no final-paper reproduction claim follows from those renderer checks.
