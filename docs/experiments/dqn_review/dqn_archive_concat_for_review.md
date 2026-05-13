
================================================================
# FILE: docs/experiments/legacy_notebook_inventory.md
================================================================

# Legacy notebook inventory

## `archive/model/PADiscriminate.ipynb`

- size_kb: `5.8`
- n_cells: `6`
- keyword_hits: `open set, OSR, VarMax, unknown`

## `archive/model/PAEvaluate.ipynb`

- size_kb: `120.2`
- n_cells: `32`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb`

- size_kb: `522.4`
- n_cells: `37`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `legacy/notebooks/non_pa/DQN_CICIDS_Part_v2.ipynb`

- size_kb: `32.6`
- n_cells: `13`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `legacy/notebooks/non_pa/DQN_UNSW.ipynb`

- size_kb: `85.1`
- n_cells: `16`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `legacy/notebooks/non_pa/cnn_unsw.ipynb`

- size_kb: `373.4`
- n_cells: `23`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `legacy/notebooks/pa_cnn_osr/PADiscriminate.ipynb`

- size_kb: `5218.4`
- n_cells: `27`
- keyword_hits: `DQN, open set, OSR, VarMax, entropy, unknown`

## `legacy/notebooks/pa_cnn_osr/PAEvaluate.ipynb`

- size_kb: `327.1`
- n_cells: `59`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `legacy/notebooks/pa_cnn_osr/PAValidate.ipynb`

- size_kb: `3.1`
- n_cells: `4`
- keyword_hits: `none`

## `legacy/txrx_debug/splice.ipynb`

- size_kb: `4.5`
- n_cells: `7`
- keyword_hits: `VarMax`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/CNN_CICIDS_runtime.ipynb`

- size_kb: `522.4`
- n_cells: `37`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/DQN_CICIDS_Part_v2.ipynb`

- size_kb: `32.6`
- n_cells: `13`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/DQN_UNSW.ipynb`

- size_kb: `85.1`
- n_cells: `16`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/PADiscriminate.ipynb`

- size_kb: `5218.4`
- n_cells: `27`
- keyword_hits: `DQN, open set, OSR, VarMax, entropy, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/PAEvaluate.ipynb`

- size_kb: `327.1`
- n_cells: `59`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/PAValidate.ipynb`

- size_kb: `3.1`
- n_cells: `4`
- keyword_hits: `none`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/archive/model/PADiscriminate.ipynb`

- size_kb: `5.8`
- n_cells: `6`
- keyword_hits: `open set, OSR, VarMax, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/archive/model/PAEvaluate.ipynb`

- size_kb: `120.2`
- n_cells: `32`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/cnn_unsw.ipynb`

- size_kb: `373.4`
- n_cells: `23`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/txrx/splice.ipynb`

- size_kb: `4.5`
- n_cells: `7`
- keyword_hits: `VarMax`

================================================================
# FILE: docs/experiments/shreyash_dqn_backbone_recovery.md
================================================================

# Shreyash DQN/CNN backbone recovery

This document extracts implementation evidence from the four legacy non-PA notebooks associated with Shreyash's CICIDS/UNSW CNN+DQN workflow.

The purpose is **not** to make this workflow mandatory for the final OTA matrix yet. The purpose is to preserve the recipe so it can later be ported into a clean PA model-family track.

## Scope

- `legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb`
- `legacy/notebooks/non_pa/DQN_CICIDS_Part_v2.ipynb`
- `legacy/notebooks/non_pa/DQN_UNSW.ipynb`
- `legacy/notebooks/non_pa/cnn_unsw.ipynb`

## Recovery questions

1. What CNN/backbone architecture was used?
2. What preprocessing/input representation was assumed?
3. What training objective, optimizer, epochs, batch size, and regularization were used?
4. What DQN state/action/reward structure was used?
5. What parts already exist in `dqn_osr.py`?
6. What still needs to be ported into the final PA runner?

---

## `legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb`

- cells: `37`
- size_kb: `522.4`

- signal_cells: `28`

### cell 2 `code` — import matplotlib.pyplot as plt

```python
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.metrics import f1_score, accuracy_score
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Conv1D, MaxPooling1D, GlobalAveragePooling1D, Dense, Dropout, Input, ReLU, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import tensorflow as tf
```

### cell 3 `code` — #Load dataset

```python
#Load dataset
df = pd.read_csv('clean_df.csv')  # Ensure this file path is correct

# Step 1: Combine specified classes into 'Unknown'
unknown_classes = [
     'Web Attack – Brute Force', 'Web Attack – XSS',
    'Infiltration', 'Web Attack – SQL Injection', 'Heartbleed'
]
df[' Label'] = df[' Label'].apply(lambda x: 'Unknown' if x in unknown_classes else x)

# Verify and filter dataset size
print(f"Initial dataset shape: {df.shape}")
print(f"Label counts:\n{df[' Label'].value_counts()}")

# Define sample sizes
expected_counts = {
    'BENIGN': 5499,
    'Unknown': 2227,  # Bot (1,966) + Brute Force (1,507) + XSS (652) + Infiltration (36) + SQL Injection (21) + Heartbleed (11)
    'DoS Hulk': 5499,
    'PortScan': 5499,
    'DDoS': 5499,
    'DoS GoldenEye': 5499,
    'FTP-Patator': 5499,
    'SSH-Patator':5499,
    'DoS slowloris': 5499,
    'DoS Slowhttptest': 5499,
     'Bot': 1966

}
filtered_df = pd.DataFrame()
for label, count in expected_counts.items():
    if label in df[' Label'].values:
        label_data = df[df[' Label'] == label].sample(n=count, random_state=42, replace=False if count <= len(df[df[' Label'] == label]) else True)
        filtered_df = pd.concat([filtered_df, label_data], axis=0)
df = filtered_df.reset_index(drop=True)
print(f"Filtered dataset shape: {df.shape}")
print(f"Filtered label counts:\n{df[' Label'].value_counts()}")
```

### cell 8 `code` — # Step 2: Separate known and unknown samples

```python
# Step 2: Separate known and unknown samples
known_df = df[df['Label'] != 'Unknown'].copy()
unknown_df = df[df['Label'] == 'Unknown'].copy()
print(f"Known samples: {known_df.shape[0]}")
print(f"Unknown samples: {unknown_df.shape[0]}")
```

### cell 9 `code` — # Step 3: Basic Preprocessing

```python
# Step 3: Basic Preprocessing
# Handle NaN/infinity for both known and unknown
# Fit on known data only
known_df.replace([np.inf, -np.inf], np.nan, inplace=True)
unknown_df.replace([np.inf, -np.inf], np.nan, inplace=True)

for col in known_df.columns:
    if col != 'Label' and col != 'label_encoded':
        if known_df[col].isna().sum() > 0:
            mean_value = known_df[col].mean()  # Compute mean on known data only
            known_df[col].fillna(mean_value, inplace=True)
            unknown_df[col].fillna(mean_value, inplace=True)  # Apply to unknown data
            print(f"Filled NaN in column '{col}' with mean {mean_value:.4f} (computed from known data)")

print(f"After handling NaN (Known): {known_df.shape[0]} samples, NaN count: {known_df.isna().sum().sum()}")
print(f"After handling NaN (Unknown): {unknown_df.shape[0]} samples, NaN count: {unknown_df.isna().sum().sum()}")

# Verify 'Label' column
if 'Label' not in known_df.columns or 'Label' not in unknown_df.columns:
    raise ValueError(f"Column 'Label' not found. Available (Known): {known_df.columns.tolist()}, (Unknown): {unknown_df.columns.tolist()}")
```

### cell 10 `code` — # Step 4: Remove zero-variance columns (fit on known data only)

```python
# Step 4: Remove zero-variance columns (fit on known data only)
# Fitting on known data ensures 'Unknown' data doesn't influence feature selection
X_known = known_df.drop(['Label', 'label_encoded'], axis=1, errors='ignore')
print(f"Initial features (Known): {X_known.shape[1]} columns: {X_known.columns.tolist()}")
selector = VarianceThreshold(threshold=0)
X_known_selected = selector.fit_transform(X_known)
selected_columns = X_known.columns[selector.get_support()].tolist()
print(f"Columns after zero-variance filter: {len(selected_columns)} columns: {selected_columns}")

# Apply the same columns to unknown data
X_unknown = unknown_df.drop(['Label', 'label_encoded'], axis=1, errors='ignore')[selected_columns]

# Drop non-informative columns
non_informative_cols = ['Fwd URG Flags', 'Fwd Header Length.1']
non_informative_cols = [col for col in non_informative_cols if col in selected_columns]
if non_informative_cols:
    selected_columns = [col for col in selected_columns if col not in non_informative_cols]
    print(f"Dropped non-informative columns: {non_informative_cols}")

# Update X_known and X_unknown
X_known = X_known[selected_columns]
X_unknown = X_unknown[selected_columns]
print(f"Final selected columns: {len(selected_columns)} columns: {selected_columns}")
```

### cell 11 `code` — # Step 5: Normalize features (fit on known data only, apply to both)

```python
# Step 5: Normalize features (fit on known data only, apply to both)
# Fitting on known data ensures 'Unknown' data remains out-of-distribution
skewed_cols = ['Flow Duration', 'Total Fwd Packets', 'Total Backward Packets', 'Fwd IAT Total',
               'Bwd IAT Total', 'Fwd Packets/s', 'Bwd Packets/s', 'Fwd IAT Max',
               'Bwd IAT Max', 'Max Packet Length']
skewed_cols = [col for col in skewed_cols if col in X_known.columns]
if skewed_cols:
    min_max_scaler = MinMaxScaler()
    X_known[skewed_cols] = min_max_scaler.fit_transform(X_known[skewed_cols])  # Fit on known
    X_unknown[skewed_cols] = min_max_scaler.transform(X_unknown[skewed_cols])  # Apply to unknown
    print(f"Applied MinMaxScaler to: {skewed_cols}")

standard_cols = [col for col in X_known.columns if col not in skewed_cols]
if standard_cols:
    standard_scaler = StandardScaler()
    X_known[standard_cols] = standard_scaler.fit_transform(X_known[standard_cols])  # Fit on known
    X_unknown[standard_cols] = standard_scaler.transform(X_unknown[standard_cols])  # Apply to unknown
    print(f"Applied StandardScaler to: {standard_cols}")

# Clip outliers (fit on known data only, apply to both)
# Ensures 'Unknown' data doesn't influence clipping bounds
for col in X_known.columns:
    lower, upper = X_known[col].quantile([0.01, 0.99])
    X_known[col] = X_known[col].clip(lower=lower, upper=upper)
    X_unknown[col] = X_unknown[col].clip(lower=lower, upper=upper)
    print(f"Clipped column '{col}' to [{lower:.4f}, {upper:.4f}] (computed from known data)")

```

### cell 12 `code` — # Step 6: Reorder labels (define all classes upfront)

```python
# Step 6: Reorder labels (define all classes upfront)
all_labels = ['BENIGN', 'DDoS', 'DoS GoldenEye', 'DoS Hulk', 'DoS Slowhttptest',
              'DoS slowloris', 'FTP-Patator', 'PortScan', 'SSH-Patator' ,'Bot','Unknown']
le = LabelEncoder()
le.classes_ = np.array(all_labels)  # Set all classes explicitly

# Encode labels
known_df['label_encoded'] = le.transform(known_df['Label'])
unknown_df['label_encoded'] = le.transform(unknown_df['Label'])
```

### cell 13 `code` — # Step 1: Split known data into train/test

```python
# Step 1: Split known data into train/test
X_train, X_test_known, y_train, y_test_known = train_test_split(
    X_known,
    known_df['label_encoded'],
    test_size=0.2,
    stratify=known_df['label_encoded'],
    random_state=42
)

# Step 2: Combine known and unknown test data
X_test = pd.concat([X_test_known, X_unknown], axis=0)
y_test = pd.concat([
    pd.Series(y_test_known, index=X_test_known.index),
    pd.Series(unknown_df['label_encoded'], index=X_unknown.index)
], axis=0)

# Step 3: Ensure labels are 1D arrays
y_train = np.squeeze(y_train.values)
y_test = np.squeeze(y_test.values)

# Step 4: One-hot encoding
num_classes_train = len(np.unique(y_train))   # Only known classes
num_classes_total = len(le.classes_)          # All classes (including 'Unknown')

y_train_cat = tf.keras.utils.to_categorical(y_train, num_classes=num_classes_train)
y_test_cat = tf.keras.utils.to_categorical(y_test, num_classes=num_classes_total)

# Step 5: Print info
print(f"Training set size: {X_train.shape[0]} samples, {X_train.shape[1]} features")
print(f"Test set size (Known): {X_test_known.shape[0]} samples")
print(f"Test set size (Unknown): {X_unknown.shape[0]} samples")
print(f"Test set size (Total): {X_test.shape[0]} samples, {X_test.shape[1]} features")
print(f"y_train shape: {y_train.shape}")
print(f"y_test shape: {y_test.shape}")
print(f"y_train_cat shape: {y_train_cat.shape}")
print(f"y_test_cat shape: {y_test_cat.shape}")

# Step 6: Optional check for data leakage
train_set = set(X_train.index)
test_set = set(X_test.index)
overlap = train_set.intersection(test_set)
print(f"Number of overlapping samples between train and test: {len(overlap)}")
```

### cell 14 `code` — # Step 8: Reshape for CNN

```python
# Step 8: Reshape for CNN
X_train_cnn = X_train.values.reshape(X_train.shape[0], X_train.shape[1], 1)
X_test_cnn = X_test.values.reshape(X_test.shape[0], X_test.shape[1], 1)
print(f"X_train_cnn shape: {X_train_cnn.shape}")
print(f"X_test_cnn shape: {X_test_cnn.shape}")

# Debug: Check for NaN or Inf in X_train_cnn and X_test_cnn
print(f"X_train_cnn NaN/Inf count: {(X_train_cnn == np.inf).sum() + (X_train_cnn == -np.inf).sum() + np.isnan(X_train_cnn).sum()}")
print(f"X_test_cnn NaN/Inf count: {(X_test_cnn == np.inf).sum() + (X_test_cnn == -np.inf).sum() + np.isnan(X_test_cnn).sum()}")
```

### cell 15 `code` — # Step 9: Compute class weights (known classes only)

```python
# Step 9: Compute class weights (known classes only)
class_weights = compute_class_weight('balanced', classes=np.arange(10), y=y_train)  # Only 10 known classes
class_weights = dict(enumerate(class_weights))
print(f"Computed class weights: {class_weights}")
```

### cell 16 `code` — # Step 0: Before model definition

```python
# Step 0: Before model definition
num_classes_train = y_train_cat.shape[1]
input_shape = (X_train_cnn.shape[1], 1)

print(num_classes_train)
```

### cell 17 `code` — # Step 0: Before model definition

```python
# Step 0: Before model definition
num_classes_train = y_train_cat.shape[1]
input_shape = (X_train_cnn.shape[1], 1)

# Step 10: CNN with reduced capacity
inputs = Input(shape=input_shape)
x = Conv1D(filters=8, kernel_size=3, padding='same', kernel_regularizer=l2(0.005))(inputs)
x = ReLU()(x)
x = BatchNormalization()(x)
x = MaxPooling1D(pool_size=2)(x)

x = Conv1D(filters=24, kernel_size=3, padding='same', kernel_regularizer=l2(0.005))(x)
x = ReLU()(x)
x = BatchNormalization()(x)
x = MaxPooling1D(pool_size=2)(x)

x = Conv1D(filters=32, kernel_size=3, padding='same', kernel_regularizer=l2(0.005))(x)
x = ReLU()(x)
x = BatchNormalization()(x)
x = MaxPooling1D(pool_size=2)(x)

x = GlobalAveragePooling1D()(x)
x = Dense(48, kernel_regularizer=l2(0.005))(x)
x = ReLU()(x)
x = Dropout(0.5)(x)

# Only 9 known classes used for training
outputs = Dense(num_classes_train, activation='softmax')(x)

model = Model(inputs=inputs, outputs=outputs)

# Custom loss function
def custom_loss_with_entropy(y_true, y_pred):
    cross_entropy = tf.keras.losses.categorical_crossentropy(y_true, y_pred)
    epsilon = 1e-7
    y_pred = tf.clip_by_value(y_pred, epsilon, 1 - epsilon)
    entropy = -tf.reduce_sum(y_pred * tf.math.log(y_pred), axis=-1)
    return cross_entropy + 1.0 * entropy

================================================================
# FILE: docs/experiments/legacy_inventory_summary.md
================================================================

# Legacy PADataset Experiment Inventory

Generated from local ignored artifacts. This file is safe to commit because it contains metadata only, not checkpoints or raw data.

## Counts

- Run directories inventoried: 203
- Checkpoints inventoried: 617
- Generated tables inventoried: 16

## Result roots

- `results_pa_baseline`: 13
- `results_pa_cache_sweep`: 12
- `results_pa_confmanifold_coarse`: 56
- `results_pa_confmanifold_refined`: 64
- `results_pa_finalist`: 2
- `results_pa_followup`: 4
- `results_pa_osr_bank`: 48
- `results_pa_ota_btzb`: 2
- `results_pa_smoke`: 2

## Family tags observed

- `smoke_ent005_lr2e4`: 2

## Source profiles observed

- `('digital', 'pilot_noisy_torch', None, None)`: 113
- `('ota', 'ota_core_high_run01', 'ota_core_high_run01', 'high_run01')`: 4
- `(None, None, None, None)`: 86

## Next reconstruction task

Use `legacy_run_inventory.csv`, `legacy_checkpoint_inventory.csv`, and old generated leaderboard CSVs to define:

1. original digital-noisy source profile
2. old backbone family grid
3. old PA open-set folds
4. OSR evaluation settings
5. minimal reruns required for missing or ambiguous artifacts

================================================================
# FILE: docs/experiments/legacy_digital_reconstruction.md
================================================================

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

================================================================
# FILE: docs/experiments/dqn_review/dqn_archive_concat_for_review.md
================================================================


================================================================
# FILE: docs/experiments/legacy_notebook_inventory.md
================================================================

# Legacy notebook inventory

## `archive/model/PADiscriminate.ipynb`

- size_kb: `5.8`
- n_cells: `6`
- keyword_hits: `open set, OSR, VarMax, unknown`

## `archive/model/PAEvaluate.ipynb`

- size_kb: `120.2`
- n_cells: `32`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb`

- size_kb: `522.4`
- n_cells: `37`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `legacy/notebooks/non_pa/DQN_CICIDS_Part_v2.ipynb`

- size_kb: `32.6`
- n_cells: `13`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `legacy/notebooks/non_pa/DQN_UNSW.ipynb`

- size_kb: `85.1`
- n_cells: `16`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `legacy/notebooks/non_pa/cnn_unsw.ipynb`

- size_kb: `373.4`
- n_cells: `23`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `legacy/notebooks/pa_cnn_osr/PADiscriminate.ipynb`

- size_kb: `5218.4`
- n_cells: `27`
- keyword_hits: `DQN, open set, OSR, VarMax, entropy, unknown`

## `legacy/notebooks/pa_cnn_osr/PAEvaluate.ipynb`

- size_kb: `327.1`
- n_cells: `59`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `legacy/notebooks/pa_cnn_osr/PAValidate.ipynb`

- size_kb: `3.1`
- n_cells: `4`
- keyword_hits: `none`

## `legacy/txrx_debug/splice.ipynb`

- size_kb: `4.5`
- n_cells: `7`
- keyword_hits: `VarMax`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/CNN_CICIDS_runtime.ipynb`

- size_kb: `522.4`
- n_cells: `37`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/DQN_CICIDS_Part_v2.ipynb`

- size_kb: `32.6`
- n_cells: `13`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/DQN_UNSW.ipynb`

- size_kb: `85.1`
- n_cells: `16`
- keyword_hits: `DQN, epsilon, replay, CNN, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/PADiscriminate.ipynb`

- size_kb: `5218.4`
- n_cells: `27`
- keyword_hits: `DQN, open set, OSR, VarMax, entropy, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/PAEvaluate.ipynb`

- size_kb: `327.1`
- n_cells: `59`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/PAValidate.ipynb`

- size_kb: `3.1`
- n_cells: `4`
- keyword_hits: `none`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/archive/model/PADiscriminate.ipynb`

- size_kb: `5.8`
- n_cells: `6`
- keyword_hits: `open set, OSR, VarMax, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/archive/model/PAEvaluate.ipynb`

- size_kb: `120.2`
- n_cells: `32`
- keyword_hits: `DQN, epsilon, OSR, VarMax, energy, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/cnn_unsw.ipynb`

- size_kb: `373.4`
- n_cells: `23`
- keyword_hits: `epsilon, CNN, Conv1d, entropy, p1_p2, unknown`

## `local_artifacts/handoffs/PADataset_training_handoff_20260512_035606/repo_code/txrx/splice.ipynb`

- size_kb: `4.5`
- n_cells: `7`
- keyword_hits: `VarMax`

================================================================
# FILE: docs/experiments/shreyash_dqn_backbone_recovery.md
================================================================

# Shreyash DQN/CNN backbone recovery

This document extracts implementation evidence from the four legacy non-PA notebooks associated with Shreyash's CICIDS/UNSW CNN+DQN workflow.

The purpose is **not** to make this workflow mandatory for the final OTA matrix yet. The purpose is to preserve the recipe so it can later be ported into a clean PA model-family track.

## Scope

- `legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb`
- `legacy/notebooks/non_pa/DQN_CICIDS_Part_v2.ipynb`
- `legacy/notebooks/non_pa/DQN_UNSW.ipynb`
- `legacy/notebooks/non_pa/cnn_unsw.ipynb`

## Recovery questions

1. What CNN/backbone architecture was used?
2. What preprocessing/input representation was assumed?
3. What training objective, optimizer, epochs, batch size, and regularization were used?
4. What DQN state/action/reward structure was used?
5. What parts already exist in `dqn_osr.py`?
6. What still needs to be ported into the final PA runner?

---

## `legacy/notebooks/non_pa/CNN_CICIDS_runtime.ipynb`

- cells: `37`
- size_kb: `522.4`

- signal_cells: `28`

### cell 2 `code` — import matplotlib.pyplot as plt

```python
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from sklearn.feature_selection import VarianceThreshold
from sklearn.metrics import f1_score, accuracy_score
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Conv1D, MaxPooling1D, GlobalAveragePooling1D, Dense, Dropout, Input, ReLU, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import tensorflow as tf
```

### cell 3 `code` — #Load dataset

```python
#Load dataset
df = pd.read_csv('clean_df.csv')  # Ensure this file path is correct

# Step 1: Combine specified classes into 'Unknown'
unknown_classes = [
     'Web Attack – Brute Force', 'Web Attack – XSS',
    'Infiltration', 'Web Attack – SQL Injection', 'Heartbleed'
]
df[' Label'] = df[' Label'].apply(lambda x: 'Unknown' if x in unknown_classes else x)

# Verify and filter dataset size
print(f"Initial dataset shape: {df.shape}")
print(f"Label counts:\n{df[' Label'].value_counts()}")

# Define sample sizes
expected_counts = {
    'BENIGN': 5499,
    'Unknown': 2227,  # Bot (1,966) + Brute Force (1,507) + XSS (652) + Infiltration (36) + SQL Injection (21) + Heartbleed (11)
    'DoS Hulk': 5499,
    'PortScan': 5499,
    'DDoS': 5499,
    'DoS GoldenEye': 5499,
    'FTP-Patator': 5499,
    'SSH-Patator':5499,
    'DoS slowloris': 5499,
    'DoS Slowhttptest': 5499,
     'Bot': 1966

}
filtered_df = pd.DataFrame()
for label, count in expected_counts.items():
    if label in df[' Label'].values:
        label_data = df[df[' Label'] == label].sample(n=count, random_state=42, replace=False if count <= len(df[df[' Label'] == label]) else True)
        filtered_df = pd.concat([filtered_df, label_data], axis=0)
df = filtered_df.reset_index(drop=True)
print(f"Filtered dataset shape: {df.shape}")
print(f"Filtered label counts:\n{df[' Label'].value_counts()}")
```

### cell 8 `code` — # Step 2: Separate known and unknown samples

```python
# Step 2: Separate known and unknown samples
known_df = df[df['Label'] != 'Unknown'].copy()
unknown_df = df[df['Label'] == 'Unknown'].copy()
print(f"Known samples: {known_df.shape[0]}")
print(f"Unknown samples: {unknown_df.shape[0]}")
```

### cell 9 `code` — # Step 3: Basic Preprocessing

```python
# Step 3: Basic Preprocessing
# Handle NaN/infinity for both known and unknown
# Fit on known data only
known_df.replace([np.inf, -np.inf], np.nan, inplace=True)
unknown_df.replace([np.inf, -np.inf], np.nan, inplace=True)

for col in known_df.columns:
    if col != 'Label' and col != 'label_encoded':
        if known_df[col].isna().sum() > 0:
            mean_value = known_df[col].mean()  # Compute mean on known data only
            known_df[col].fillna(mean_value, inplace=True)
            unknown_df[col].fillna(mean_value, inplace=True)  # Apply to unknown data
            print(f"Filled NaN in column '{col}' with mean {mean_value:.4f} (computed from known data)")

print(f"After handling NaN (Known): {known_df.shape[0]} samples, NaN count: {known_df.isna().sum().sum()}")
print(f"After handling NaN (Unknown): {unknown_df.shape[0]} samples, NaN count: {unknown_df.isna().sum().sum()}")

# Verify 'Label' column
if 'Label' not in known_df.columns or 'Label' not in unknown_df.columns:
    raise ValueError(f"Column 'Label' not found. Available (Known): {known_df.columns.tolist()}, (Unknown): {unknown_df.columns.tolist()}")
```

### cell 10 `code` — # Step 4: Remove zero-variance columns (fit on known data only)

```python
# Step 4: Remove zero-variance columns (fit on known data only)
# Fitting on known data ensures 'Unknown' data doesn't influence feature selection
X_known = known_df.drop(['Label', 'label_encoded'], axis=1, errors='ignore')
print(f"Initial features (Known): {X_known.shape[1]} columns: {X_known.columns.tolist()}")
selector = VarianceThreshold(threshold=0)
X_known_selected = selector.fit_transform(X_known)
selected_columns = X_known.columns[selector.get_support()].tolist()
print(f"Columns after zero-variance filter: {len(selected_columns)} columns: {selected_columns}")

# Apply the same columns to unknown data
X_unknown = unknown_df.drop(['Label', 'label_encoded'], axis=1, errors='ignore')[selected_columns]

# Drop non-informative columns
non_informative_cols = ['Fwd URG Flags', 'Fwd Header Length.1']
non_informative_cols = [col for col in non_informative_cols if col in selected_columns]
if non_informative_cols:
    selected_columns = [col for col in selected_columns if col not in non_informative_cols]
    print(f"Dropped non-informative columns: {non_informative_cols}")

# Update X_known and X_unknown
X_known = X_known[selected_columns]
X_unknown = X_unknown[selected_columns]
print(f"Final selected columns: {len(selected_columns)} columns: {selected_columns}")
```

### cell 11 `code` — # Step 5: Normalize features (fit on known data only, apply to both)

```python
# Step 5: Normalize features (fit on known data only, apply to both)
# Fitting on known data ensures 'Unknown' data remains out-of-distribution
skewed_cols = ['Flow Duration', 'Total Fwd Packets', 'Total Backward Packets', 'Fwd IAT Total',
               'Bwd IAT Total', 'Fwd Packets/s', 'Bwd Packets/s', 'Fwd IAT Max',
               'Bwd IAT Max', 'Max Packet Length']
skewed_cols = [col for col in skewed_cols if col in X_known.columns]
if skewed_cols:
    min_max_scaler = MinMaxScaler()
    X_known[skewed_cols] = min_max_scaler.fit_transform(X_known[skewed_cols])  # Fit on known
    X_unknown[skewed_cols] = min_max_scaler.transform(X_unknown[skewed_cols])  # Apply to unknown
    print(f"Applied MinMaxScaler to: {skewed_cols}")

standard_cols = [col for col in X_known.columns if col not in skewed_cols]
if standard_cols:
    standard_scaler = StandardScaler()
    X_known[standard_cols] = standard_scaler.fit_transform(X_known[standard_cols])  # Fit on known
    X_unknown[standard_cols] = standard_scaler.transform(X_unknown[standard_cols])  # Apply to unknown
    print(f"Applied StandardScaler to: {standard_cols}")

# Clip outliers (fit on known data only, apply to both)
# Ensures 'Unknown' data doesn't influence clipping bounds
for col in X_known.columns:
    lower, upper = X_known[col].quantile([0.01, 0.99])
    X_known[col] = X_known[col].clip(lower=lower, upper=upper)
    X_unknown[col] = X_unknown[col].clip(lower=lower, upper=upper)
    print(f"Clipped column '{col}' to [{lower:.4f}, {upper:.4f}] (computed from known data)")

```

### cell 12 `code` — # Step 6: Reorder labels (define all classes upfront)

```python
# Step 6: Reorder labels (define all classes upfront)

================================================================
# FILE: docs/experiments/legacy_prior_chat_experiment_knowledge.md
================================================================

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
