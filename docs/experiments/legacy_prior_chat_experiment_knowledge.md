# Legacy prior-chat experiment knowledge

This document is a compact knowledge export of the old PA CNN/OSR experiment program, combining:

- committed reconstruction artifacts already on this branch,
- the new final manifest/training system definitions,
- and prior-chat context that captured intent, naming, conclusions, and abandoned directions.

It is intended to preserve *scientific and configuration knowledge* even when raw checkpoints, caches, MAT files, or long local logs are not immediately available.

## Sources used for this writeup

Primary committed branch sources:

- `docs/experiments/legacy_digital_reconstruction.md`
- `docs/experiments/legacy_run_inventory.csv`
- `docs/experiments/legacy_checkpoint_inventory.csv`
- `docs/experiments/legacy_generated_table_inventory.csv`
- `experiments/pa_make_train_manifest.py`
- `experiments/pa_train_one.py`
- `experiments/pa_constants.py`

## Confidence labels used below

- **Committed**: directly supported by files on branch.
- **Reconstructed**: strongly inferred from committed inventory, run names, or branch constants.
- **Prior-chat memory**: preserved from earlier experiment planning and result interpretation; useful, but should be treated as memory-backed rather than file-backed.

---

## 1. Original scientific goal of the digital-noisy experiments

The original digital-noisy PA experiments were not meant to be the final deployment system. They were a controlled research program to answer four questions:

1. **Can a compact CNN backbone cleanly separate the PA classes under synthetic noisy-digital conditions?**
2. **Which training recipe produces the best feature geometry for later open-set rejection?**
3. **Which OSR metrics are actually useful and deployable, versus merely diagnostic?**
4. **Which unknown PA folds are intrinsically easy or hard, especially when the classifier is calibrated on known classes only?**

The high-level workflow was:

- train a closed-set CNN on known PA classes,
- withhold one PA as the unknown fold,
- evaluate open-set behavior using confidence-manifold / proxy metrics and later VarMax-style logic,
- identify backbones whose known-class representations transfer well to OSR.

The old digital-noisy experiments were therefore a **representation-learning and OSR-calibration program**, not merely a closed-set accuracy exercise.

---

## 2. Dataset / source assumptions used in the old digital-noisy program

### 2.1 Old source assumptions

**Committed / reconstructed:** the legacy reconstruction explicitly identifies a **digital `pilot_noisy_torch`** result subset inside the larger legacy inventory and reports 113 complete digital-noisy summaries. The observed unknown folds in those digital-noisy runs were `PA2`, `PA3`, `PA4`, and `PA8`. The dominant cache length was `16384`, batch size `16`, and epochs `200`. The strongest historical digital-noisy result roots were `results_pa_confmanifold_refined` and `results_pa_confmanifold_coarse`, with additional support from `results_pa_osr_bank`, `results_pa_baseline`, `results_pa_followup`, and `results_pa_finalist`.

### 2.2 Exact old assumptions (best reconstruction)

- **source_type**: `digital` or digital-noisy synthetic source
- **source_name**: effectively `pilot_noisy_torch`
- **PA universe**: historical core PA universe was `PA2, PA3, PA4, PA8`
- **unknown-fold setup**: leave-one-PA-out open-set folds over that 4-PA universe
- **cache length**: `16384`
- **batch size**: `16`
- **epochs**: typically `200`
- **noise condition**: noisy digital, i.e. digitally generated data with injected/noisy conditions, not OTA capture

### 2.3 New system assumptions for reruns

The final manifest-based system does **not** use the legacy digital-noisy defaults as its primary source. The current committed manifest generator builds configs with:

- `source_type = "ota"`
- `source_name = "ota_core_high_run01"`
- `dataset_tag = "ota_core_high_run01"`
- `noise_tag = "high_run01"`
- `cache_len = 16384`
- `cache_root = _feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01`

and supports paper-set PA universes:

- `OG = [PA2, PA3, PA4, PA8]`
- `DISTINCT = [PA1, PA3, PA4, PA8]`
- `MASTER = [PA1, PA2, PA3, PA4, PA8]`

So the old digital-noisy program should be treated as the *historical search phase*, while the new runner is the *modern rerun / OTA-first phase*.

---

## 3. Historical experiment phases, in order

This ordering is the best reconstruction of how the old experiment program evolved.

### Phase 1 — baseline / cache sweep

Purpose:

- validate the basic CNN training loop,
- settle cache length and training stability,
- confirm the problem was easy in closed-set mode,
- establish a reference backbone for later OSR work.

Typical result roots:

- `results_pa_baseline`
- `results_pa_cache_sweep`

Main outputs:

- cache length comparisons,
- closed-set sanity checks,
- initial timestamped run dirs with `summary.json`, `history.json`, checkpoints.

### Phase 2 — confidence manifold coarse sweep

Purpose:

- perform a broad first-pass search over families that might improve open-set separation,
- tune confidence-manifold style selections and proxy metrics,
- explore paper-inspired variants before narrowing.

Typical result root:

- `results_pa_confmanifold_coarse`

Main families introduced here:

- `confman_baseline_knownonly`
- `confman_baseline_openconf`
- `confman_paperish_mild`
- `confman_paperish_mid`
- `confman_paperish_mid_smooth`
- `confman_paperish_strong`

### Phase 3 — confidence manifold refined sweep

Purpose:

- narrow the search onto reference backbones and targeted variants,
- compare entropy regularization, dropout, label smoothing, and center-loss choices,
- identify deployable backbones for later OSR evaluation.

Typical result root:

- `results_pa_confmanifold_refined`

Key families / variants from this stage:

- `ref_base_ent005`
- `ref_base_lr2e4`
- `ref_base_nocenter`
- `ref_base_drop040`
- `ref_base_drop050`
- `ref_base_ls002`
- `ref_base_ls005`
- `ref_base_ctrl`
- `ref_base_ent002`
- `ref_pms_lr2e4`

### Phase 4 — OSR backbone bank

Purpose:

- collect trained backbones judged worth evaluating under stronger OSR logic,
- separate backbone search from later calibration/evaluation search,
- build a bank of candidates for surrogate/oracle style evaluation.

Typical result root:

- `results_pa_osr_bank`

This phase was the bridge between raw training sweeps and more explicit open-set evaluation.

### Phase 5 — finalist / followup runs

Purpose:

- compare a small set of best candidates directly,
- run targeted confirmation experiments,
- investigate thresholding/calibration behavior rather than broad backbone search.

Typical result roots:

- `results_pa_followup`
- `results_pa_finalist`

This was where earlier broad sweep conclusions were condensed into a short list of "serious" backbones.

### Phase 6 — early OTA BT/ZB attempts

Purpose:

- test whether the digital conclusions transferred to limited OTA data,
- especially for Bluetooth and Zigbee.

Typical result root:

- `results_pa_ota_btzb`

Why it was limited / abandoned as the final answer:

- the OTA BT/ZB attempt was small and not the final source definition,
- the old OTA attempt did not represent the unified OTA core dataset later developed,
- it was useful as a stress test but not trustworthy enough to replace the digital-noisy conclusions,
- later work showed that OTA preprocessing, splicing, validation, and cache construction all had to be rebuilt much more carefully.

Bottom line: the old BT/ZB OTA attempt was an exploratory transfer check, not the final experimental basis for the paper or the new final runner.

---

## 4. Important model / backbone families and what each meant

### `ref_base_ent005`

Reference baseline with entropy regularization. This became the most important family because it repeatedly looked strong under realistic OSR conditions and not just diagnostic proxy metrics.

### `ref_base_lr2e4`

Lower-learning-rate reference baseline. Important because it offered a cleaner stability comparison against the entropy-regularized reference.

### `ref_pms_drop040`

Paper-motivated or paperish-style stronger-regularization family with nonzero center loss and heavier dropout. Useful as a more structured comparison point, but not always the best deployable choice.

### `ref_base_nocenter`

Reference baseline without center loss. Useful for testing whether center-style attraction helped or hurt downstream OSR feature geometry.

### `confman_baseline_knownonly`

Confidence-manifold baseline selected in a known-only stopping mode. Important as a diagnostic comparator showing what happens when model selection is not explicitly OSR-aware.

### `confman_baseline_openconf`

Confidence-manifold baseline using open-confidence selection rather than known-only stopping.

### `confman_paperish_*`

A family of coarse-sweep variants inspired by more aggressive confidence-manifold or paper-style regularization choices. The suffixes roughly meant:

- `mild`: weaker regularization / weaker open-set shaping
- `mid`: moderate setting
- `mid_smooth`: moderate setting with extra smoothing
- `strong`: stronger confidence-manifold shaping

These were valuable in the coarse search but generally not the final deployable backbone choice.

---

## 5. Hyperparameters by family (best reconstruction)

The table below combines committed branch constants with prior-chat reconstruction. Values are grouped by confidence.

| family | lr | label smoothing | entropy loss weight | center loss / lambda_center | dropout | weight decay | grad clip | scheduler | early stopping mode | selection metric | batch size | epochs | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ref_base_ent005` | `5e-4` | `0.10` | `0.05` | likely none or baseline default only | `0.30` | baseline / small | none | cosine in final system; legacy varied | `open_conf` | `dqn_proxy_softmax3` in legacy; later broader OSR metrics | `16` | `200` old, `60` in new runner | prior-chat memory + run-name reconstruction |
| `ref_base_lr2e4` | `2e-4` | `0.10` | `0.00` | likely none or baseline default only | `0.30` | baseline / small | none | cosine in final system; legacy varied | `open_conf` | `dqn_proxy_softmax3` legacy | `16` | `200` old | prior-chat memory |
| `ref_pms_drop040` | `1e-4` | `0.05` | `0.05` | `lambda_center = 0.1` | `0.40` | `1e-4` | `1.0` | plateau | `open_conf` | proxy metric / OSR-aware | `16` | `200` old | prior-chat memory |
| `ref_base_nocenter` | `5e-4` | `0.10` | `0.00` | no center loss | `0.30` | baseline / small | none | legacy default | `open_conf` | `dqn_proxy_softmax3` | `16` | `200` | reconstructed from run names and branch doc |
| `confman_baseline_knownonly` | `5e-4` | `0.10` | `0.00` | none | `0.30` | baseline / small | none | legacy default | `known_only` | `dqn_proxy_softmax3` reported in reconstruction tables | `16` | `200` | committed reconstruction |
| `confman_baseline_openconf` | `5e-4` | `0.10` | `0.00` | none | `0.30` | baseline / small | none | legacy default | `open_conf` | `dqn_proxy_softmax3` | `16` | `200` | committed reconstruction |
| `confman_paperish_mild` | `1e-4` | `0.00` | `0.02` | none / unclear | `0.50` | paperish coarse default | none | legacy default | `open_conf` | `dqn_proxy_softmax3` | `16` | `200` | committed reconstruction |
| `confman_paperish_mid` | `1e-4` | `0.00` | `0.05` | none / unclear | `0.50` | paperish coarse default | none | legacy default | `open_conf` | `dqn_proxy_softmax3` | `16` | `200` | committed reconstruction |
| `confman_paperish_mid_smooth` | `1e-4` | `0.05` | `0.05` | none / unclear | `0.50` | paperish coarse default | none | legacy default | `open_conf` | `dqn_proxy_softmax3` | `16` | `200` | committed reconstruction |
| `confman_paperish_strong` | `1e-4` | `0.00` | `0.10` | none / unclear | `0.50` | paperish coarse default | none | legacy default | `open_conf` | `dqn_proxy_softmax3` | `16` | `200` | committed reconstruction |

### Important note on new runner defaults

The *new* final manifest system does **not** preserve all legacy families directly. The committed final branch currently exposes these family grids:

- `smoke_ent005_lr2e4`: `lr=2e-4`, `label_smoothing=0.10`, `entropy_loss_weight=0.05`, `mlp_dropout=0.30`, `epochs=3`
- `ref_ent005_lr2e4`: `lr=2e-4`, `label_smoothing=0.10`, `entropy_loss_weight=0.05`, `mlp_dropout=0.30`, `epochs=60`, `patience=10`
- `ref_ent005_lr5e4`: `lr=5e-4`, `label_smoothing=0.10`, `entropy_loss_weight=0.05`, `mlp_dropout=0.30`, `epochs=60`, `patience=10`
- `ref_noent_lr5e4`: `lr=5e-4`, `label_smoothing=0.10`, `entropy_loss_weight=0.00`, `mlp_dropout=0.30`, `epochs=60`, `patience=10`
- `ref_ls000_noent_lr5e4`: `lr=5e-4`, `label_smoothing=0.00`, `entropy_loss_weight=0.00`, `mlp_dropout=0.30`, `epochs=60`, `patience=10`

The final system also hardcodes:

- `source_type = ota`
- `split_mode = open_pa`
- `cache_len = 16384`
- `open_val_frac = 0.15`
- `build_balanced_val_open = True`
- `require_true_val_open = True`
- `early_stopping_mode = open_conf`
- `model_selection_metric = val_macro_f1`
- `open_conf_selection_metric = dqn_proxy_expanded5`
- `scheduler_name = cosine`
- `lambda_center = 0.1`
- `weight_decay = 0.0`

This means the new runner is already incorporating lessons from the old OSR program rather than literally reusing every old training knob.

---

## 6. Old OSR / evaluation methods

### 6.1 VarMax settings and role

**Prior-chat memory:** the long-term direction became a VarMax-based OSR layer using class-specific thresholding on representation-derived scores, eventually combined with energy-based confidence. The critical lesson was that backbone quality mattered first, and calibration strategy mattered second.

The old evaluation program considered metrics drawn from:

- logit variance,
- energy,
- entropy,
- max softmax probability (`pmax`),
- margin / `p1 - p2`,
- expanded proxy families used for DQN-style selection.

### 6.2 Surrogate-all vs oracle-balanced

**Prior-chat memory:** one major theme was distinguishing *deployable* thresholding from *diagnostic upper-bound* thresholding.

- **oracle-balanced / oracle**: threshold chosen with unrealistically privileged access or sweep knowledge; useful as an upper bound.
- **surrogate-all**: practical thresholding using surrogate unknowns from the available known-class setting.
- other variants discussed later included aligned vs mismatched surrogate choices.

The key historical lesson was: many backbones can look good under oracle thresholding, but fewer remain good under surrogate-based deployable calibration.

### 6.3 DQN proxy metrics

The legacy reconstruction tables explicitly report `best_val_dqn_proxy_expanded5`, `test_dqn_proxy_expanded5`, and legacy `open_conf_selection_metric = dqn_proxy_softmax3` in many rows. That indicates the old system used DQN-style proxy aggregates as selection metrics even before the final VarMax framing was stabilized.

### 6.4 Deployable vs diagnostic metrics

**Prior-chat memory:** the metric hierarchy was roughly:

Deployable / decision-facing:

- VarMax score with calibrated thresholds
- energy score
- `pmax`
- `p1 - p2`

Mostly diagnostic / exploratory:

- raw entropy
n- raw logit variance without calibrated decision policy
- oracle threshold sweeps
- some DQN proxy aggregates used for model selection but not intended as final deployment logic

Main lesson: a metric could be useful for ranking or model selection without being the final deployed accept/reject statistic.

---

## 7. Main historical conclusions

### 7.1 Which backbone/config was best?

**Prior-chat memory, supported by the branch reconstruction narrative:** `ref_base_ent005` emerged as the most important historical backbone family because it balanced strong learned representations with comparatively good performance under more realistic OSR evaluation, not just oracle-style sweeps.

`ref_base_lr2e4` was the key control / backup comparison. `ref_pms_drop040` had some promise, especially in upper-bound style evaluations, but was less clearly the deployable winner.

### 7.2 Which unknown folds were easy / hard?

**Committed reconstruction:** digital-noisy folds over `PA2`, `PA3`, `PA4`, `PA8` were all present, and many top rows by proxy metric came from `PA8`, `PA3`, or `PA4`. PA2 repeatedly appeared as a harder fold in prior-chat interpretation.

**Prior-chat memory:**

- `PA8` often looked comparatively easier.
- `PA3` and `PA4` were generally manageable depending on family.
- `PA2` was the recurring hard case.

### 7.3 What happened with PA2?

PA2 was historically important because it exposed the limits of naive confidence-based OSR.

**Prior-chat memory:** PA2-open runs were consistently more fragile, suggesting that the withheld PA2 distribution was not cleanly separated by the feature geometry learned by weaker backbones. This is one reason the search shifted toward backbone families with better open-set shaping and entropy regularization.

### 7.4 Why did `ref_base_ent005` matter?

Because it was the most compelling evidence that a *simple* reference backbone with moderate entropy regularization could outperform fancier or more paperish families when judged by realistic OSR behavior, not just closed-set known accuracy.

It became the backbone family to beat.

### 7.5 Why was the old BT/ZB OTA attempt not the final answer?

Because it was exploratory and incomplete:

- limited OTA scope,
- not built on the later unified OTA core dataset,
- not supported by the later splicing/validation rigor,
- and therefore not a trustworthy replacement for the digital-noisy search program.

The correct interpretation of old BT/ZB OTA results is: **interesting transfer check, not final evidence**.

---

## 8. What should be rerun now under the new manifest-based system

### 8.1 Rerun goals

The new runner should *not* blindly repeat the entire legacy program. It should perform a **disciplined rerun** using the knowledge already gained.

### 8.2 Minimal recommended rerun set

#### Backbone families to rerun first

Use the new manifest system to rerun only the compact modern equivalents of the historical finalists:

- `ref_ent005_lr2e4`
- `ref_ent005_lr5e4`
- `ref_noent_lr5e4`
- `ref_ls000_noent_lr5e4`

These map directly onto the historical lessons:

- entropy vs no-entropy,
- `5e-4` vs `2e-4`,
- label smoothing on vs off,
- stable reference dropout of `0.30`.

#### Paper-set sweep

Run all three committed paper sets:

- `OG`
- `DISTINCT`
- `MASTER`

#### Unknown-fold sweep

Within each paper set, sweep every PA that exists in that set as the unknown fold.

#### Source sweep

Use the committed OTA source and cache settings from the final runner first:

- `source_type = ota`
- `source_name = ota_core_high_run01`
- `dataset_tag = ota_core_high_run01`
- `noise_tag = high_run01`
- `cache_root = _feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01`

#### Protocol ablations

After all-protocol OTA runs, repeat top families for:

- wifi-only
- bluetooth-only
- zigbee-only

### 8.3 OSR rerun recommendation

Rerun OSR evaluation for:

- practical surrogate-style calibration,
- oracle-only as an upper bound,
- and explicit foldwise reporting on which unknown PAs remain difficult.

---

## 9. What should *not* be rerun

These do **not** need a full rerun simply to recover knowledge:

1. The broad coarse confidence-manifold search over many `confman_paperish_*` variants.
   - Existing metadata and reconstruction already preserve what these families were for.
2. The old cache-length sweeps whose only purpose was to settle on `16384`.
   - The new runner already assumes `cache_len = 16384`.
3. The old notebook UI workflow itself.
   - The final system replaces it with manifests and worker processes.
4. The early BT/ZB OTA attempt as a stand-alone scientific phase.
   - It should be superseded by new unified OTA reruns.
5. Redundant known-only baselines beyond one or two anchor comparisons.
   - They are useful as references but do not need a large rerun budget.

---

## 10. Caveats, mistakes, abandoned hypotheses, and naming confusion

### 10.1 Closed-set accuracy was not the main bottleneck

A recurring mistake would be to over-focus on known-class macro-F1. The old experiments already showed that strong closed-set accuracy could coexist with weak deployable OSR.

### 10.2 Oracle metrics were useful but dangerous

Oracle-balanced or oracle-style thresholds were valuable as upper bounds, but they could make weaker backbones look better than they really were in deployable settings.

### 10.3 OTA BT/ZB transfer was over-interpretable

The old BT/ZB OTA attempt was easy to over-read. It should be treated as exploratory, not final.

### 10.4 Naming drift

Legacy names mixed several concepts:

- backbone family,
- source condition,
- unknown fold,
- cache length,
- timestamped run dir,
- and sometimes selection mode.

Examples include:

- `ref_base_ent005_unkPA8_c16384_seed0`
- `confman_paperish_mid_smooth_unkPA8_c16384_seed0`
- `confman_baseline_knownonly_unkPA4_c16384_seed0`

The final manifest system improves this by separating:

- `paper_set`
- `family_tag`
- `unknown_pa`
- `seed`
- `protocol_tag`
- config JSON path

### 10.5 PA universe confusion across eras

The old digital-noisy work mostly used the 4-PA universe `PA2, PA3, PA4, PA8`.

Later work introduced:

- `DISTINCT = [PA1, PA3, PA4, PA8]`
- `MASTER = [PA1, PA2, PA3, PA4, PA8]`

This means comparisons between old and new runs must always note which paper set was used.

### 10.6 Center-loss confusion

Some historical family names implied center-loss ablations (`nocenter`, paperish / PMS variants), but the exact center-loss usage was not preserved uniformly in committed artifacts. Where exact values are not directly committed, this document labels them as reconstructed or prior-chat memory rather than pretending they are exact.

### 10.7 Final runner is opinionated by design

The new final manifest system already bakes in several historical lessons:

- OTA-first source assumptions,
- `cache_len = 16384`,
- `split_mode = open_pa`,
- open validation construction,
- `early_stopping_mode = open_conf`,
- and a compact family grid rather than a huge legacy sweep.

That is a feature, not a bug.

---

## 11. Recommended practical rerun plan

### Tier 1 — mandatory

- run `baseline` and `search` grids from the final manifest system,
- on `OG`, `DISTINCT`, and `MASTER`,
- for all unknown folds in each paper set,
- all-protocol OTA first,
- then per-protocol ablations for top families.

### Tier 2 — targeted legacy comparison only if needed

Only if the new results are ambiguous, add one small legacy-style comparison layer:

- mimic `ref_base_ent005`
- mimic `ref_base_lr2e4`
- optionally mimic `ref_pms_drop040`

This is enough to tie the new system back to the old scientific story without rebuilding the entire legacy tree.

---

## 12. Final one-paragraph summary

The legacy digital-noisy experiment program established that the important problem was not merely closed-set PA classification, but learning a backbone whose feature geometry supports deployable open-set rejection. The broad baseline/cache and coarse confidence-manifold sweeps narrowed into refined reference families, with `ref_base_ent005` emerging as the historically most important backbone and `PA2` remaining the most informative hard unknown fold. Early BT/ZB OTA transfer experiments were useful but not final. The new final manifest-based experiment system should therefore rerun only the compact modern equivalent of those lessons—using the committed OTA core source, the `OG` / `DISTINCT` / `MASTER` paper sets, and a narrow set of reference families—rather than repeating the full historical search.
