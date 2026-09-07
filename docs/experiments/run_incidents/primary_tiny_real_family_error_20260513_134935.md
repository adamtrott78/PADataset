> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../../experiments/CONTEXT.md).

# Primary tiny real-family incident

## Run

- run_name: `og_ref_ent005_lr2e4_unkPA2_c16384_seed0`
- run_dir: `results_pa_ota_primary/og_ref_ent005_lr2e4_unkPA2_c16384_seed0`
- manifest: `manifests/primary_tiny_real_family.tsv`
- log_source: `results/train_workers/og_ref_ent005_lr2e4_unkPA2_c16384_seed0_20260513_133216.log`

## Artifact check

```text
OK config.json
OK best_model.pt
OK final_model.pt
OK history.json
MISSING summary.json
MISSING train_complete.json
OK train_error.json
OK train_progress.json
```

## train_error.json

```json
{
    "run_name": "og_ref_ent005_lr2e4_unkPA2_c16384_seed0",
    "cfg_path": "/home/atrott/adamArchives/Adam/varMax/PADataset/manifests/configs/primary_tiny_real_family/og_ref_ent005_lr2e4_unkPA2_c16384_seed0.json",
    "gpu": "1",
    "error": "ValueError('The number of FixedLocator locations (3), usually from a call to set_ticks, does not match the number of labels (4).')",
    "elapsed_sec": 273.59328842163086
}
```

## Per-run log tail

```text
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4175 | steps=7875 | pct=53.02 | loss_so_far=0.47437 | steps_per_sec=35.932
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4200 | steps=7875 | pct=53.33 | loss_so_far=0.47401 | steps_per_sec=35.931
Epoch 1/1:  53%|█████▎    | 4204/7875 [01:57<01:42, 35.75it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4225 | steps=7875 | pct=53.65 | loss_so_far=0.47358 | steps_per_sec=35.929
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4250 | steps=7875 | pct=53.97 | loss_so_far=0.47312 | steps_per_sec=35.928
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4275 | steps=7875 | pct=54.29 | loss_so_far=0.47273 | steps_per_sec=35.927
Epoch 1/1:  54%|█████▍    | 4276/7875 [01:59<01:40, 35.74it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4300 | steps=7875 | pct=54.60 | loss_so_far=0.47227 | steps_per_sec=35.925
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4325 | steps=7875 | pct=54.92 | loss_so_far=0.47180 | steps_per_sec=35.924
Epoch 1/1:  55%|█████▌    | 4348/7875 [02:01<01:38, 35.72it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4350 | steps=7875 | pct=55.24 | loss_so_far=0.47133 | steps_per_sec=35.923
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4375 | steps=7875 | pct=55.56 | loss_so_far=0.47085 | steps_per_sec=35.921
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4400 | steps=7875 | pct=55.87 | loss_so_far=0.47080 | steps_per_sec=35.920
Epoch 1/1:  56%|█████▌    | 4420/7875 [02:03<01:36, 35.72it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4425 | steps=7875 | pct=56.19 | loss_so_far=0.47040 | steps_per_sec=35.919
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4450 | steps=7875 | pct=56.51 | loss_so_far=0.46996 | steps_per_sec=35.918
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4475 | steps=7875 | pct=56.83 | loss_so_far=0.46950 | steps_per_sec=35.917
Epoch 1/1:  57%|█████▋    | 4492/7875 [02:05<01:34, 35.71it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4500 | steps=7875 | pct=57.14 | loss_so_far=0.46905 | steps_per_sec=35.916
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4525 | steps=7875 | pct=57.46 | loss_so_far=0.46872 | steps_per_sec=35.914
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4550 | steps=7875 | pct=57.78 | loss_so_far=0.46828 | steps_per_sec=35.913
Epoch 1/1:  58%|█████▊    | 4564/7875 [02:07<01:32, 35.70it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4575 | steps=7875 | pct=58.10 | loss_so_far=0.46785 | steps_per_sec=35.911
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4600 | steps=7875 | pct=58.41 | loss_so_far=0.46758 | steps_per_sec=35.910
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4625 | steps=7875 | pct=58.73 | loss_so_far=0.46727 | steps_per_sec=35.909
Epoch 1/1:  59%|█████▉    | 4636/7875 [02:09<01:30, 35.70it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4650 | steps=7875 | pct=59.05 | loss_so_far=0.46707 | steps_per_sec=35.907
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4675 | steps=7875 | pct=59.37 | loss_so_far=0.46668 | steps_per_sec=35.905
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4700 | steps=7875 | pct=59.68 | loss_so_far=0.46627 | steps_per_sec=35.904
Epoch 1/1:  60%|█████▉    | 4708/7875 [02:11<01:28, 35.65it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4725 | steps=7875 | pct=60.00 | loss_so_far=0.46585 | steps_per_sec=35.902
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4750 | steps=7875 | pct=60.32 | loss_so_far=0.46543 | steps_per_sec=35.901
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4775 | steps=7875 | pct=60.63 | loss_so_far=0.46503 | steps_per_sec=35.899
Epoch 1/1:  61%|██████    | 4780/7875 [02:13<01:26, 35.64it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4800 | steps=7875 | pct=60.95 | loss_so_far=0.46463 | steps_per_sec=35.897
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4825 | steps=7875 | pct=61.27 | loss_so_far=0.46426 | steps_per_sec=35.895
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4850 | steps=7875 | pct=61.59 | loss_so_far=0.46387 | steps_per_sec=35.893
Epoch 1/1:  62%|██████▏   | 4852/7875 [02:15<01:24, 35.60it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4875 | steps=7875 | pct=61.90 | loss_so_far=0.46347 | steps_per_sec=35.892
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4900 | steps=7875 | pct=62.22 | loss_so_far=0.46309 | steps_per_sec=35.888
Epoch 1/1:  63%|██████▎   | 4924/7875 [02:17<01:23, 35.53it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4925 | steps=7875 | pct=62.54 | loss_so_far=0.46271 | steps_per_sec=35.885
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4950 | steps=7875 | pct=62.86 | loss_so_far=0.46233 | steps_per_sec=35.880
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=4975 | steps=7875 | pct=63.17 | loss_so_far=0.46196 | steps_per_sec=35.877
Epoch 1/1:  63%|██████▎   | 4996/7875 [02:19<01:21, 35.43it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5000 | steps=7875 | pct=63.49 | loss_so_far=0.46159 | steps_per_sec=35.875
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5025 | steps=7875 | pct=63.81 | loss_so_far=0.46122 | steps_per_sec=35.871
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5050 | steps=7875 | pct=64.13 | loss_so_far=0.46088 | steps_per_sec=35.868
Epoch 1/1:  64%|██████▍   | 5067/7875 [02:21<01:19, 35.38it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5075 | steps=7875 | pct=64.44 | loss_so_far=0.46051 | steps_per_sec=35.865
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5100 | steps=7875 | pct=64.76 | loss_so_far=0.46018 | steps_per_sec=35.863
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5125 | steps=7875 | pct=65.08 | loss_so_far=0.46004 | steps_per_sec=35.861
Epoch 1/1:  65%|██████▌   | 5138/7875 [02:23<01:17, 35.38it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5150 | steps=7875 | pct=65.40 | loss_so_far=0.45980 | steps_per_sec=35.858
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5175 | steps=7875 | pct=65.71 | loss_so_far=0.45980 | steps_per_sec=35.854
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5200 | steps=7875 | pct=66.03 | loss_so_far=0.45953 | steps_per_sec=35.852
Epoch 1/1:  66%|██████▌   | 5209/7875 [02:25<01:15, 35.36it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5225 | steps=7875 | pct=66.35 | loss_so_far=0.45927 | steps_per_sec=35.850
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5250 | steps=7875 | pct=66.67 | loss_so_far=0.45912 | steps_per_sec=35.849
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5275 | steps=7875 | pct=66.98 | loss_so_far=0.45882 | steps_per_sec=35.845
Epoch 1/1:  67%|██████▋   | 5280/7875 [02:27<01:13, 35.35it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5300 | steps=7875 | pct=67.30 | loss_so_far=0.45858 | steps_per_sec=35.843
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5325 | steps=7875 | pct=67.62 | loss_so_far=0.45826 | steps_per_sec=35.839
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5350 | steps=7875 | pct=67.94 | loss_so_far=0.45793 | steps_per_sec=35.836
Epoch 1/1:  68%|██████▊   | 5351/7875 [02:29<01:11, 35.30it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5375 | steps=7875 | pct=68.25 | loss_so_far=0.45762 | steps_per_sec=35.834
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5400 | steps=7875 | pct=68.57 | loss_so_far=0.45729 | steps_per_sec=35.831
Epoch 1/1:  69%|██████▉   | 5422/7875 [02:31<01:09, 35.33it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5425 | steps=7875 | pct=68.89 | loss_so_far=0.45695 | steps_per_sec=35.829
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5450 | steps=7875 | pct=69.21 | loss_so_far=0.45662 | steps_per_sec=35.826
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5475 | steps=7875 | pct=69.52 | loss_so_far=0.45629 | steps_per_sec=35.823
Epoch 1/1:  70%|██████▉   | 5493/7875 [02:33<01:07, 35.32it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5500 | steps=7875 | pct=69.84 | loss_so_far=0.45595 | steps_per_sec=35.822
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5525 | steps=7875 | pct=70.16 | loss_so_far=0.45565 | steps_per_sec=35.819
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5550 | steps=7875 | pct=70.48 | loss_so_far=0.45533 | steps_per_sec=35.816
Epoch 1/1:  71%|███████   | 5564/7875 [02:35<01:05, 35.29it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5575 | steps=7875 | pct=70.79 | loss_so_far=0.45501 | steps_per_sec=35.814
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5600 | steps=7875 | pct=71.11 | loss_so_far=0.45468 | steps_per_sec=35.811
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5625 | steps=7875 | pct=71.43 | loss_so_far=0.45436 | steps_per_sec=35.810
Epoch 1/1:  72%|███████▏  | 5635/7875 [02:37<01:03, 35.30it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5650 | steps=7875 | pct=71.75 | loss_so_far=0.45406 | steps_per_sec=35.808
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5675 | steps=7875 | pct=72.06 | loss_so_far=0.45375 | steps_per_sec=35.807
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5700 | steps=7875 | pct=72.38 | loss_so_far=0.45346 | steps_per_sec=35.806
Epoch 1/1:  72%|███████▏  | 5707/7875 [02:39<01:01, 35.38it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5725 | steps=7875 | pct=72.70 | loss_so_far=0.45315 | steps_per_sec=35.805
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5750 | steps=7875 | pct=73.02 | loss_so_far=0.45284 | steps_per_sec=35.802
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5775 | steps=7875 | pct=73.33 | loss_so_far=0.45253 | steps_per_sec=35.800
Epoch 1/1:  73%|███████▎  | 5778/7875 [02:41<00:59, 35.37it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5800 | steps=7875 | pct=73.65 | loss_so_far=0.45222 | steps_per_sec=35.798
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5825 | steps=7875 | pct=73.97 | loss_so_far=0.45192 | steps_per_sec=35.794
Epoch 1/1:  74%|███████▍  | 5849/7875 [02:43<00:57, 35.30it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5850 | steps=7875 | pct=74.29 | loss_so_far=0.45166 | steps_per_sec=35.792
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5875 | steps=7875 | pct=74.60 | loss_so_far=0.45138 | steps_per_sec=35.789
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5900 | steps=7875 | pct=74.92 | loss_so_far=0.45110 | steps_per_sec=35.787
Epoch 1/1:  75%|███████▌  | 5920/7875 [02:45<00:55, 35.27it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5925 | steps=7875 | pct=75.24 | loss_so_far=0.45081 | steps_per_sec=35.783
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5950 | steps=7875 | pct=75.56 | loss_so_far=0.45052 | steps_per_sec=35.781
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=5975 | steps=7875 | pct=75.87 | loss_so_far=0.45023 | steps_per_sec=35.779
Epoch 1/1:  76%|███████▌  | 5991/7875 [02:47<00:53, 35.26it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6000 | steps=7875 | pct=76.19 | loss_so_far=0.44994 | steps_per_sec=35.777
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6025 | steps=7875 | pct=76.51 | loss_so_far=0.44969 | steps_per_sec=35.776
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6050 | steps=7875 | pct=76.83 | loss_so_far=0.44949 | steps_per_sec=35.773
Epoch 1/1:  77%|███████▋  | 6062/7875 [02:49<00:51, 35.27it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6075 | steps=7875 | pct=77.14 | loss_so_far=0.44934 | steps_per_sec=35.771
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6100 | steps=7875 | pct=77.46 | loss_so_far=0.44949 | steps_per_sec=35.769
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6125 | steps=7875 | pct=77.78 | loss_so_far=0.44939 | steps_per_sec=35.766
Epoch 1/1:  78%|███████▊  | 6133/7875 [02:51<00:49, 35.24it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6150 | steps=7875 | pct=78.10 | loss_so_far=0.44917 | steps_per_sec=35.762
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6175 | steps=7875 | pct=78.41 | loss_so_far=0.44892 | steps_per_sec=35.761
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6200 | steps=7875 | pct=78.73 | loss_so_far=0.44865 | steps_per_sec=35.758
Epoch 1/1:  79%|███████▉  | 6204/7875 [02:53<00:47, 35.21it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6225 | steps=7875 | pct=79.05 | loss_so_far=0.44839 | steps_per_sec=35.756
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6250 | steps=7875 | pct=79.37 | loss_so_far=0.44814 | steps_per_sec=35.753
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6275 | steps=7875 | pct=79.68 | loss_so_far=0.44788 | steps_per_sec=35.750
Epoch 1/1:  80%|███████▉  | 6275/7875 [02:55<00:45, 35.17it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6300 | steps=7875 | pct=80.00 | loss_so_far=0.44761 | steps_per_sec=35.747
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6325 | steps=7875 | pct=80.32 | loss_so_far=0.44736 | steps_per_sec=35.746
Epoch 1/1:  81%|████████  | 6346/7875 [02:57<00:43, 35.18it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6350 | steps=7875 | pct=80.63 | loss_so_far=0.44714 | steps_per_sec=35.743
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6375 | steps=7875 | pct=80.95 | loss_so_far=0.44689 | steps_per_sec=35.742
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6400 | steps=7875 | pct=81.27 | loss_so_far=0.44665 | steps_per_sec=35.741
Epoch 1/1:  81%|████████▏ | 6417/7875 [02:59<00:41, 35.25it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6425 | steps=7875 | pct=81.59 | loss_so_far=0.44639 | steps_per_sec=35.740
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6450 | steps=7875 | pct=81.90 | loss_so_far=0.44622 | steps_per_sec=35.738
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6475 | steps=7875 | pct=82.22 | loss_so_far=0.44605 | steps_per_sec=35.737
Epoch 1/1:  82%|████████▏ | 6488/7875 [03:01<00:39, 35.28it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6500 | steps=7875 | pct=82.54 | loss_so_far=0.44591 | steps_per_sec=35.735
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6525 | steps=7875 | pct=82.86 | loss_so_far=0.44572 | steps_per_sec=35.732
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6550 | steps=7875 | pct=83.17 | loss_so_far=0.44547 | steps_per_sec=35.729
Epoch 1/1:  83%|████████▎ | 6559/7875 [03:03<00:37, 35.19it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6575 | steps=7875 | pct=83.49 | loss_so_far=0.44523 | steps_per_sec=35.726
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6600 | steps=7875 | pct=83.81 | loss_so_far=0.44504 | steps_per_sec=35.724
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6625 | steps=7875 | pct=84.13 | loss_so_far=0.44482 | steps_per_sec=35.722
Epoch 1/1:  84%|████████▍ | 6630/7875 [03:05<00:35, 35.19it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6650 | steps=7875 | pct=84.44 | loss_so_far=0.44459 | steps_per_sec=35.720
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6675 | steps=7875 | pct=84.76 | loss_so_far=0.44435 | steps_per_sec=35.717
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6700 | steps=7875 | pct=85.08 | loss_so_far=0.44412 | steps_per_sec=35.715
Epoch 1/1:  85%|████████▌ | 6701/7875 [03:07<00:33, 35.16it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6725 | steps=7875 | pct=85.40 | loss_so_far=0.44392 | steps_per_sec=35.713
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6750 | steps=7875 | pct=85.71 | loss_so_far=0.44370 | steps_per_sec=35.710
Epoch 1/1:  86%|████████▌ | 6772/7875 [03:09<00:31, 35.14it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6775 | steps=7875 | pct=86.03 | loss_so_far=0.44354 | steps_per_sec=35.708
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6800 | steps=7875 | pct=86.35 | loss_so_far=0.44331 | steps_per_sec=35.706
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6825 | steps=7875 | pct=86.67 | loss_so_far=0.44308 | steps_per_sec=35.703
Epoch 1/1:  87%|████████▋ | 6843/7875 [03:11<00:29, 35.12it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6850 | steps=7875 | pct=86.98 | loss_so_far=0.44286 | steps_per_sec=35.701
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6875 | steps=7875 | pct=87.30 | loss_so_far=0.44263 | steps_per_sec=35.698
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6900 | steps=7875 | pct=87.62 | loss_so_far=0.44241 | steps_per_sec=35.696
Epoch 1/1:  88%|████████▊ | 6914/7875 [03:13<00:27, 35.10it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6925 | steps=7875 | pct=87.94 | loss_so_far=0.44218 | steps_per_sec=35.694
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6950 | steps=7875 | pct=88.25 | loss_so_far=0.44195 | steps_per_sec=35.693
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=6975 | steps=7875 | pct=88.57 | loss_so_far=0.44173 | steps_per_sec=35.692
Epoch 1/1:  89%|████████▊ | 6985/7875 [03:15<00:25, 35.16it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7000 | steps=7875 | pct=88.89 | loss_so_far=0.44150 | steps_per_sec=35.689
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7025 | steps=7875 | pct=89.21 | loss_so_far=0.44131 | steps_per_sec=35.687
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7050 | steps=7875 | pct=89.52 | loss_so_far=0.44109 | steps_per_sec=35.685
Epoch 1/1:  90%|████████▉ | 7056/7875 [03:17<00:23, 35.15it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7075 | steps=7875 | pct=89.84 | loss_so_far=0.44088 | steps_per_sec=35.684
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7100 | steps=7875 | pct=90.16 | loss_so_far=0.44066 | steps_per_sec=35.684
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7125 | steps=7875 | pct=90.48 | loss_so_far=0.44044 | steps_per_sec=35.682
Epoch 1/1:  91%|█████████ | 7127/7875 [03:19<00:21, 35.24it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7150 | steps=7875 | pct=90.79 | loss_so_far=0.44022 | steps_per_sec=35.680
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7175 | steps=7875 | pct=91.11 | loss_so_far=0.44001 | steps_per_sec=35.678
Epoch 1/1:  91%|█████████▏| 7198/7875 [03:21<00:19, 35.21it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7200 | steps=7875 | pct=91.43 | loss_so_far=0.43979 | steps_per_sec=35.677
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7225 | steps=7875 | pct=91.75 | loss_so_far=0.43959 | steps_per_sec=35.675
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7250 | steps=7875 | pct=92.06 | loss_so_far=0.43940 | steps_per_sec=35.674
Epoch 1/1:  92%|█████████▏| 7269/7875 [03:23<00:17, 35.22it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7275 | steps=7875 | pct=92.38 | loss_so_far=0.43930 | steps_per_sec=35.673
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7300 | steps=7875 | pct=92.70 | loss_so_far=0.43941 | steps_per_sec=35.671
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7325 | steps=7875 | pct=93.02 | loss_so_far=0.43926 | steps_per_sec=35.669
Epoch 1/1:  93%|█████████▎| 7340/7875 [03:25<00:15, 35.20it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7350 | steps=7875 | pct=93.33 | loss_so_far=0.43912 | steps_per_sec=35.667
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7375 | steps=7875 | pct=93.65 | loss_so_far=0.43894 | steps_per_sec=35.665
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7400 | steps=7875 | pct=93.97 | loss_so_far=0.43875 | steps_per_sec=35.664
Epoch 1/1:  94%|█████████▍| 7411/7875 [03:27<00:13, 35.21it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7425 | steps=7875 | pct=94.29 | loss_so_far=0.43855 | steps_per_sec=35.663
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7450 | steps=7875 | pct=94.60 | loss_so_far=0.43836 | steps_per_sec=35.662
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7475 | steps=7875 | pct=94.92 | loss_so_far=0.43828 | steps_per_sec=35.659
Epoch 1/1:  95%|█████████▌| 7482/7875 [03:29<00:11, 35.20it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7500 | steps=7875 | pct=95.24 | loss_so_far=0.43810 | steps_per_sec=35.657
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7525 | steps=7875 | pct=95.56 | loss_so_far=0.43792 | steps_per_sec=35.655
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7550 | steps=7875 | pct=95.87 | loss_so_far=0.43773 | steps_per_sec=35.653
Epoch 1/1:  96%|█████████▌| 7553/7875 [03:31<00:09, 35.13it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7575 | steps=7875 | pct=96.19 | loss_so_far=0.43754 | steps_per_sec=35.650
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7600 | steps=7875 | pct=96.51 | loss_so_far=0.43735 | steps_per_sec=35.648
Epoch 1/1:  97%|█████████▋| 7624/7875 [03:33<00:07, 35.12it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7625 | steps=7875 | pct=96.83 | loss_so_far=0.43718 | steps_per_sec=35.647
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7650 | steps=7875 | pct=97.14 | loss_so_far=0.43699 | steps_per_sec=35.646
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7675 | steps=7875 | pct=97.46 | loss_so_far=0.43680 | steps_per_sec=35.644
Epoch 1/1:  98%|█████████▊| 7695/7875 [03:35<00:05, 35.15it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7700 | steps=7875 | pct=97.78 | loss_so_far=0.43661 | steps_per_sec=35.643
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7725 | steps=7875 | pct=98.10 | loss_so_far=0.43642 | steps_per_sec=35.640
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7750 | steps=7875 | pct=98.41 | loss_so_far=0.43623 | steps_per_sec=35.638
Epoch 1/1:  99%|█████████▊| 7766/7875 [03:37<00:03, 35.12it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7775 | steps=7875 | pct=98.73 | loss_so_far=0.43604 | steps_per_sec=35.637
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7800 | steps=7875 | pct=99.05 | loss_so_far=0.43585 | steps_per_sec=35.636
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7825 | steps=7875 | pct=99.37 | loss_so_far=0.43567 | steps_per_sec=35.635
Epoch 1/1: 100%|█████████▉| 7837/7875 [03:39<00:01, 35.20it/s]TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7850 | steps=7875 | pct=99.68 | loss_so_far=0.43548 | steps_per_sec=35.634
TRAIN_STEP | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | step=7875 | steps=7875 | pct=100.00 | loss_so_far=0.43529 | steps_per_sec=35.633
                                                              TRAIN_EPOCH_TRAIN_DONE | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | train_loss=0.43529
Epoch 001 | train_loss=0.4353 | ce=0.3909 | ent=0.3569 | center=0.2657 | val_loss=0.0795 | val_acc=1.0000 | val_macro_f1=1.0000 | val_dqn_proxy_softmax3=0.8497 | val_dqn_proxy_expanded5=0.8830
TRAIN_EPOCH_DONE | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | epoch=1 | epochs=1 | train_loss=0.43529 | val_loss=0.07947 | val_acc=1.00000 | val_macro_f1=1.00000
RUN_STAGE | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | stage=post_train_eval_start
TRAIN ERROR | run_name=og_ref_ent005_lr2e4_unkPA2_c16384_seed0 | gpu=1 | error=ValueError('The number of FixedLocator locations (3), usually from a call to set_ticks, does not match the number of labels (4).')
Traceback (most recent call last):
  File "/home/atrott/adamArchives/Adam/varMax/PADataset/experiments/pa_train_one.py", line 87, in main
    summary = run_experiment(cfg, data_root=args.data_root)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/Adam/varMax/PADataset/discriminate.py", line 944, in run_experiment
    known_stats = evaluate_classifier(
                  ^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/torch/utils/_contextlib.py", line 116, in decorate_context
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/Adam/varMax/PADataset/evaluate.py", line 217, in evaluate_classifier
    disp.plot(ax=ax, cmap="Blues", xticks_rotation=45, colorbar=False)
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/sklearn/metrics/_plot/confusion_matrix.py", line 188, in plot
    ax.set(
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 146, in <lambda>
    cls.set = lambda self, **kwargs: Artist.set(self, **kwargs)
                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 1241, in set
    return self._internal_update(cbook.normalize_kwargs(kwargs, self))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 1233, in _internal_update
    return self._update_props(
           ^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 1209, in _update_props
    ret.append(func(v))
               ^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/axes/_base.py", line 74, in wrapper
    return get_method(self)(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/axis.py", line 2106, in set_ticklabels
    raise ValueError(
ValueError: The number of FixedLocator locations (3), usually from a call to set_ticks, does not match the number of labels (4).
Traceback (most recent call last):
  File "/home/atrott/adamArchives/Adam/varMax/PADataset/experiments/pa_train_one.py", line 136, in <module>
    main()
  File "/home/atrott/adamArchives/Adam/varMax/PADataset/experiments/pa_train_one.py", line 87, in main
    summary = run_experiment(cfg, data_root=args.data_root)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/Adam/varMax/PADataset/discriminate.py", line 944, in run_experiment
    known_stats = evaluate_classifier(
                  ^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/torch/utils/_contextlib.py", line 116, in decorate_context
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/Adam/varMax/PADataset/evaluate.py", line 217, in evaluate_classifier
    disp.plot(ax=ax, cmap="Blues", xticks_rotation=45, colorbar=False)
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/sklearn/metrics/_plot/confusion_matrix.py", line 188, in plot
    ax.set(
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 146, in <lambda>
    cls.set = lambda self, **kwargs: Artist.set(self, **kwargs)
                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 1241, in set
    return self._internal_update(cbook.normalize_kwargs(kwargs, self))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 1233, in _internal_update
    return self._update_props(
           ^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/artist.py", line 1209, in _update_props
    ret.append(func(v))
               ^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/axes/_base.py", line 74, in wrapper
    return get_method(self)(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/atrott/adamArchives/venvs/DNNs/lib/python3.12/site-packages/matplotlib/axis.py", line 2106, in set_ticklabels
    raise ValueError(
ValueError: The number of FixedLocator locations (3), usually from a call to set_ticks, does not match the number of labels (4).
```
