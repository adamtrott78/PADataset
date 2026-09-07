> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../experiments/CONTEXT.md).

# Legacy Digital-Noisy Experiment Reconstruction

This report is generated from local metadata inventories only. It does not include raw checkpoints, tensors, H5 cache contents, or MAT files.

## Inventory counts

- Total inventoried run dirs: 203
- Digital `pilot_noisy_torch` run dirs: 113
- Digital complete summaries: 113
- Digital missing summaries: 0
- Checkpoint metadata rows: 617
- Generated table rows: 16

## Result roots

- `results_pa_confmanifold_refined`: 64
- `results_pa_confmanifold_coarse`: 56
- `results_pa_osr_bank`: 48
- `results_pa_baseline`: 13
- `results_pa_cache_sweep`: 12
- `results_pa_followup`: 4
- `results_pa_finalist`: 2
- `results_pa_ota_btzb`: 2
- `results_pa_smoke`: 2

## Digital-noisy result roots

- `results_pa_confmanifold_refined`: 64
- `results_pa_confmanifold_coarse`: 49

## Unknown folds observed in digital-noisy runs

- `PA2`: 29
- `PA3`: 28
- `PA4`: 28
- `PA8`: 28

## Inferred backbone/family labels

- `(unlabeled)`: 85
- `confman_baseline_knownonly`: 8
- `confman_baseline_openconf`: 8
- `ref_base_ent005`: 4
- `ref_base_lr2e4`: 4
- `ref_pms_drop040`: 4

## Top digital-noisy rows by deployable proxy5

| result_root | run_name | inferred_family | unknown_fold | cache_len | batch_size | epochs | seed | lr | label_smoothing | entropy_loss_weight | mlp_dropout | early_stopping_mode | open_conf_selection_metric | best_epoch | best_val_dqn_proxy_expanded5 | test_dqn_proxy_expanded5 | test_known_macro_f1 | test_known_acc | summary_path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| results_pa_confmanifold_refined | ref_base_nocenter_unkPA2_c16384_seed0 |  | PA2 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 25.0 | 0.9780740076654788 | 0.9911785200607806 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_refined/00-12_04-30-26_ref_base_nocenter_unkPA2_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_smooth_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.05 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 28.0 | 0.9843358513980616 | 0.9889513502518776 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_coarse/17-46_04-29-26_confman_paperish_mid_smooth_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_ent005_unkPA8_c16384_seed0 | ref_base_ent005 | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.05 | 0.3 | open_conf | dqn_proxy_softmax3 | 10.0 | 0.9847159346347232 | 0.987758392658899 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_refined/22-43_04-29-26_ref_base_ent005_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mild_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.02 | 0.5 | open_conf | dqn_proxy_softmax3 | 17.0 | 0.9798988662075752 | 0.9870852707994549 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_coarse/16-46_04-29-26_confman_paperish_mild_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_nocenter_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 12.0 | 0.9812898856808974 | 0.9850653243448724 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_refined/00-21_04-30-26_ref_base_nocenter_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mild_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.02 | 0.5 | open_conf | dqn_proxy_softmax3 | 23.0 | 0.988641889824954 | 0.9824293253199344 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_coarse/16-00_04-29-26_confman_paperish_mild_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mild_unkPA3_c16384_seed0 |  | PA3 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.02 | 0.5 | open_conf | dqn_proxy_softmax3 | 43.0 | 0.9823070814126988 | 0.9814260078192362 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_coarse/15-53_04-29-26_confman_paperish_mild_unkPA3_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_nocenter_unkPA3_c16384_seed0 |  | PA3 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 42.0 | 0.9648735897086174 | 0.9756179607430484 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_refined/00-15_04-30-26_ref_base_nocenter_unkPA3_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_pms_lr2e4_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0002 | 0.05 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 5.0 | 0.9623462412592692 | 0.9741569180931056 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_refined/00-10_04-30-26_ref_pms_lr2e4_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_baseline_knownonly_unkPA8_c16384_seed0 | confman_baseline_knownonly | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | known_only | dqn_proxy_softmax3 | 7.0 | 0.9739646831163928 | 0.9727465214566652 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_coarse/16-26_04-29-26_confman_baseline_knownonly_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_unkPA3_c16384_seed0 |  | PA3 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 48.0 | 0.967821787492759 | 0.9724833368705024 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_coarse/16-52_04-29-26_confman_paperish_mid_unkPA3_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_drop050_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.5 | open_conf | dqn_proxy_softmax3 | 1.0 | 0.960260024227263 | 0.9714106768144743 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_refined/22-25_04-29-26_ref_base_drop050_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_ls002_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.02 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 6.0 | 0.9579853446531325 | 0.9694392523208152 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_refined/21-54_04-29-26_ref_base_ls002_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_baseline_knownonly_unkPA8_c16384_seed0 | confman_baseline_knownonly | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | known_only | dqn_proxy_softmax3 | 7.0 | 0.9630072159411284 | 0.966472354800234 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_coarse/15-38_04-29-26_confman_baseline_knownonly_unkPA8_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_unkPA8_c16384_seed0 |  | PA8 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 16.0 | 0.9647277887363516 | 0.9662643160029816 | 0.9851778656126484 | 0.9851851851851852 | results_pa_confmanifold_coarse/16-12_04-29-26_confman_paperish_mid_unkPA8_c16384_seed0/summary.json |

## Top digital-noisy rows by known macro-F1

| result_root | run_name | inferred_family | unknown_fold | cache_len | batch_size | epochs | seed | lr | label_smoothing | entropy_loss_weight | mlp_dropout | early_stopping_mode | open_conf_selection_metric | best_epoch | best_val_dqn_proxy_expanded5 | test_dqn_proxy_expanded5 | test_known_macro_f1 | test_known_acc | summary_path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| results_pa_confmanifold_coarse | confman_baseline_knownonly_unkPA4_c16384_seed0 | confman_baseline_knownonly | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | known_only | dqn_proxy_softmax3 | 5.0 | 0.7168464699320536 | 0.7109630156246222 | 1.0 | 1.0 | results_pa_confmanifold_coarse/15-37_04-29-26_confman_baseline_knownonly_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_unkPA3_c16384_seed0 |  | PA3 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 25.0 | 0.9442395492966772 | 0.9468017486244188 | 1.0 | 1.0 | results_pa_confmanifold_coarse/16-06_04-29-26_confman_paperish_mid_unkPA3_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_baseline_openconf_unkPA3_c16384_seed0 | confman_baseline_openconf | PA3 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 10.0 | 0.9589248984300812 | 0.962156483135262 | 1.0 | 1.0 | results_pa_confmanifold_coarse/15-42_04-29-26_confman_baseline_openconf_unkPA3_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_smooth_unkPA4_c16384_seed0 |  | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.05 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 28.0 | 0.8783656759710052 | 0.8835674043471112 | 1.0 | 1.0 | results_pa_confmanifold_coarse/17-43_04-29-26_confman_paperish_mid_smooth_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_unkPA4_c16384_seed0 |  | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 18.0 | 0.9274417222381944 | 0.9304452670962052 | 1.0 | 1.0 | results_pa_confmanifold_coarse/16-57_04-29-26_confman_paperish_mid_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_drop050_unkPA4_c16384_seed0 |  | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.5 | open_conf | dqn_proxy_softmax3 | 28.0 | 0.883050269111435 | 0.9029516675164476 | 1.0 | 1.0 | results_pa_confmanifold_refined/22-21_04-29-26_ref_base_drop050_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_drop040_unkPA3_c16384_seed0 |  | PA3 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.4 | open_conf | dqn_proxy_softmax3 | 16.0 | 0.9451043446213876 | 0.9447427441256526 | 1.0 | 1.0 | results_pa_confmanifold_refined/22-07_04-29-26_ref_base_drop040_unkPA3_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_ctrl_unkPA4_c16384_seed0 |  | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 36.0 | 0.8995291852141243 | 0.9051791591140442 | 1.0 | 1.0 | results_pa_confmanifold_refined/21-29_04-29-26_ref_base_ctrl_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_ls005_unkPA4_c16384_seed0 |  | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.05 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 25.0 | 0.9080844035389096 | 0.9229227987078484 | 1.0 | 1.0 | results_pa_confmanifold_refined/21-42_04-29-26_ref_base_ls005_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_refined | ref_base_ent002_unkPA4_c16384_seed0 |  | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.02 | 0.3 | open_conf | dqn_proxy_softmax3 | 18.0 | 0.8663863836398896 | 0.8793309663821892 | 1.0 | 1.0 | results_pa_confmanifold_refined/22-31_04-29-26_ref_base_ent002_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_strong_unkPA2_c16384_seed0 |  | PA2 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.1 | 0.5 | open_conf | dqn_proxy_softmax3 | 13.0 | 0.8937258997276102 | 0.7497713289360439 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_coarse/16-15_04-29-26_confman_paperish_strong_unkPA2_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_unkPA4_c16384_seed0 |  | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 16.0 | 0.8957040159971333 | 0.9066142591095382 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_coarse/16-10_04-29-26_confman_paperish_mid_unkPA4_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mid_unkPA2_c16384_seed0 |  | PA2 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.05 | 0.5 | open_conf | dqn_proxy_softmax3 | 22.0 | 0.8045346339785401 | 0.7978712496431594 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_coarse/16-03_04-29-26_confman_paperish_mid_unkPA2_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_paperish_mild_unkPA2_c16384_seed0 |  | PA2 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0001 | 0.0 | 0.02 | 0.5 | open_conf | dqn_proxy_softmax3 | 8.0 | 0.8704227635049286 | 0.8699613444471442 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_coarse/15-51_04-29-26_confman_paperish_mild_unkPA2_c16384_seed0/summary.json |
| results_pa_confmanifold_coarse | confman_baseline_openconf_unkPA4_c16384_seed0 | confman_baseline_openconf | PA4 | 16384.0 | 16.0 | 200.0 | 0.0 | 0.0005 | 0.1 | 0.0 | 0.3 | open_conf | dqn_proxy_softmax3 | 33.0 | 0.8826454294667284 | 0.8948561051564191 | 0.9962961819809254 | 0.9962962962962963 | results_pa_confmanifold_coarse/15-44_04-29-26_confman_baseline_openconf_unkPA4_c16384_seed0/summary.json |

## First reconstruction conclusion

The old digital-noisy experiment program can be reconstructed from committed metadata inventories. The next step is to map the inferred families and source profile into `pa_experiment_catalog.py`, then rerun only missing/ambiguous cells rather than repeating the entire historical search.

## Preserved historical family interpretation

Extracted from the pre-modularization final_rerun_plan and prior-chat knowledge
at commit `077c8d9466e1a4e70bb8163560e4b52e108cef92`. This appendix preserves
historical correspondence and uncertainty, not new experiment requirements.
The original plan's mandatory rerun/seed policy is superseded. Current family
definitions and overrides belong to the experiment context and executable catalog.
Historical 16384 defaults do not establish the author-confirmed 8192 paper profile.

### Legacy-to-modern correspondence recorded by the old plan

The following correspondences were the plan author's reconstruction/proposal;
an approximate mapping does not reproduce a saved run. Compare the actual
source, PA universe, splits, optimizer, loss weights, selection metric and cache
headers before interpreting a bridge experiment. “Final branch” below names
the historical planning snapshot, not the current scientific operating profile.

| old family name | old source/root | old purpose | old key hyperparameters | new family name | new hyperparameters | exact / approximate / superseded |
| --- | --- | --- | --- | --- | --- | --- |
| `ref_base_ent005` | `results_pa_confmanifold_refined` | reference deployable backbone with entropy regularization | lr `5e-4`, ls `0.10`, entropy `0.05`, dropout `0.30`, batch `16`, epochs `200`, `open_conf`, `dqn_proxy_softmax3` | `ref_ent005_lr5e4` | lr `5e-4`, ls `0.10`, entropy `0.05`, dropout `0.30`, epochs `60`, patience `10`, OTA-first defaults | **approximate modernized equivalent** |
| `ref_base_lr2e4` | `results_pa_confmanifold_refined` / followup context | lower-lr reference control backbone | lr `2e-4`, ls `0.10`, entropy `0.00`, dropout `0.30`, batch `16`, epochs `200`, `open_conf` | `ref_noent_lr5e4` and partially `ref_ent005_lr2e4` | not exact; new family split separates lr and entropy axis | **superseded / split across new families** |
| `ref_pms_drop040` | refined / finalist-followup family | stronger regularized comparison, paperish / PMS style | lr `1e-4`, wd `1e-4`, lambda_center `0.1`, ls `0.05`, entropy `0.05`, dropout `0.40`, grad clip `1.0`, plateau scheduler | none exact in final branch | would require explicit legacy bridge config if rerun | **superseded** |
| `ref_base_nocenter` | `results_pa_confmanifold_refined` | test no-center-loss representation | lr `5e-4`, ls `0.10`, entropy `0.00`, dropout `0.30` | none exact | final branch currently keeps `lambda_center=0.1` globally | **superseded** |
| `confman_baseline_knownonly` | `results_pa_confmanifold_coarse` | known-only stopping baseline | lr `5e-4`, ls `0.10`, entropy `0.00`, dropout `0.30`, `known_only` stop mode | none exact | final system standardized on `open_conf` | **superseded** |
| `confman_baseline_openconf` | `results_pa_confmanifold_coarse` | baseline open-confidence stopping reference | lr `5e-4`, ls `0.10`, entropy `0.00`, dropout `0.30`, `open_conf` | `ref_noent_lr5e4` | close modern equivalent with updated OTA defaults | **approximate** |
| `confman_paperish_mild` | `results_pa_confmanifold_coarse` | coarse broad-search mild regularization variant | lr `1e-4`, ls `0.00`, entropy `0.02`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** |
| `confman_paperish_mid` | `results_pa_confmanifold_coarse` | coarse broad-search mid regularization variant | lr `1e-4`, ls `0.00`, entropy `0.05`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** |
| `confman_paperish_mid_smooth` | `results_pa_confmanifold_coarse` | coarse broad-search mid + smoothing | lr `1e-4`, ls `0.05`, entropy `0.05`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** |
| `confman_paperish_strong` | `results_pa_confmanifold_coarse` | coarse broad-search stronger regularization variant | lr `1e-4`, ls `0.00`, entropy `0.10`, dropout `0.50` | none exact | no direct final branch equivalent | **superseded** |

### Naming mismatch resolution

The old refined-family names bundled multiple axes into a single historical label. The new final-branch families separate the retained axes more cleanly:

- old `ref_base_ent005` maps most directly to **`ref_ent005_lr5e4`**
- old `ref_base_lr2e4` is **not one exact family** in the final branch; its legacy role is now represented by comparing:
  - `ref_ent005_lr2e4`
  - `ref_noent_lr5e4`
- old no-label-smoothing / no-entropy ablations map to **`ref_ls000_noent_lr5e4`**
- old center-loss ablations and paperish coarse families are treated as **superseded**, not as mandatory exact reruns

---

### Original confidence-labeled hyperparameter reconstruction

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

### Findings and limitations retained from the old knowledge export

- **Committed inventory evidence:** the digital `pilot_noisy_torch` subset had
  113 completed summaries over PA2/PA3/PA4/PA8; these counts describe the sampled
  inventory, not all subsequent research. Earlier sections retain the result
  roots and recovered metrics.
- **Reconstructed chronology:** baseline/cache sweeps led to coarse confidence
  manifold searches, refined reference families, an OSR backbone bank, finalist
  follow-ups and exploratory Bluetooth/Zigbee OTA transfer checks.
- **Prior-chat interpretation, not newly verified ranking:** `ref_base_ent005`
  was regarded as the strongest deployable candidate, `ref_base_lr2e4` as a
  control, and `ref_pms_drop040` as a structured comparison. PA2 was considered
  repeatedly difficult, with PA8 often easier. Do not promote these judgments
  to current OTA results or general behavior rankings.
- **Historical scope:** early BT/ZB OTA runs were limited transfer experiments,
  not the later unified OTA paper evidence. Old digital work used four PAs;
  later DISTINCT/MASTER sets change the task and cannot be compared by run name
  alone.
- **Interpretation lesson:** strong closed-set accuracy or an oracle/proxy score
  need not imply reliable rejection under available deployment calibration.
  DQN-style proxy selection metrics are not proof that a DQN decision head ran.
  Read method-specific calibration definitions before comparing thresholds.
- **Uncertainty retained:** center-loss values and some optimizer details were
  not uniformly preserved. Family names mixed source, fold, cache length,
  selection mode and timestamp. The confidence labels above must remain attached
  to recovered values; saved configuration is needed for an exact replication.
