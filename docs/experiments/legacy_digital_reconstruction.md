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
