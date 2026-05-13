# Final rerun plan

This document is an **actionable experiment specification** for the final manifest-based PA CNN/OSR rerun program. It is written so that a follow-on implementation pass can directly convert it into:

- `experiments/pa_experiment_catalog.py`
- updated manifest generation logic
- final train/eval sweep commands

It is intentionally more operational than `legacy_prior_chat_experiment_knowledge.md`.

---

## 1. Executive decision

### Final decision

We will **not** rerun the entire legacy digital-noisy search tree. We will:

1. **Reuse legacy evidence** from the reconstructed digital-noisy experiment program.
2. **Rerun a compact OTA-first matrix** using the new final manifest-based system.
3. **Evaluate OSR from saved checkpoints/artifacts** using a standardized post-training evaluation matrix.
4. **Use limited bridge reruns only if needed** to verify that the new runner can reproduce the key legacy conclusions.

### What we are rerunning

Mandatory:

- `ota_primary_matrix`
- `ota_master_context`
- `osr_eval_matrix`

After the primary matrix:

- `ota_protocol_ablation`

Optional / only if needed:

- `legacy_digital_bridge_rerun`

### What we are not rerunning

We are **not** rerunning:

- the broad legacy `confman_paperish_*` coarse sweep
- the old cache-length sweep
- the old notebook UI workflow
- the early BT/ZB OTA attempt as standalone evidence
- redundant known-only baseline grids beyond minimal anchors

### What legacy evidence is being reused

We are reusing:

- the reconstructed digital-noisy family inventory
- the legacy run inventory and checkpoint inventory
- the legacy generated tables
- the branch-level prior-chat knowledge export
- the final-branch manifest and family definitions

### Why this is enough for the paper/project

This is enough because the scientific question is no longer “what does the entire old search tree look like?” It is now:

- can the final runner reproduce the historically important backbone comparisons,
- can it do so on the final OTA source definition,
- and can it produce standardized OSR evaluation artifacts for the final paper/project.

The existing legacy metadata already preserves the old broad-search conclusions sufficiently well. The remaining missing evidence is **final OTA rerun evidence under the new system**, not another huge rediscovery sweep.

---

## 2. Evidence basis

This plan is grounded against the following branch files:

- `docs/experiments/legacy_prior_chat_experiment_knowledge.md`
- `docs/experiments/legacy_digital_reconstruction.md`
- `docs/experiments/legacy_run_inventory.csv`
- `docs/experiments/legacy_checkpoint_inventory.csv`
- `docs/experiments/legacy_generated_table_inventory.csv`
- `experiments/pa_make_train_manifest.py`
- `experiments/pa_train_one.py`
- `experiments/pa_constants.py`

### Evidence labels used in this document

- **Committed evidence**: directly supported by committed branch files.
- **Reconstructed**: strongly inferred from inventories, run names, or current branch constants.
- **Prior-chat memory**: preserved from earlier chats and planning; useful but not treated as file-exact unless cross-supported.
- **Recommendation**: decision made for the final rerun program.

### Evidence-basis claims

1. **Committed evidence**: the final branch already defines an OTA-first manifest/training system with `source_type="ota"`, `source_name="ota_core_high_run01"`, `dataset_tag="ota_core_high_run01"`, `noise_tag="high_run01"`, `cache_len=16384`, `cache_root=_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01`, `split_mode="open_pa"`, `early_stopping_mode="open_conf"`, and `open_conf_selection_metric="dqn_proxy_expanded5"`.
2. **Committed evidence**: the final branch defines paper sets `OG`, `DISTINCT`, and `MASTER` and exposes compact family grids rather than the full legacy family universe.
3. **Committed evidence**: the legacy digital reconstruction already identifies the old result roots, observed unknown folds, major family labels, and many key hyperparameters from inventories.
4. **Prior-chat memory + reconstructed**: `ref_base_ent005` was historically the most important deployable backbone family; `ref_base_lr2e4` was the main control; `ref_pms_drop040` was useful but not the default final winner.
5. **Prior-chat memory + recommendation**: the final project should focus rerun budget on OTA evidence and OSR evaluation rather than repeating the broad digital-noisy family search.

---

## 3. Legacy-to-new mapping table

| old family name | old source/root | old purpose | old key hyperparameters | new family name | new hyperparameters | exact / approximate / superseded | rerun? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ref_base_ent005` | `results_pa_confmanifold_refined` | reference deployable backbone with entropy regularization | lr `5e-4`, ls `0.10`, entropy `0.05`, dropout `0.30`, batch `16`, epochs `200`, `open_conf`, `dqn_proxy_softmax3` | `ref_ent005_lr5e4` | lr `5e-4`, ls `0.10`, entropy `0.05`, dropout `0.30`, epochs `60`, patience `10`, OTA-first defaults | **approximate modernized equivalent** | yes |
| `ref_base_lr2e4` | `results_pa_confmanifold_refined` / followup context | lower-lr reference control backbone | lr `2e-4`, ls `0.10`, entropy `0.00`, dropout `0.30`, batch `16`, epochs `200`, `open_conf` | `ref_noent_lr5e4` and partially `ref_ent005_lr2e4` | not exact; new family split separates lr and entropy axis | **superseded / split across new families** | yes, via modern equivalents |
| `ref_pms_drop040` | refined / finalist-followup family | stronger regularized comparison, paperish / PMS style | lr `1e-4`, wd `1e-4`, lambda_center `0.1`, ls `0.05`, entropy `0.05`, dropout `0.40`, grad clip `1.0`, plateau scheduler | none exact in final branch | would require explicit legacy bridge config if rerun | **superseded** | optional bridge only |
| `ref_base_nocenter` | `results_pa_confmanifold_refined` | test no-center-loss representation | lr `5e-4`, ls `0.10`, entropy `0.00`, dropout `0.30` | none exact | final branch currently keeps `lambda_center=0.1` globally | **superseded** | no by default |
| `confman_baseline_knownonly` | `results_pa_confmanifold_coarse` | known-only stopping baseline | lr `5e-4`, ls `0.10`, entropy `0.00`, dropout `0.30`, `known_only` stop mode | none exact | final system standardized on `open_conf` | **superseded** | no |
| `confman_baseline_openconf` | `results_pa_confmanifold_coarse` | baseline open-confidence stopping reference | lr `5e-4`, ls `0.10`, entropy `0.00`, dropout `0.30`, `open_conf` | `ref_noent_lr5e4` | close modern equivalent with updated OTA defaults | **approximate** | maybe as anchor only |
| `confman_paperish_mild` | `results_pa_confmanifold_coarse` | coarse broad-search mild regularization variant | lr `1e-4`, ls `0.00`, entropy `0.02`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** | no |
| `confman_paperish_mid` | `results_pa_confmanifold_coarse` | coarse broad-search mid regularization variant | lr `1e-4`, ls `0.00`, entropy `0.05`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** | no |
| `confman_paperish_mid_smooth` | `results_pa_confmanifold_coarse` | coarse broad-search mid + smoothing | lr `1e-4`, ls `0.05`, entropy `0.05`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** | no |
| `confman_paperish_strong` | `results_pa_confmanifold_coarse` | coarse broad-search stronger regularization variant | lr `1e-4`, ls `0.00`, entropy `0.10`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** | no |

### Naming mismatch resolution

The old refined-family names bundled multiple axes into a single historical label. The new final-branch families separate the retained axes more cleanly:

- old `ref_base_ent005` maps most directly to **`ref_ent005_lr5e4`**
- old `ref_base_lr2e4` is **not one exact family** in the final branch; its legacy role is now represented by comparing:
  - `ref_ent005_lr2e4`
  - `ref_noent_lr5e4`
- old no-label-smoothing / no-entropy ablations map to **`ref_ls000_noent_lr5e4`**
- old center-loss ablations and paperish coarse families are treated as **superseded**, not as mandatory exact reruns

---

## 4. Source profiles

```yaml
source_profiles:
  digital_noisy_legacy:
    source_type: digital
    source_name: pilot_noisy_torch
    purpose: legacy reconstruction / optional bridge rerun
    cache_len: 16384
    notes:
      - historical source profile used in old digital-noisy search
      - not the default final source

  ota_core_high_run01:
    source_type: ota
    source_name: ota_core_high_run01
    dataset_tag: ota_core_high_run01
    noise_tag: high_run01
    cache_len: 16384
    cache_root: _feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01
    purpose: final OTA experiments
    notes:
      - primary final source profile
      - all mandatory reruns should target this source first
```

### Source-profile notes

- `digital_noisy_legacy` exists for documentation and optional bridge verification only.
- `ota_core_high_run01` is the primary final source profile for all mandatory reruns.

---

## 5. Paper sets

```yaml
paper_sets:
  OG:
    pas: [PA2, PA3, PA4, PA8]
    purpose: legacy-compatible original PA universe

  DISTINCT:
    pas: [PA1, PA3, PA4, PA8]
    purpose: PA1 replacement / distinct behavior comparison

  MASTER:
    pas: [PA1, PA2, PA3, PA4, PA8]
    purpose: final full context
```

### Paper-set notes

- `OG` is needed for direct continuity with the legacy four-PA search universe.
- `DISTINCT` is needed because PA1 became a new behavioral axis and a replacement comparison universe.
- `MASTER` is needed because the final project context is no longer strictly the original four-PA world.

---

## 6. Final run groups

```yaml
run_groups:
  smoke_functional:
    source_profile: ota_core_high_run01
    paper_sets: [OG]
    families: [smoke_ent005_lr2e4]
    unknown_folds: all_in_set
    seeds: [0]
    epochs: 3
    priority: mandatory-first
    purpose: test runner/dashboard only
    expected_output_root: results_pa_final_smoke
    status: mandatory

  legacy_digital_recovered:
    source_profile: digital_noisy_legacy
    paper_sets: [OG]
    families: [legacy_metadata_only]
    unknown_folds: [PA2, PA3, PA4, PA8]
    seeds: legacy_observed
    epochs: legacy_observed
    priority: mandatory-reference
    purpose: document old digital-noisy results, no rerun unless needed
    expected_output_root: docs/experiments + legacy inventories
    status: mandatory-reference-only

  legacy_digital_bridge_rerun:
    source_profile: digital_noisy_legacy
    paper_sets: [OG]
    families: [ref_ent005_lr5e4, ref_ent005_lr2e4, ref_noent_lr5e4]
    unknown_folds: [PA2, PA3, PA4, PA8]
    seeds: [0]
    epochs: 60
    priority: optional
    purpose: optional small rerun to verify new runner can reproduce old digital assumptions
    expected_output_root: results_pa_bridge_digital
    status: optional

  ota_primary_matrix:
    source_profile: ota_core_high_run01
    paper_sets: [OG, DISTINCT]
    families: [ref_ent005_lr2e4, ref_ent005_lr5e4, ref_noent_lr5e4, ref_ls000_noent_lr5e4]
    unknown_folds: all_in_set
    seeds: [0]
    epochs: 60
    priority: mandatory
    purpose: main final OTA experiment
    expected_output_root: results_pa_ota_primary
    status: mandatory

  ota_master_context:
    source_profile: ota_core_high_run01
    paper_sets: [MASTER]
    families: [ref_ent005_lr2e4, ref_ent005_lr5e4, ref_noent_lr5e4]
    unknown_folds: all_in_set
    seeds: [0]
    epochs: 60
    priority: mandatory-near-final
    purpose: full 5-class PA context
    expected_output_root: results_pa_ota_master
    status: mandatory

  ota_protocol_ablation:
    source_profile: ota_core_high_run01
    paper_sets: [OG, DISTINCT, MASTER]
    families: [top_1_or_2_from_primary]
    unknown_folds: all_in_set
    seeds: [0]
    epochs: 60
    priority: after-primary
    purpose: wifi/bluetooth/zigbee per-protocol comparison for best families
    expected_output_root: results_pa_ota_protocol_ablation
    status: mandatory-after-primary

  osr_eval_matrix:
    source_profile: artifact_based
    paper_sets: [OG, DISTINCT, MASTER]
    families: [all_trained_families_selected_for_eval]
    unknown_folds: match_training_runs
    seeds: match_training_runs
    epochs: n/a
    priority: mandatory-after-training
    purpose: VarMax/energy/softmax/entropy/p1p2 evaluation from saved checkpoints
    expected_output_root: results_pa_osr_eval
    status: mandatory
```

### Run-group notes

#### `smoke_functional`

Exists only to verify:

- manifest generation
- worker launch
- dashboard/progress rendering
- artifact completion
- result reduction

#### `legacy_digital_recovered`

This is a **documentation run group**, not a training rerun. It is the persistent reference set for the old digital-noisy world.

#### `legacy_digital_bridge_rerun`

Only run if one of the following happens:

- the new runner appears unable to reproduce the historical backbone ordering,
- the paper needs one explicit “same assumptions, new runner” sanity check,
- or OTA results diverge enough that a bridge experiment is required.

#### `ota_primary_matrix`

This is the core final experiment. It should be treated as the main train matrix.

#### `ota_master_context`

This is required because the final project context includes PA1 and the full five-PA universe, not only the historical OG universe.

#### `ota_protocol_ablation`

This should only run after the primary matrix identifies which family or two families are worth carrying forward.

#### `osr_eval_matrix`

This is mandatory because training alone is not the final result; the final project depends on standardized OSR evaluation from saved artifacts.

---

## 7. Exact minimal rerun matrix

The matrix below is the **minimum required rerun program**.

| run_group | source_profile | paper_set | families | unknowns | seeds | approx number of training runs | why required |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `smoke_functional` | `ota_core_high_run01` | `OG` | `smoke_ent005_lr2e4` | all in set = 4 | `0` | `1 x 4 x 1 = 4` | verify runner, manifests, dashboard, artifacts |
| `ota_primary_matrix` | `ota_core_high_run01` | `OG` | `ref_ent005_lr2e4`, `ref_ent005_lr5e4`, `ref_noent_lr5e4`, `ref_ls000_noent_lr5e4` | 4 | `0` | `4 x 4 x 1 = 16` | legacy-compatible final OTA comparison |
| `ota_primary_matrix` | `ota_core_high_run01` | `DISTINCT` | `ref_ent005_lr2e4`, `ref_ent005_lr5e4`, `ref_noent_lr5e4`, `ref_ls000_noent_lr5e4` | 4 | `0` | `4 x 4 x 1 = 16` | PA1 replacement / distinct-behavior comparison |
| `ota_master_context` | `ota_core_high_run01` | `MASTER` | `ref_ent005_lr2e4`, `ref_ent005_lr5e4`, `ref_noent_lr5e4` | 5 | `0` | `3 x 5 x 1 = 15` | final 5-class context |
| `ota_protocol_ablation` | `ota_core_high_run01` with protocol filter | `OG`, `DISTINCT`, optionally `MASTER` | top 1-2 from primary | all in set | `0` | depends on top families; nominally `3 protocols x 2 families x 8 folds = 48` for `OG+DISTINCT` | show per-protocol sensitivity |

### Seed policy

#### Required first pass

- Start with **seed 0 only** for all mandatory training groups.

#### Multi-seed follow-up

- Add seeds `1,2` only for:
  - top family/families from `ota_primary_matrix`
  - top family/families from `ota_master_context`
  - only after the initial rank ordering is clear

### Why seed-0-first is the correct policy

Because the current uncertainty is primarily about **source transfer and family ranking**, not final confidence intervals. Seed expansion should happen *after* the primary ranking is established.

---

## 8. What not to rerun

### 8.1 Broad `confman_paperish_*` coarse sweep

Do not rerun.

Why:

- the legacy inventories already preserve what that sweep was exploring,
- it served as a coarse narrowing stage,
- and the final branch intentionally replaces it with a compact family grid.

### 8.2 Old cache length sweep

Do not rerun.

Why:

- the legacy program already settled on `cache_len = 16384`,
- the final runner hardcodes `cache_len = 16384`,
- there is no current scientific reason to reopen that axis.

### 8.3 Old notebook UI workflow

Do not rerun.

Why:

- the final branch replaces notebook-driven experiment control with manifest-driven worker processes,
- reproducing the UI workflow adds no scientific value.

### 8.4 Early BT/ZB OTA attempt as standalone evidence

Do not rerun as its own legacy phase.

Why:

- it was exploratory,
- it predates the current OTA source/caching system,
- new unified OTA reruns supersede it.

### 8.5 Redundant known-only baselines

Do not rerun broadly.

Why:

- one or two anchors are enough if needed,
- the main decision boundary now concerns OTA transfer and OSR behavior,
- excessive known-only reruns consume budget without resolving the main final questions.

---

## 9. OSR / evaluation plan

The final evaluation matrix should run **from saved checkpoints / saved run artifacts**, not as ad hoc notebook-only analyses.

### 9.1 Score families to evaluate

Mandatory score families:

- VarMax
- energy
- `pmax`
- `p1-p2`
- entropy
- logit variance

### 9.2 Calibration regimes

Evaluate at least two calibration regimes:

- **oracle upper bound**
- **surrogate / deployable calibration**

If implemented cleanly, the deployable side can later split into:

- surrogate-all
- aligned surrogate
- mismatched surrogate

But the minimum requirement is:

- one realistic deployable regime
- one oracle upper-bound regime

### 9.3 Final CSV metrics to report

Each eval row should include at least:

- `run_name`
- `paper_set`
- `protocol_tag`
- `source_profile`
- `family_tag`
- `unknown_pa`
- `seed`
- `calibration_mode`
- `score_family`
- `known_macro_f1`
- `known_acc`
- `unknown_precision`
- `unknown_recall`
- `unknown_f1`
- `overall_macro_f1`
- `overall_weighted_f1`
- `auroc_unknown_vs_known` if implemented
- `threshold_summary`
- `notes`

### 9.4 Diagnostic-only metrics

Treat these as diagnostic unless explicitly promoted into the decision logic:

- raw entropy without calibrated thresholding
- raw logit variance without calibrated thresholding
- oracle-only best-case thresholds
- any proxy metric used solely for model selection

### 9.5 Evaluation output roots

Recommended output roots:

- `results_pa_osr_eval/leaderboards/`
- `results_pa_osr_eval/per_run/`
- `results_pa_osr_eval/summaries/`

---

## 10. Commands / spec blocks

These are proposed command patterns for the new system. They are examples even if the exact CLI is not yet final.

### 10.1 Smoke

```bash
bash scripts/train/pa_trainctl.sh make smoke_functional
bash scripts/train/pa_trainctl.sh run manifests/smoke_functional.tsv 2
bash scripts/train/pa_trainctl.sh watch manifests/smoke_functional.tsv
bash scripts/train/pa_trainctl.sh reduce results_pa_final_smoke results/smoke_train_leaderboard.csv
```

### 10.2 Main OTA primary matrix

```bash
bash scripts/train/pa_trainctl.sh make ota_primary_matrix
bash scripts/train/pa_trainctl.sh run manifests/ota_primary_matrix.tsv 2
bash scripts/train/pa_trainctl.sh watch manifests/ota_primary_matrix.tsv
bash scripts/train/pa_trainctl.sh reduce results_pa_ota_primary results/ota_primary_train_leaderboard.csv
```

### 10.3 OTA master context

```bash
bash scripts/train/pa_trainctl.sh make ota_master_context
bash scripts/train/pa_trainctl.sh run manifests/ota_master_context.tsv 2
bash scripts/train/pa_trainctl.sh watch manifests/ota_master_context.tsv
bash scripts/train/pa_trainctl.sh reduce results_pa_ota_master results/ota_master_train_leaderboard.csv
```

### 10.4 Protocol ablation

```bash
bash scripts/train/pa_trainctl.sh make ota_protocol_ablation
bash scripts/train/pa_trainctl.sh run manifests/ota_protocol_ablation.tsv 2
bash scripts/train/pa_trainctl.sh watch manifests/ota_protocol_ablation.tsv
bash scripts/train/pa_trainctl.sh reduce results_pa_ota_protocol_ablation results/ota_protocol_ablation_leaderboard.csv
```

### 10.5 Optional legacy bridge rerun

```bash
bash scripts/train/pa_trainctl.sh make legacy_digital_bridge_rerun
bash scripts/train/pa_trainctl.sh run manifests/legacy_digital_bridge_rerun.tsv 2
bash scripts/train/pa_trainctl.sh watch manifests/legacy_digital_bridge_rerun.tsv
bash scripts/train/pa_trainctl.sh reduce results_pa_bridge_digital results/legacy_bridge_train_leaderboard.csv
```

### 10.6 OSR evaluation from saved artifacts

```bash
bash scripts/train/pa_trainctl.sh make osr_eval_matrix
bash scripts/train/pa_trainctl.sh eval manifests/osr_eval_matrix.tsv 2
bash scripts/train/pa_trainctl.sh reduce results_pa_osr_eval results/osr_eval_leaderboard.csv
```

### 10.7 Direct manifest-spec examples

#### Primary matrix spec sketch

```yaml
make_manifest:
  run_group: ota_primary_matrix
  source_profile: ota_core_high_run01
  paper_sets: [OG, DISTINCT]
  families: [ref_ent005_lr2e4, ref_ent005_lr5e4, ref_noent_lr5e4, ref_ls000_noent_lr5e4]
  unknowns: all_in_set
  seeds: [0]
  save_root: results_pa_ota_primary
```

#### Master context spec sketch

```yaml
make_manifest:
  run_group: ota_master_context
  source_profile: ota_core_high_run01
  paper_sets: [MASTER]
  families: [ref_ent005_lr2e4, ref_ent005_lr5e4, ref_noent_lr5e4]
  unknowns: all_in_set
  seeds: [0]
  save_root: results_pa_ota_master
```

---

## 11. Implementation notes for `pa_experiment_catalog.py`

Below is a structured pseudo-spec intended to translate directly into a catalog module.

```python
EXPERIMENT_CATALOG = {
    "source_profiles": {
        "digital_noisy_legacy": {
            "source_type": "digital",
            "source_name": "pilot_noisy_torch",
            "cache_len": 16384,
            "purpose": "legacy reconstruction / optional bridge rerun",
            "priority_tier": "reference",
        },
        "ota_core_high_run01": {
            "source_type": "ota",
            "source_name": "ota_core_high_run01",
            "dataset_tag": "ota_core_high_run01",
            "noise_tag": "high_run01",
            "cache_len": 16384,
            "cache_root": "_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01",
            "purpose": "final OTA experiments",
            "priority_tier": "primary",
        },
    },

    "paper_sets": {
        "OG": {
            "pas": ["PA2", "PA3", "PA4", "PA8"],
            "purpose": "legacy-compatible original PA universe",
        },
        "DISTINCT": {
            "pas": ["PA1", "PA3", "PA4", "PA8"],
            "purpose": "PA1 replacement / distinct behavior comparison",
        },
        "MASTER": {
            "pas": ["PA1", "PA2", "PA3", "PA4", "PA8"],
            "purpose": "final full context",
        },
    },

    "family_configs": {
        "smoke_ent005_lr2e4": {
            "lr": 2e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.30,
            "epochs": 3,
            "early_stopping_patience": None,
            "maps_from_legacy": None,
        },
        "ref_ent005_lr2e4": {
            "lr": 2e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
            "maps_from_legacy": ["ref_base_ent005", "ref_base_lr2e4"],
        },
        "ref_ent005_lr5e4": {
            "lr": 5e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
            "maps_from_legacy": ["ref_base_ent005"],
        },
        "ref_noent_lr5e4": {
            "lr": 5e-4,
            "label_smoothing": 0.10,
            "entropy_loss_weight": 0.00,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
            "maps_from_legacy": ["ref_base_lr2e4", "confman_baseline_openconf"],
        },
        "ref_ls000_noent_lr5e4": {
            "lr": 5e-4,
            "label_smoothing": 0.00,
            "entropy_loss_weight": 0.00,
            "mlp_dropout": 0.30,
            "epochs": 60,
            "early_stopping_patience": 10,
            "maps_from_legacy": ["legacy no-LS / no-entropy ablations"],
        },
        "legacy_bridge_ref_pms_drop040": {
            "lr": 1e-4,
            "weight_decay": 1e-4,
            "lambda_center": 0.1,
            "label_smoothing": 0.05,
            "entropy_loss_weight": 0.05,
            "mlp_dropout": 0.40,
            "grad_clip_norm": 1.0,
            "scheduler_name": "plateau",
            "epochs": 60,
            "early_stopping_patience": 10,
            "maps_from_legacy": ["ref_pms_drop040"],
            "status": "optional bridge only",
        },
    },

    "run_groups": {
        "smoke_functional": {
            "source_profile": "ota_core_high_run01",
            "paper_sets": ["OG"],
            "families": ["smoke_ent005_lr2e4"],
            "unknown_mode": "all_in_set",
            "seeds": [0],
            "epochs": 3,
            "output_root": "results_pa_final_smoke",
            "priority": "tier0",
            "status": "mandatory",
        },
        "legacy_digital_recovered": {
            "source_profile": "digital_noisy_legacy",
            "paper_sets": ["OG"],
            "families": [],
            "unknown_mode": "inventory_only",
            "seeds": [],
            "epochs": None,
            "output_root": "docs/experiments",
            "priority": "reference",
            "status": "no_rerun",
        },
        "legacy_digital_bridge_rerun": {
            "source_profile": "digital_noisy_legacy",
            "paper_sets": ["OG"],
            "families": ["ref_ent005_lr5e4", "ref_ent005_lr2e4", "ref_noent_lr5e4"],
            "unknown_mode": "all_in_set",
            "seeds": [0],
            "epochs": 60,
            "output_root": "results_pa_bridge_digital",
            "priority": "optional",
            "status": "optional",
        },
        "ota_primary_matrix": {
            "source_profile": "ota_core_high_run01",
            "paper_sets": ["OG", "DISTINCT"],
            "families": ["ref_ent005_lr2e4", "ref_ent005_lr5e4", "ref_noent_lr5e4", "ref_ls000_noent_lr5e4"],
            "unknown_mode": "all_in_set",
            "seeds": [0],
            "epochs": 60,
            "output_root": "results_pa_ota_primary",
            "priority": "tier1",
            "status": "mandatory",
        },
        "ota_master_context": {
            "source_profile": "ota_core_high_run01",
            "paper_sets": ["MASTER"],
            "families": ["ref_ent005_lr2e4", "ref_ent005_lr5e4", "ref_noent_lr5e4"],
            "unknown_mode": "all_in_set",
            "seeds": [0],
            "epochs": 60,
            "output_root": "results_pa_ota_master",
            "priority": "tier1",
            "status": "mandatory",
        },
        "ota_protocol_ablation": {
            "source_profile": "ota_core_high_run01",
            "paper_sets": ["OG", "DISTINCT", "MASTER"],
            "families": ["top_selected"],
            "protocols": [["wifi"], ["bluetooth"], ["zigbee"]],
            "unknown_mode": "all_in_set",
            "seeds": [0],
            "epochs": 60,
            "output_root": "results_pa_ota_protocol_ablation",
            "priority": "tier2",
            "status": "mandatory_after_primary",
        },
        "osr_eval_matrix": {
            "source_profile": "artifact_based",
            "paper_sets": ["OG", "DISTINCT", "MASTER"],
            "score_families": ["varmax", "energy", "pmax", "p1p2", "entropy", "logit_variance"],
            "calibration_modes": ["oracle", "surrogate_deployable"],
            "output_root": "results_pa_osr_eval",
            "priority": "tier1",
            "status": "mandatory",
        },
    },

    "output_roots": {
        "results_pa_final_smoke": "smoke training runs",
        "results_pa_ota_primary": "main OTA matrix",
        "results_pa_ota_master": "MASTER-context OTA matrix",
        "results_pa_ota_protocol_ablation": "per-protocol OTA ablations",
        "results_pa_bridge_digital": "optional legacy digital bridge rerun",
        "results_pa_osr_eval": "post-training OSR evaluation",
    },

    "priority_tiers": {
        "tier0": ["smoke_functional"],
        "tier1": ["ota_primary_matrix", "ota_master_context", "osr_eval_matrix"],
        "tier2": ["ota_protocol_ablation"],
        "optional": ["legacy_digital_bridge_rerun"],
        "reference": ["legacy_digital_recovered"],
    },
}
```

### Final implementation guidance

When `pa_experiment_catalog.py` is built, it should:

1. encode **source profiles**, **paper sets**, **family configs**, and **run groups** separately,
2. allow `all_in_set` unknown expansion automatically,
3. support output-root separation by run group,
4. support protocol filtering as a first-class run-group dimension,
5. treat `legacy_digital_recovered` as a reference-only group with no generated training manifest,
6. allow future seed expansion without changing the scientific plan.
