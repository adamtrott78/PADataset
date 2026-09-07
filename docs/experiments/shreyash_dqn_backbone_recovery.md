> **Historical evidence.** This record describes an earlier run, design iteration or recovery. Its next steps, paths, scores and settings are historical observations, not current instructions. Current workflow: [owning context](../../experiments/CONTEXT.md).

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

model.compile(
    optimizer=Adam(learning_rate=0.00001, clipnorm=1.0),
    loss=custom_loss_with_entropy,
    metrics=['accuracy']
)

# Debug check
initial_loss = model.evaluate(X_train_cnn, y_train_cat, batch_size=1000, verbose=0)[0]
print(f"Initial loss: {initial_loss}")

```

### cell 18 `code` — # Step 11: Train the model

```python
# Step 11: Train the model
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7)
history = model.fit(
    X_train_cnn, y_train_cat,
    epochs=500,
    batch_size=500,
    validation_split=0.2,
    class_weight=class_weights,
    callbacks=[early_stopping, lr_scheduler],
    verbose=1
)
```

### cell 19 `code` — print("Train classes (unique):", np.unique(y_train))

```python
print("Train classes (unique):", np.unique(y_train))
print("Train one-hot shape:", y_train_cat.shape)
print("Total label classes (including unknown):", len(le.classes_))

```

### cell 20 `code` — # Step 12: Training validation metrics

```python
# Step 12: Training validation metrics
val_indices = int(0.8 * len(X_train_cnn))
X_val_cnn = X_train_cnn[val_indices:]
y_val_cat = y_train_cat[val_indices:]
val_pred = model.predict(X_val_cnn)
val_pred_classes = np.argmax(val_pred, axis=1)
val_true_classes = np.argmax(y_val_cat, axis=1)
val_f1 = f1_score(val_true_classes, val_pred_classes, average='weighted')
val_acc = accuracy_score(val_true_classes, val_pred_classes)
print(f"Training validation F1 score: {val_f1:.4f}")
print(f"Training validation accuracy: {val_acc:.4f}")
```

### cell 21 `code` — # Step 13: Test metrics (known classes only)

```python
# Step 13: Test metrics (known classes only)
known_mask = y_test != le.transform(['Unknown'])[0]
X_test_known = X_test_cnn[known_mask]
y_test_known_cat = y_test_cat[known_mask]
test_pred_known = model.predict(X_test_known)
test_pred_classes = np.argmax(test_pred_known, axis=1)
test_true_classes = np.argmax(y_test_known_cat, axis=1)
test_acc = accuracy_score(test_true_classes, test_pred_classes)
test_f1 = f1_score(test_true_classes, test_pred_classes, average='weighted')
print(f"Test accuracy (Known classes only): {test_acc:.4f}")
print(f"Test F1 score (Known classes only): {test_f1:.4f}")
```

### cell 22 `code` — # Step 14: Predict on test set

```python
# Step 14: Predict on test set
test_pred = model.predict(X_test_cnn, batch_size=512, verbose=1)  # shape: (17819, 9)

# Calculate softmax metrics
max_probs = np.max(test_pred, axis=1)
sorted_probs = np.sort(test_pred, axis=1)
p1_minus_p2 = sorted_probs[:, -1] - sorted_probs[:, -2]

# Apply known/unknown mask
known_probs = max_probs[known_mask]
unknown_probs = max_probs[~known_mask]
known_p1_p2_diff = p1_minus_p2[known_mask]
unknown_p1_p2_diff = p1_minus_p2[~known_mask]

# Print metrics
print("\n--- Softmax Confidence Results ---")
print(f"Known samples: {known_mask.sum()}, Unknown samples: {(~known_mask).sum()}")
print(f"Known p_max (p1): {np.mean(known_probs):.4f} ± {np.std(known_probs):.4f}")
print(f"Unknown p_max (p1): {np.mean(unknown_probs):.4f} ± {np.std(unknown_probs):.4f}")
print(f"Known p1-p2 diff: {np.mean(known_p1_p2_diff):.4f} ± {np.std(known_p1_p2_diff):.4f}")
print(f"Unknown p1-p2 diff: {np.mean(unknown_p1_p2_diff):.4f} ± {np.std(unknown_p1_p2_diff):.4f}")

# Sanity check: Output size must match test labels
print("\n--- Sanity Check ---")
print(f"Predicted probability shape: {test_pred.shape}")
print(f"y_test shape: {y_test.shape}")
assert test_pred.shape[0] == y_test.shape[0], "Mismatch in number of test samples!"



print("\n Results saved: 'test_predictions_softmax.npy', 'test_p1_max_probs.npy', 'test_p1_minus_p2.npy', 'test_known_mask.npy'")

```

### cell 23 `code` — # Step 17: Debug overfitting

```python
# Step 17: Debug overfitting
train_pred = model.predict(X_train_cnn, batch_size=1000)
train_acc = accuracy_score(np.argmax(y_train_cat, axis=1), np.argmax(train_pred, axis=1))
print(f"Training accuracy: {train_acc:.4f}")
```

### cell 24 `code` — # Step 1: Get CNN predictions

```python
# Step 1: Get CNN predictions
cnn_probs = model.predict(X_test_cnn)
cnn_preds = np.argmax(cnn_probs, axis=1)
p_max = np.max(cnn_probs, axis=1)

# Step 2: Separate based on true labels
true_labels = y_test

known_mask = true_labels != 10
unknown_mask = true_labels == 10

p_max_known = p_max[known_mask]
p_max_unknown = p_max[unknown_mask]
# Step 4: Print Stats
print(f"True known samples in test: {known_mask.sum()}")
print(f"True unknown samples in test: {unknown_mask.sum()}")

print(f"\n--- p_max Distribution ---")
print(f"Known class p_max: {p_max_known.mean():.4f} ± {p_max_known.std():.4f}")
print(f"Unknown class p_max: {p_max_unknown.mean():.4f} ± {p_max_unknown.std():.4f}")

# Step 5: Plot Distributions
plt.figure(figsize=(10,5))
plt.hist(p_max_known, bins=50, alpha=0.6, label='Known', color='blue')
plt.hist(p_max_unknown, bins=50, alpha=0.6, label='Unknown', color='red')
plt.title("Softmax p_max Distribution (CNN 0-8 output)")
plt.xlabel("p_max")
plt.ylabel("Frequency")
plt.legend()
plt.grid(True)
plt.show()
```

### cell 25 `code` — # Step 5: Plot Distributions

```python
# Step 5: Plot Distributions
plt.figure(figsize=(12,6))

# Increase histogram text size
plt.hist(p_max_known, bins=40, alpha=0.6, label='Known', color='blue')
plt.hist(p_max_unknown, bins=40, alpha=0.6, label='Unknown', color='red')

# Title and axis labels with bigger font
plt.title("Softmax p_max Distribution (CNN 0-8 output)", fontsize=18, fontweight='bold')
plt.xlabel("p_max", fontsize=30)
plt.ylabel("Frequency", fontsize=30)

# Bigger ticks (scale numbers on axes)
plt.xticks(fontsize=25)
plt.yticks(fontsize=25)

# Legend with bigger font
plt.legend(fontsize=14)

# Grid
plt.grid(True, linestyle="--", alpha=0.7)

plt.show()

```

### cell 26 `code` — # Step 1: Get softmax predictions from CNN

```python
# Step 1: Get softmax predictions from CNN
cnn_probs = model.predict(X_test_cnn)  # shape
true_labels = y_test                   # shape

# Step 2: Save softmax outputs and true labels as npy
np.save("cnn_softmax_outputs.npy", cnn_probs)
np.save("true_labels.npy", true_labels)

print("Saved 'cnn_softmax_outputs.npy' (shape:", cnn_probs.shape, ")")
print("Saved 'true_labels.npy' (shape:", true_labels.shape, ")")

```

### cell 27 `code` — # Load the saved softmax outputs and true labels

```python
# Load the saved softmax outputs and true labels
probs = np.load("cnn_softmax_outputs.npy")
true_labels = np.load("true_labels.npy")

# Compute p1 - p2 for each sample
sorted_probs = np.sort(probs, axis=1)
p1_minus_p2 = sorted_probs[:, -1] - sorted_probs[:, -2]

# Mask for known and unknown based on true labels
known_mask = true_labels != 10
unknown_mask = true_labels == 10

# Split p1-p2 for known and unknown
known_p1_p2_diff = p1_minus_p2[known_mask]
unknown_p1_p2_diff = p1_minus_p2[unknown_mask]

# Print summary statistics
print(f"Known p1-p2: mean={np.mean(known_p1_p2_diff):.4f}, std={np.std(known_p1_p2_diff):.4f}")
print(f"Unknown p1-p2: mean={np.mean(unknown_p1_p2_diff):.4f}, std={np.std(unknown_p1_p2_diff):.4f}")

# Plot distributions
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.hist(known_p1_p2_diff, bins=50, color='blue', alpha=0.7)
plt.title("Known Samples: p1 - p2 Distribution")
plt.xlabel("p1 - p2")
plt.ylabel("Frequency")
plt.grid(True)

plt.subplot(1, 2, 2)
plt.hist(unknown_p1_p2_diff, bins=50, color='orange', alpha=0.7)
plt.title("Unknown Samples: p1 - p2 Distribution")
plt.xlabel("p1 - p2")
plt.ylabel("Frequency")
plt.grid(True)

plt.tight_layout()
plt.show()

```

### cell 28 `code` — # Plot distributions with larger fonts

```python
# Plot distributions with larger fonts
plt.figure(figsize=(14, 6))

plt.subplot(1, 2, 1)
plt.hist(known_p1_p2_diff, bins=40, color='blue', alpha=0.7)
plt.title("Known Samples: p1 - p2 Distribution", fontsize=18, fontweight='bold')
plt.xlabel("p1 - p2", fontsize=30)
plt.ylabel("Frequency", fontsize=30)
plt.xticks(fontsize=25)
plt.yticks(fontsize=25)
plt.grid(True, linestyle="--", alpha=0.7)

plt.subplot(1, 2, 2)
plt.hist(unknown_p1_p2_diff, bins=40, color='orange', alpha=0.7)
plt.title("Unknown Samples: p1 - p2 Distribution", fontsize=18, fontweight='bold')
plt.xlabel("p1 - p2", fontsize=30)
plt.ylabel("Frequency", fontsize=30)
plt.xticks(fontsize=25)
plt.yticks(fontsize=25)
plt.grid(True, linestyle="--", alpha=0.7)

plt.tight_layout()
plt.show()

```

### cell 32 `code` — # Step 1: Get predictionss

```python
from sklearn.metrics import roc_auc_score, roc_curve, auc
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt
from itertools import cycle


# Step 1: Get predictionss
y_score = model.predict(X_test_known)
y_true_bin = y_test_known_cat

n_classes = y_score.shape[1]
fpr = dict()
tpr = dict()
roc_auc = dict()

# Step 2: Compute ROC curve and ROC area for each class
for i in range(n_classes):
    fpr[i], tpr[i], _ = roc_curve(y_true_bin[:, i], y_score[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

# Step 3: Plot all ROC curves
colors = cycle(['aqua', 'darkorange', 'cornflowerblue', 'red', 'green', 'purple', 'olive', 'magenta', 'brown'])
plt.figure(figsize=(10, 8))
for i, color in zip(range(n_classes), colors):
    class_name = le.inverse_transform([i])[0]  # if using LabelEncoder
    plt.plot(fpr[i], tpr[i], color=color, lw=2,
             label=f'Class {class_name} (AUC = {roc_auc[i]:0.2f})')

plt.plot([0, 1], [0, 1], 'k--', lw=1)
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Multi-Class ROC Curve (Known Classes)')
plt.legend(loc="lower right")
plt.grid(True)
plt.show()

```

### cell 33 `code` — # Step 13: Test metrics (known classes only)

```python
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    classification_report,
    confusion_matrix
)
import seaborn as sns
import matplotlib.pyplot as plt

# Step 13: Test metrics (known classes only)
known_mask = y_test != le.transform(['Unknown'])[0]
X_test_known = X_test_cnn[known_mask]
y_test_known_cat = y_test_cat[known_mask]

# Predictions
test_pred_known = model.predict(X_test_known)
test_pred_classes = np.argmax(test_pred_known, axis=1)
test_true_classes = np.argmax(y_test_known_cat, axis=1)

# Metrics
test_acc = accuracy_score(test_true_classes, test_pred_classes)
test_f1 = f1_score(test_true_classes, test_pred_classes, average='weighted')
test_precision = precision_score(test_true_classes, test_pred_classes, average='weighted', zero_division=0)
test_recall = recall_score(test_true_classes, test_pred_classes, average='weighted')

# Output metrics
print(f"Test Accuracy (Known classes only): {test_acc:.4f}")
print(f"Test F1 Score (Known classes only): {test_f1:.4f}")
print(f"Test Precision (Known classes only): {test_precision:.4f}")
print(f"Test Recall (Known classes only): {test_recall:.4f}")

# Classification report
target_names = le.inverse_transform(np.unique(test_true_classes))
print("\nClassification Report:")
print(classification_report(test_true_classes, test_pred_classes, target_names=target_names))

# Optional: Confusion matrix
cm = confusion_matrix(test_true_classes, test_pred_classes)
plt.figure(figsize=(10, 8))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=target_names, yticklabels=target_names)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix (Known Classes)')
plt.show()

```

### cell 34 `code` — # Confusion matrix with improved readability

```python
# Confusion matrix with improved readability
cm = confusion_matrix(test_true_classes, test_pred_classes)

plt.figure(figsize=(12, 10))
sns.heatmap(
    cm,
    annot=True,
    fmt='d',
    cmap='Blues',
    xticklabels=target_names,
    yticklabels=target_names,
    annot_kws={"size": 14}   # increase numbers inside the boxes
)

# Bigger labels and title
plt.xlabel('Predicted', fontsize=16)
plt.ylabel('True', fontsize=16)
plt.title('Confusion Matrix (Known Classes)', fontsize=18, fontweight='bold')

# Tick labels bigger
plt.xticks(fontsize=14, rotation=45, ha="right")
plt.yticks(fontsize=14, rotation=0)

plt.tight_layout()
plt.show()

```

### cell 35 `code` — # Ensure numpy array

```python
import time
import numpy as np

# Ensure numpy array
if hasattr(X_test, "values"):
    X_test_array = X_test.values
else:
    X_test_array = np.array(X_test)

# Reshape if model expects (features, 1)
try:
    expected_shape = model.input_shape  # e.g., (None, 68, 1)
except:
    expected_shape = None

needs_reshape = False
if expected_shape and len(expected_shape) == 3 and expected_shape[-1] == 1:
    needs_reshape = True

batch_size = 64
n_samples = len(X_test_array)
n_batches = (n_samples + batch_size - 1) // batch_size

batch_times = []

for i in range(n_batches):
    batch = X_test_array[i*batch_size : (i+1)*batch_size]

    # If needed, reshape to (batch, features, 1)
    if needs_reshape:
        batch = batch.reshape(batch.shape[0], batch.shape[1], 1)

    start = time.time()
    _ = model.predict(batch, verbose=0)
    end = time.time()

    batch_times.append(end - start)

total_time = np.sum(batch_times)
avg_batch_time = total_time / n_batches
avg_sample_time = total_time / n_samples

print(f"Total inference time: {total_time:.4f} sec")
print(f"Average time per batch: {avg_batch_time:.6f} sec")
print(f"Average time per sample: {avg_sample_time*1000:.6f} ms")

```

### cell 36 `code` — #Model Review:

```python
#Model Review:

# 1. Close Train vs Validation Accuracy
#    - Training accuracy: ~96.4%
#    - Validation accuracy: ~97.18%
#    - Indicates stable learning and no overfitting.

# 2. Close Train vs Validation F1 Score
#    - Training F1 score: 0.9713
#    - Validation F1 score: 0.9685
#    - Suggests balanced class-wise performance across sets.

# 3. High Test Performance on Unseen Data
#    - Test accuracy: 0.9693
#    - Test F1 score: 0.9685
#    - Confirms generalization beyond the training data.

# 4. Validation Loss Lower Than Training Loss
#    - Training loss: ~0.61
#    - Validation loss: ~0.49
#    - Expected behavior due to dropout/batchnorm being inactive during validation.

# 5. ROC-AUC Curve Indicates Strong Class Separation
#    - AUC = 1.00 for all classes except BENIGN (0.98)
#    - Shows excellent model discrimination ability.

# 6. No Signs of Underfitting
#    - High training accuracy and F1 score
#    - Confirms the model has learned the data patterns effectively.

# 7. Loss Curves Have Converged
#    - Loss stabilizes in final epochs without increase
#  -  Suggests the model has reached a good learning plateau.

```

---

## `legacy/notebooks/non_pa/DQN_CICIDS_Part_v2.ipynb`

- cells: `13`
- size_kb: `32.6`

- signal_cells: `9`

### cell 0 `code` — import numpy as np

```python
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
import tensorflow as tf
from collections import deque
import random

```

### cell 4 `code` — # === Setup ===

```python
# === Setup ===
total_size = len(true_labels)
val_size = int(0.2 * total_size)  # 20% validation
all_indices = np.arange(total_size)

# Random shuffle for unbiased split
np.random.seed(42)  # for reproducibility
np.random.shuffle(all_indices)

# Split indices
val_indices = all_indices[:val_size]
remaining_indices = all_indices[val_size:]  # 80% test

# === Sanity Check ===
print("=== Set Sizes ===")
print(f"Validation Set: {len(val_indices)}")
print(f"Test Set:       {len(remaining_indices)}")

# Optional: check distribution of labels in each set
val_labels = true_labels[val_indices]
test_labels = true_labels[remaining_indices]

val_known = np.sum(val_labels != 10)
val_unknown = np.sum(val_labels == 10)

test_known = np.sum(test_labels != 10)
test_unknown = np.sum(test_labels == 10)

print("\n=== Label Distribution (for sanity, not used in split) ===")
print(f"Validation Known:   {val_known}")
print(f"Validation Unknown: {val_unknown}")
print(f"Test Known:         {test_known}")
print(f"Test Unknown:       {test_unknown}")

```

### cell 5 `code` — def compute_entropy(softmax_outputs):

```python
def compute_entropy(softmax_outputs):

    epsilon = 1e-12  # to avoid log(0)
    softmax_clipped = np.clip(softmax_outputs, epsilon, 1. - epsilon)
    entropy = -np.sum(softmax_clipped * np.log(softmax_clipped), axis=1)
    return entropy

# === Compute Entropy ===
val_softmax_outputs = softmax_outputs[val_indices]
test_softmax_outputs = softmax_outputs[remaining_indices]

val_entropy = compute_entropy(val_softmax_outputs)
test_entropy = compute_entropy(test_softmax_outputs)

# === Stats Check ===
print(f"Validation entropy stats - min: {val_entropy.min():.4f}, max: {val_entropy.max():.4f}, mean: {val_entropy.mean():.4f}")
print(f"Test entropy stats       - min: {test_entropy.min():.4f}, max: {test_entropy.max():.4f}, mean: {test_entropy.mean():.4f}")

```

### cell 6 `code` — def compute_entropy(softmax_probs):

```python
from scipy.stats import entropy

def compute_entropy(softmax_probs):

    epsilon = 1e-12
    softmax_clipped = np.clip(softmax_probs, epsilon, 1. - epsilon)
    return entropy(softmax_clipped.T)  # entropy across classes for each sample

# === Extract softmax outputs for validation set ===
val_softmax_outputs = softmax_outputs[val_indices]  # shape: (n_val_samples, n_classes)

# === Compute p1 (max confidence), p1 - p2, and entropy ===
val_p1 = np.max(val_softmax_outputs, axis=1)
sorted_preds = np.sort(val_softmax_outputs, axis=1)
val_p1_p2_diff = sorted_preds[:, -1] - sorted_preds[:, -2]
val_entropy = compute_entropy(val_softmax_outputs)

# === Define top/bottom 5% size ===
n_val = len(val_indices)
n_top_bottom = int(0.05 * n_val)

# === Get top 5% high-confidence based on p1 only ===
sorted_indices = np.argsort(val_p1)
low_conf_top_indices = sorted_indices[:n_top_bottom]        # bottom 5% → low confidence
high_conf_top_indices = sorted_indices[-n_top_bottom:]      # top 5% → high confidence

# === Create boolean masks (for excluding in training) ===
high_conf_mask = np.zeros(n_val, dtype=bool)
low_conf_mask = np.zeros(n_val, dtype=bool)
high_conf_mask[high_conf_top_indices] = True
low_conf_mask[low_conf_top_indices] = True

# === Optional Debug Output ===
print(f"High-confidence samples selected: {len(high_conf_top_indices)}")
print(f"Low-confidence samples selected:  {len(low_conf_top_indices)}")
print(f"Mean p1: {np.mean(val_p1):.4f}")
print(f"Mean p1-p2 diff: {np.mean(val_p1_p2_diff):.4f}")
print(f"Mean entropy: {np.mean(val_entropy):.4f}")

```

### cell 7 `code` — class DQNAgent:

```python
from sklearn.metrics.pairwise import cosine_similarity

class DQNAgent:
    def __init__(self, state_size=3, action_size=2):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.990
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(self.state_size,)),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate), loss='mse')
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randint(0, self.action_size - 1)
        q_values = self.model.predict(state, verbose=0)
        return np.argmax(q_values[0])

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target += self.gamma * np.amax(self.model.predict(next_state, verbose=0)[0])
            q_values = self.model.predict(state, verbose=0)
            q_values[0][action] = target
            self.model.fit(state, q_values, epochs=1, verbose=0)
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

# === Initialization ===
agent = DQNAgent(state_size=3, action_size=2)
batch_size = 32
episodes = 30

val_pred_confidence = np.zeros(n_val, dtype=int)

# Initial centroids from top/bottom 5% p1 confidence
high_conf_list = list(high_conf_top_indices)
low_conf_list = list(low_conf_top_indices)

centroid_high = np.array([
    np.mean(val_p1[high_conf_list]),
    np.mean(val_p1_p2_diff[high_conf_list]),
    np.mean(val_entropy[high_conf_list])
])
centroid_low = np.array([
    np.mean(val_p1[low_conf_list]),
    np.mean(val_p1_p2_diff[low_conf_list]),
    np.mean(val_entropy[low_conf_list])
])
high_count = len(high_conf_list)
low_count = len(low_conf_list)

# Remaining samples (excluding anchors)
rest_indices = np.where(~high_conf_mask & ~low_conf_mask)[0]
np.random.shuffle(rest_indices)
subsample_size = min(1500, len(rest_indices))
rest_indices = rest_indices[:subsample_size]

# === Training Loop ===
for episode in range(episodes):
    total_reward = 0
    n_processed = 0
    action_stats = {0: 0, 1: 0}

    for i, idx in enumerate(rest_indices):
        state = np.array([val_p1[idx], val_p1_p2_diff[idx], val_entropy[idx]]).reshape(1, -1)
        action = agent.act(state)
        action_stats[action] += 1

        # Compute similarity to both centroids
        sim_high = cosine_similarity(state, centroid_high.reshape(1, -1))[0][0]
        sim_low = cosine_similarity(state, centroid_low.reshape(1, -1))[0][0]
... truncated 36 lines ...
```

### cell 8 `code` — # Extract test features consistent with training:

```python
from sklearn.metrics import accuracy_score, f1_score



# Extract test features consistent with training:
test_p1 = np.max(test_softmax_outputs, axis=1)
sorted_test_preds = np.sort(test_softmax_outputs, axis=1)
test_p1_p2_diff = sorted_test_preds[:, -1] - sorted_test_preds[:, -2]
test_entropy = compute_entropy(test_softmax_outputs)

test_features = np.stack([test_p1, test_p1_p2_diff, test_entropy], axis=1)

# Predict confidence (action 0 or 1) using trained DQN model
dqn_predictions = agent.model.predict(test_features, verbose=0)
predicted_actions = np.argmax(dqn_predictions, axis=1)  # 0 or 1

# Prepare true binary confidence labels:
known_labels = np.arange(10)  # your known class indices
test_true_labels = true_labels[remaining_indices]
true_confidence = np.isin(test_true_labels, known_labels).astype(int)

# Evaluate performance:
accuracy = accuracy_score(true_confidence, predicted_actions)
f1 = f1_score(true_confidence, predicted_actions)

# Count correct predictions in known and unknown separately:
correct_known = np.sum((predicted_actions == 1) & (true_confidence == 1))
total_known = np.sum(true_confidence == 1)

correct_unknown = np.sum((predicted_actions == 0) & (true_confidence == 0))
total_unknown = np.sum(true_confidence == 0)

print("=== Test Set Confidence Prediction ===")
print(f"Total samples: {len(test_true_labels)}")
print(f"Known samples: {total_known}")
print(f"Unknown samples: {total_unknown}")
print(f"Overall Accuracy: {accuracy:.4f}")
print(f"Overall F1 Score: {f1:.4f}")
print(f"Correct Known predictions: {correct_known} / {total_known}")
print(f"Correct Unknown predictions: {correct_unknown} / {total_unknown}")

```

### cell 9 `markdown` — #Evaluation of CNN-DQN

```text
#Evaluation of CNN-DQN
```

### cell 10 `code` — print("\n=== CNN Predictions Breakdown for Known Classes ===")

```python
print("\n=== CNN Predictions Breakdown for Known Classes ===")
for cls in known_labels:
    cls_mask = (true_known_labels == cls)
    pred_counts = Counter(cnn_pred_known_labels[cls_mask])
    print(f"True class {cls}: CNN predicted counts: {dict(pred_counts)}")

```

### cell 11 `code` — # Load results

```python
from collections import defaultdict

# Load results
loaded = np.load("cnn_results_combined.npz")
true_labels = loaded['true_labels']
predicted_labels = loaded['predicted_labels']
softmax_outputs = loaded['softmax_outputs']

# Known and unknown labels
known_labels = np.arange(10)
unknown_label = 10

# === Use test set only ===
test_indices = remaining_indices  # from your earlier val/test split
test_true = true_labels[test_indices]
test_pred = predicted_labels[test_indices]
test_softmax = softmax_outputs[test_indices]

# Extract test features for DQN
p1 = np.max(test_softmax, axis=1)
sorted_preds = np.sort(test_softmax, axis=1)
p1_p2_diff = sorted_preds[:, -1] - sorted_preds[:, -2]
entropy = -np.sum(test_softmax * np.log(test_softmax + 1e-10), axis=1)
test_features = np.stack([p1, p1_p2_diff, entropy], axis=1)

# Get DQN predictions
dqn_preds = np.argmax(agent.model.predict(test_features, verbose=0), axis=1)  # 0 = unknown, 1 = known

# === Only analyze known-class test samples ===
mask_known = test_true != unknown_label
true_known = test_true[mask_known]
pred_known = test_pred[mask_known]
dqn_known = dqn_preds[mask_known]

# === Count per-class accuracy of CNN+DQN ===
summary = defaultdict(lambda: {'correct': 0, 'total': 0})

for i in range(len(true_known)):
    t = true_known[i]
    p = pred_known[i]
    dqn = dqn_known[i]

    summary[t]['total'] += 1
    if t == p and dqn == 1:
        summary[t]['correct'] += 1

# === Print Summary ===
print("\n=== CNN + DQN Accuracy on Known Test Samples ===")
for cls in sorted(summary):
    correct = summary[cls]['correct']
    total = summary[cls]['total']
    acc = correct / total if total > 0 else 0
    print(f"Class {cls}: {correct} / {total} ({acc:.2%})")

```

---

## `legacy/notebooks/non_pa/DQN_UNSW.ipynb`

- cells: `16`
- size_kb: `85.1`

- signal_cells: `11`

### cell 0 `code` — import numpy as np

```python
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
import tensorflow as tf
from collections import deque
import random

```

### cell 4 `code` — # === Setup ===

```python
# === Setup ===
known_labels = np.arange(6)
unknown_label = 6

# Get all known and unknown indices
known_indices = np.where(np.isin(true_labels, known_labels))[0]
unknown_indices = np.where(true_labels == unknown_label)[0]

# Calculate validation set size as 10% of total dataset
total_size = len(true_labels)
val_size = int(0.1* total_size)

# For a balanced val set, half known and half unknown
val_half_size = val_size // 2

# Ensure we have enough samples
assert len(known_indices) >= val_half_size, "Not enough known samples for validation"
assert len(unknown_indices) >= val_half_size, "Not enough unknown samples for validation"

# Select samples for validation
val_known_indices = known_indices[:val_half_size]
val_unknown_indices = unknown_indices[:val_half_size]
val_indices = np.concatenate([val_known_indices, val_unknown_indices])

# Everything else goes to test set
remaining_indices = np.setdiff1d(np.arange(total_size), val_indices)

# === Sanity Check ===
print("=== Set Sizes ===")
print(f"Validation Set: {len(val_indices)} (Known: {len(val_known_indices)}, Unknown: {len(val_unknown_indices)})")
print(f"Test Set:       {len(remaining_indices)}")

test_known = np.sum(true_labels[remaining_indices] != unknown_label)
test_unknown = np.sum(true_labels[remaining_indices] == unknown_label)

print("\n=== Balance Check ===")
print(f"Test Known:      {test_known}")
print(f"Test Unknown:    {test_unknown}")

```

### cell 5 `code` — def compute_entropy(softmax_outputs):

```python
def compute_entropy(softmax_outputs):
    """
    Compute the entropy of softmax probability distributions.

    Parameters:
        softmax_outputs (np.ndarray): Softmax output array of shape (n_samples, n_classes)

    Returns:
        np.ndarray: Entropy values of shape (n_samples,)
    """
    epsilon = 1e-12  # to avoid log(0)
    softmax_clipped = np.clip(softmax_outputs, epsilon, 1. - epsilon)
    entropy = -np.sum(softmax_clipped * np.log(softmax_clipped), axis=1)
    return entropy

# === Compute Entropy ===
val_softmax_outputs = softmax_outputs[val_indices]
test_softmax_outputs = softmax_outputs[remaining_indices]

val_entropy = compute_entropy(val_softmax_outputs)
test_entropy = compute_entropy(test_softmax_outputs)

# === Stats Check ===
print(f"Validation entropy stats - min: {val_entropy.min():.4f}, max: {val_entropy.max():.4f}, mean: {val_entropy.mean():.4f}")
print(f"Test entropy stats       - min: {test_entropy.min():.4f}, max: {test_entropy.max():.4f}, mean: {test_entropy.mean():.4f}")

```

### cell 6 `code` — def compute_entropy(softmax_probs):

```python
from scipy.stats import entropy

def compute_entropy(softmax_probs):

    epsilon = 1e-12
    softmax_clipped = np.clip(softmax_probs, epsilon, 1. - epsilon)
    return entropy(softmax_clipped.T)  # entropy across classes for each sample

# === Extract softmax outputs for validation set ===
val_softmax_outputs = softmax_outputs[val_indices]  # shape: (n_val_samples, n_classes)

# === Compute p1 (max confidence), p1 - p2, and entropy ===
val_p1 = np.max(val_softmax_outputs, axis=1)
sorted_preds = np.sort(val_softmax_outputs, axis=1)
val_p1_p2_diff = sorted_preds[:, -1] - sorted_preds[:, -2]
val_entropy = compute_entropy(val_softmax_outputs)

# === Define top/bottom 5% size ===
n_val = len(val_indices)
n_top_bottom = int(0.05 * n_val)

# === Get top 5% high-confidence based on p1 only ===
sorted_indices = np.argsort(val_p1)
low_conf_top_indices = sorted_indices[:n_top_bottom]        # bottom 5% → low confidence
high_conf_top_indices = sorted_indices[-n_top_bottom:]      # top 5% → high confidence

# === Create boolean masks (for excluding in training) ===
high_conf_mask = np.zeros(n_val, dtype=bool)
low_conf_mask = np.zeros(n_val, dtype=bool)
high_conf_mask[high_conf_top_indices] = True
low_conf_mask[low_conf_top_indices] = True

# === Optional Debug Output ===
print(f"High-confidence samples selected: {len(high_conf_top_indices)}")
print(f"Low-confidence samples selected:  {len(low_conf_top_indices)}")
print(f"Mean p1: {np.mean(val_p1):.4f}")
print(f"Mean p1-p2 diff: {np.mean(val_p1_p2_diff):.4f}")
print(f"Mean entropy: {np.mean(val_entropy):.4f}")

```

### cell 7 `code` — # --- Step 1: Compute entropy for each sample ---

```python
import matplotlib.pyplot as plt
from scipy.stats import entropy


# --- Step 1: Compute entropy for each sample ---
entropies = entropy(softmax_outputs, axis=1)

# --- Step 2: Separate entropy of known vs unknown ---
known_mask = np.isin(true_labels, known_labels)
unknown_mask = ~known_mask

known_entropies = entropies[known_mask]
unknown_entropies = entropies[unknown_mask]

# --- Step 3: Plot the distributions ---
plt.figure(figsize=(10, 6))
plt.hist(known_entropies, bins=50, alpha=0.7, label='Known', color='skyblue', density=True)
plt.hist(unknown_entropies, bins=50, alpha=0.7, label='Unknown', color='salmon', density=True)
plt.title('Entropy Distribution: Known vs Unknown Samples')
plt.xlabel('Entropy')
plt.ylabel('Density')
plt.legend()
plt.grid(True)
plt.show()

```

### cell 8 `code` — # --- Step 3: Plot the distributions with improved readability ---

```python
# --- Step 3: Plot the distributions with improved readability ---
plt.figure(figsize=(12, 6))

plt.hist(known_entropies, bins=40, alpha=0.7, label='Known', color='skyblue', density=True)
plt.hist(unknown_entropies, bins=40, alpha=0.7, label='Unknown', color='salmon', density=True)

# Title and axis labels
plt.title('Entropy Distribution: Known vs Unknown Samples', fontsize=18, fontweight='bold')
plt.xlabel('Entropy', fontsize=30)
plt.ylabel('Density', fontsize=30)

# Legend and ticks
plt.legend(fontsize=25)
plt.xticks(fontsize=25)
plt.yticks(fontsize=25)

# Grid styling
plt.grid(True, linestyle="--", alpha=0.7)

plt.tight_layout()
plt.show()
```

### cell 9 `code` — class DQNAgent:

```python
from sklearn.metrics.pairwise import cosine_similarity

class DQNAgent:
    def __init__(self, state_size=3, action_size=2):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.990
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(self.state_size,)),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate), loss='mse')
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randint(0, self.action_size - 1)
        q_values = self.model.predict(state, verbose=0)
        return np.argmax(q_values[0])

    def replay(self, batch_size):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target += self.gamma * np.amax(self.model.predict(next_state, verbose=0)[0])
            q_values = self.model.predict(state, verbose=0)
            q_values[0][action] = target
            self.model.fit(state, q_values, epochs=1, verbose=0)
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

# === Initialization ===
agent = DQNAgent(state_size=3, action_size=2)
batch_size = 32
episodes = 30

val_pred_confidence = np.zeros(n_val, dtype=int)

# Initial centroids from top/bottom 5% p1 confidence
high_conf_list = list(high_conf_top_indices)
low_conf_list = list(low_conf_top_indices)

centroid_high = np.array([
    np.mean(val_p1[high_conf_list]),
    np.mean(val_p1_p2_diff[high_conf_list]),
    np.mean(val_entropy[high_conf_list])
])
centroid_low = np.array([
    np.mean(val_p1[low_conf_list]),
    np.mean(val_p1_p2_diff[low_conf_list]),
    np.mean(val_entropy[low_conf_list])
])
high_count = len(high_conf_list)
low_count = len(low_conf_list)

# Remaining samples (excluding anchors)
rest_indices = np.where(~high_conf_mask & ~low_conf_mask)[0]
np.random.shuffle(rest_indices)
subsample_size = min(1500, len(rest_indices))
rest_indices = rest_indices[:subsample_size]

# === Training Loop ===
for episode in range(episodes):
    total_reward = 0
    n_processed = 0
    action_stats = {0: 0, 1: 0}

    for i, idx in enumerate(rest_indices):
        state = np.array([val_p1[idx], val_p1_p2_diff[idx], val_entropy[idx]]).reshape(1, -1)
        action = agent.act(state)
        action_stats[action] += 1

        # Compute similarity to both centroids
        sim_high = cosine_similarity(state, centroid_high.reshape(1, -1))[0][0]
        sim_low = cosine_similarity(state, centroid_low.reshape(1, -1))[0][0]
... truncated 36 lines ...
```

### cell 10 `code` — # === Compute entropy function ===

```python
from sklearn.metrics import accuracy_score, f1_score
from scipy.stats import entropy  # import properly

# === Compute entropy function ===
def compute_entropy(softmax_probs):
    epsilon = 1e-12
    softmax_clipped = np.clip(softmax_probs, epsilon, 1. - epsilon)
    return entropy(softmax_clipped.T)  # entropy for each sample

# === Extract test features consistent with training ===
test_p1 = np.max(test_softmax_outputs, axis=1)
sorted_test_preds = np.sort(test_softmax_outputs, axis=1)
test_p1_p2_diff = sorted_test_preds[:, -1] - sorted_test_preds[:, -2]
test_entropy = compute_entropy(test_softmax_outputs)

# Stack features for DQN
test_features = np.stack([test_p1, test_p1_p2_diff, test_entropy], axis=1)

# Predict confidence (action 0 or 1) using trained DQN model
dqn_predictions = agent.model.predict(test_features, verbose=0)
predicted_actions = np.argmax(dqn_predictions, axis=1)  # 0 = unknown, 1 = known

# Prepare true binary confidence labels:
# 6 known classes (0–5), 1 unknown class (6)
known_labels = np.arange(6)
test_true_labels = true_labels[remaining_indices]
true_confidence = np.isin(test_true_labels, known_labels).astype(int)

# Evaluate performance
accuracy = accuracy_score(true_confidence, predicted_actions)
f1 = f1_score(true_confidence, predicted_actions)

# Correct predictions for known and unknown separately
correct_known = np.sum((predicted_actions == 1) & (true_confidence == 1))
total_known = np.sum(true_confidence == 1)

correct_unknown = np.sum((predicted_actions == 0) & (true_confidence == 0))
total_unknown = np.sum(true_confidence == 0)

print("=== Test Set Confidence Prediction ===")
print(f"Total samples: {len(test_true_labels)}")
print(f"Known samples: {total_known}")
print(f"Unknown samples: {total_unknown}")
print(f"Overall Accuracy: {accuracy:.4f}")
print(f"Overall F1 Score: {f1:.4f}")
print(f"Correct Known predictions: {correct_known} / {total_known}")
print(f"Correct Unknown predictions: {correct_unknown} / {total_unknown}")


```

### cell 11 `markdown` — #Evaluation of CNN-DQN

```text
#Evaluation of CNN-DQN
```

### cell 12 `code` — # known_labels indices

```python
from collections import Counter


# known_labels indices
known_labels = np.arange(5)  # Known classes are 0 to 9 inclusive

# Filter indices for known class samples in the test set
known_indices = np.where(np.isin(true_labels, known_labels))[0]

# Extract relevant arrays for known samples
true_known_labels = true_labels[known_indices]
cnn_pred_known_labels = predicted_labels[known_indices]
dqn_pred_known_confidence = predicted_actions[known_indices]  # 1 means "known" predicted by DQN

```

### cell 13 `code` — print("\n=== CNN Predictions Breakdown for Known Classes ===")

```python
print("\n=== CNN Predictions Breakdown for Known Classes ===")
for cls in known_labels:
    cls_mask = (true_known_labels == cls)
    pred_counts = Counter(cnn_pred_known_labels[cls_mask])
    print(f"True class {cls}: CNN predicted counts: {dict(pred_counts)}")

```

---

## `legacy/notebooks/non_pa/cnn_unsw.ipynb`

- cells: `23`
- size_kb: `373.4`

- signal_cells: `16`

### cell 1 `code` — # Load the dataset

```python
import pandas as pd

# Load the dataset
unsw = pd.read_csv("UNSW_NB15_testing-set.csv")

# List unique labels in 'attack_cat'
unique_labels = unsw['attack_cat'].unique()
print("Unique UNSW attack_cat labels:")
print(unique_labels)

```

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

### cell 3 `code` — # -------------------------------

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import VarianceThreshold
import tensorflow as tf

# -------------------------------
# 1. LOAD UNSW DATASET
# -------------------------------
unsw = pd.read_csv("UNSW_NB15_testing-set.csv")
unsw.columns = unsw.columns.str.strip()

if "attack_cat" in unsw.columns:
    unsw.rename(columns={"attack_cat": "Label"}, inplace=True)

# -------------------------------
# 2. DEFINE KNOWN & UNKNOWN CLASSES
# -------------------------------
known_classes = ["Normal", "DoS", "Fuzzers", "Generic", "Reconnaissance", "Exploits"]
zero_day_classes = ["Analysis", "Shellcode", "Worms", "Backdoor"]

unsw_known = unsw[unsw["Label"].isin(known_classes)].copy()
unsw_unknown = unsw[unsw["Label"].isin(zero_day_classes)].copy()
unsw_unknown["Label"] = "Unknown"

# -------------------------------
# 3. BALANCE KNOWN CLASSES
# -------------------------------
TARGET = 5999
balanced_known = []

for cls in known_classes:
    df_cls = unsw_known[unsw_known["Label"] == cls]
    sampled = df_cls.sample(n=min(TARGET, len(df_cls)), random_state=42)
    balanced_known.append(sampled)

known_df = pd.concat(balanced_known, ignore_index=True)
unknown_df = unsw_unknown.copy()

print("Balanced Known Class Counts:\n", known_df["Label"].value_counts())
print("Unknown Class Count:", unknown_df.shape[0])

# -------------------------------
# 4. BASIC PREPROCESSING (NUMERIC ONLY)
# -------------------------------
numeric_cols = known_df.select_dtypes(include=[np.number]).columns.tolist()
known_df[numeric_cols] = known_df[numeric_cols].replace([np.inf, -np.inf], np.nan)
unknown_df[numeric_cols] = unknown_df[numeric_cols].replace([np.inf, -np.inf], np.nan)

# Fill NaN only in numeric columns
for col in numeric_cols:
    mean_val = known_df[col].mean()
    known_df[col] = known_df[col].fillna(mean_val)
    unknown_df[col] = unknown_df[col].fillna(mean_val)

# -------------------------------
# 5. REMOVE ZERO-VARIANCE FEATURES
# -------------------------------
X_known = known_df[numeric_cols].copy()
X_unknown = unknown_df[numeric_cols].copy()

selector = VarianceThreshold(threshold=0)
X_known = X_known.loc[:, selector.fit(X_known).get_support()]
X_unknown = X_unknown[X_known.columns]

# -------------------------------
# 6. FEATURE SCALING
# -------------------------------
skewed_cols = [col for col in ['Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
                                'Fwd IAT Total', 'Bwd IAT Total', 'Fwd Packets/s', 'Bwd Packets/s',
                                'Fwd IAT Max', 'Bwd IAT Max', 'Max Packet Length'] if col in X_known.columns]

if skewed_cols:
    mms = MinMaxScaler()
    X_known[skewed_cols] = mms.fit_transform(X_known[skewed_cols])
    X_unknown[skewed_cols] = mms.transform(X_unknown[skewed_cols])

standard_cols = [col for col in X_known.columns if col not in skewed_cols]
if standard_cols:
    ss = StandardScaler()
    X_known[standard_cols] = ss.fit_transform(X_known[standard_cols])
    X_unknown[standard_cols] = ss.transform(X_unknown[standard_cols])

# Clip extreme outliers
for col in X_known.columns:
    lower, upper = X_known[col].quantile([0.01, 0.99])
    X_known[col] = X_known[col].clip(lower=lower, upper=upper)
    X_unknown[col] = X_unknown[col].clip(lower=lower, upper=upper)

... truncated 46 lines ...
```

### cell 4 `code` — # Step: Compute class weights for known classes only (0–5)

```python
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

# Step: Compute class weights for known classes only (0–5)
known_class_indices = np.arange(len(known_classes))  # 0 to 5

class_weights_array = compute_class_weight(
    class_weight='balanced',
    classes=known_class_indices,
    y=y_train  # only training labels (known classes)
)

# Convert to dictionary for Keras
class_weights = dict(zip(known_class_indices, class_weights_array))

print(f"Computed class weights (known classes only): {class_weights}")

```

### cell 5 `code` — # Encode only known classes for training

```python
# Encode only known classes for training
le_known = LabelEncoder()
le_known.fit(known_classes)

y_train_encoded = le_known.transform(known_df['Label'])
y_train_cat = tf.keras.utils.to_categorical(y_train_encoded, num_classes=len(known_classes))

```

### cell 6 `code` — # Step 0: Before defining the CNN model

```python
# Step 0: Before defining the CNN model
num_classes_train = y_train_cat.shape[1]  # Number of classes in training (known classes only)
input_shape = (X_train_cnn.shape[1], 1)  # Features × 1 (for CNN input)

print(f"Number of training classes: {num_classes_train}")
print(f"CNN input shape: {input_shape}")

```

### cell 7 `code` — # 1. Encode known classes only

```python
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
import numpy as np

# 1. Encode known classes only
le_known = LabelEncoder()
le_known.fit(known_classes)

y_train_encoded = le_known.transform(known_df['Label'].iloc[X_train.index])
y_test_known_encoded = le_known.transform(known_df['Label'].iloc[X_test_known.index])

# 2. One-hot encode
y_train_cat = tf.keras.utils.to_categorical(y_train_encoded, num_classes=len(known_classes))
y_test_known_cat = tf.keras.utils.to_categorical(y_test_known_encoded, num_classes=len(known_classes))

# 3. Combine with unknowns for full test set
y_unknown_encoded = len(known_classes) * np.ones(unknown_df.shape[0], dtype=int)  # 'Unknown' index
y_test_cat = tf.keras.utils.to_categorical(
    np.concatenate([y_test_known_encoded, y_unknown_encoded]),
    num_classes=len(known_classes) + 1  # 7 classes total
)

```

### cell 8 `code` — import tensorflow as tf

```python
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv1D, ReLU, BatchNormalization, MaxPooling1D, GlobalAveragePooling1D, Dense, Dropout
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam

```

### cell 9 `code` — # Step 0: Before model definition

```python
# Step 0: Before model definition
num_classes_train = y_train_cat.shape[1]  # Should be 10 known classes
input_shape = (X_train_cnn.shape[1], 1)

# Step 10: CNN with reduced capacity
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv1D, ReLU, BatchNormalization, MaxPooling1D
from tensorflow.keras.layers import GlobalAveragePooling1D, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
import tensorflow as tf

inputs = Input(shape=input_shape)

# Conv Block 1
x = Conv1D(filters=8, kernel_size=3, padding='same', kernel_regularizer=l2(0.005))(inputs)
x = ReLU()(x)
x = BatchNormalization()(x)
x = MaxPooling1D(pool_size=2)(x)

# Conv Block 2
x = Conv1D(filters=24, kernel_size=3, padding='same', kernel_regularizer=l2(0.005))(x)
x = ReLU()(x)
x = BatchNormalization()(x)
x = MaxPooling1D(pool_size=2)(x)

# Conv Block 3
x = Conv1D(filters=32, kernel_size=3, padding='same', kernel_regularizer=l2(0.005))(x)
x = ReLU()(x)
x = BatchNormalization()(x)
x = MaxPooling1D(pool_size=2)(x)

# Dense layers
x = GlobalAveragePooling1D()(x)
x = Dense(48, kernel_regularizer=l2(0.005))(x)
x = ReLU()(x)
x = Dropout(0.5)(x)

# Output layer: only 10 known classes
outputs = Dense(num_classes_train, activation='softmax')(x)

model = Model(inputs=inputs, outputs=outputs)

# Custom loss with entropy to encourage smoother output
def custom_loss_with_entropy(y_true, y_pred):
    cross_entropy = tf.keras.losses.categorical_crossentropy(y_true, y_pred)
    epsilon = 1e-7
    y_pred = tf.clip_by_value(y_pred, epsilon, 1 - epsilon)
    entropy = -tf.reduce_sum(y_pred * tf.math.log(y_pred), axis=-1)
    return cross_entropy + 1.0 * entropy

model.compile(
    optimizer=Adam(learning_rate=1e-5, clipnorm=1.0),
    loss=custom_loss_with_entropy,
    metrics=['accuracy']
)

# Debug: Check initial loss
initial_loss = model.evaluate(X_train_cnn, y_train_cat, batch_size=1000, verbose=0)[0]
print(f"Initial loss: {initial_loss}")



```

### cell 10 `code` — # Step 11: Train the model

```python
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Step 11: Train the model
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7)

history = model.fit(
    X_train_cnn, y_train_cat,
    epochs=800,
    batch_size=500,
    validation_split=0.2,
    class_weight=class_weights,
    callbacks=[early_stopping, lr_scheduler],
    verbose=1
)

```

### cell 11 `code` — # Step 12: Sanity check on labels

```python
# Step 12: Sanity check on labels
print("Train classes (unique):", np.unique(y_train))
print("Train one-hot shape:", y_train_cat.shape)
print("Total label classes (including unknown):", len(le.classes_))

```

### cell 12 `code` — # Step 13: Evaluate test metrics on known classes only

```python
# Step 13: Evaluate test metrics on known classes only
# Create mask for known classes in y_test
unknown_encoded = le.transform(['Unknown'])[0]
known_mask = y_test != unknown_encoded

# Select only known-class samples
X_test_known_cnn = X_test_cnn[known_mask]
y_test_known_cat = y_test_cat[known_mask]

# Predict
test_pred_known = model.predict(X_test_known_cnn)
test_pred_classes = np.argmax(test_pred_known, axis=1)
test_true_classes = np.argmax(y_test_known_cat, axis=1)

# Compute metrics
test_acc = accuracy_score(test_true_classes, test_pred_classes)
test_f1 = f1_score(test_true_classes, test_pred_classes, average='weighted')

print(f"Test accuracy (Known classes only): {test_acc:.4f}")
print(f"Test F1 score (Known classes only): {test_f1:.4f}")

```

### cell 13 `code` — true_labels = y_test

```python
true_labels = y_test
unknown_class_index = le.transform(["Unknown"])[0]

known_mask = true_labels != unknown_class_index
unknown_mask = true_labels == unknown_class_index

p_max_known = p_max[known_mask]
p_max_unknown = p_max[unknown_mask]

p1_p2_known = p1_minus_p2[known_mask]
p1_p2_unknown = p1_minus_p2[unknown_mask]

print(f"True known samples in test: {known_mask.sum()}")
print(f"True unknown samples in test: {unknown_mask.sum()}")

```

### cell 14 `code` — # Step 1: Get CNN predictions

```python
import matplotlib.pyplot as plt
import numpy as np

# Step 1: Get CNN predictions
cnn_probs = model.predict(X_test_cnn, batch_size=512, verbose=1)  # shape: (num_samples, 10)
cnn_preds = np.argmax(cnn_probs, axis=1)
p_max = np.max(cnn_probs, axis=1)

# Compute p1 - p2 for confidence gap
sorted_probs = np.sort(cnn_probs, axis=1)
p1_minus_p2 = sorted_probs[:, -1] - sorted_probs[:, -2]

# Step 2: Separate based on true labels
true_labels = y_test
known_mask = true_labels != 6  # known class mask
unknown_mask = true_labels == 6  # unknown class mask

p_max_known = p_max[known_mask]
p_max_unknown = p_max[unknown_mask]

p1_p2_known = p1_minus_p2[known_mask]
p1_p2_unknown = p1_minus_p2[unknown_mask]

# Step 3: Print Stats
print(f"True known samples in test: {known_mask.sum()}")
print(f"True unknown samples in test: {unknown_mask.sum()}")
print(f"\n--- p_max Distribution ---")
print(f"Known class p_max: {p_max_known.mean():.4f} ± {p_max_known.std():.4f}")
print(f"Unknown class p_max: {p_max_unknown.mean():.4f} ± {p_max_unknown.std():.4f}")
print(f"Known class p1-p2 diff: {p1_p2_known.mean():.4f} ± {p1_p2_known.std():.4f}")
print(f"Unknown class p1-p2 diff: {p1_p2_unknown.mean():.4f} ± {p1_p2_unknown.std():.4f}")

# Step 4: Plot Distributions
plt.figure(figsize=(12,6))

plt.hist(p_max_known, bins=50, alpha=0.6, label='Known', color='blue')
plt.hist(p_max_unknown, bins=50, alpha=0.6, label='Unknown', color='red')

plt.title("Softmax p_max Distribution (CNN 10 known classes)", fontsize=18, fontweight='bold')
plt.xlabel("p_max", fontsize=14)
plt.ylabel("Frequency", fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.show()

# Optional: Plot p1-p2 distribution
plt.figure(figsize=(12,6))
plt.hist(p1_p2_known, bins=50, alpha=0.6, label='Known', color='blue')
plt.hist(p1_p2_unknown, bins=50, alpha=0.6, label='Unknown', color='red')
plt.title("p1 - p2 Distribution (Confidence Gap)", fontsize=18, fontweight='bold')
plt.xlabel("p1 - p2", fontsize=14)
plt.ylabel("Frequency", fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.7)
plt.show()

```

### cell 15 `code` — # Step 5: Plot Distributions

```python
# Step 5: Plot Distributions
plt.figure(figsize=(12,6))

# Increase histogram text size
plt.hist(p_max_known, bins=40, alpha=0.6, label='Known', color='blue')
plt.hist(p_max_unknown, bins=40, alpha=0.6, label='Unknown', color='red')

# Title and axis labels with bigger font
plt.title("Softmax p_max Distribution (CNN 0-9 output)", fontsize=18, fontweight='bold')
plt.xlabel("p_max", fontsize=30)
plt.ylabel("Frequency", fontsize=30)

# Bigger ticks (scale numbers on axes)
plt.xticks(fontsize=25)
plt.yticks(fontsize=25)

# Legend with bigger font
plt.legend(fontsize=14)

# Grid
plt.grid(True, linestyle="--", alpha=0.7)

plt.show()

```

### cell 16 `code` — # Step 1: Get softmax predictions from CNN

```python
# Step 1: Get softmax predictions from CNN
cnn_probs = model.predict(X_test_cnn)  # shape
true_labels = y_test                   # shape

# Step 2: Save softmax outputs and true labels as npy
np.save("cnn_softmax_outputs.npy", cnn_probs)
np.save("true_labels.npy", true_labels)

print("Saved 'cnn_softmax_outputs.npy' (shape:", cnn_probs.shape, ")")
print("Saved 'true_labels.npy' (shape:", true_labels.shape, ")")

```

---

## Initial interpretation

- The DQN logic should be treated as a separate OSR/evaluator track unless the notebooks reveal a backbone-training loss that materially differs from the current PA CNN.
- If the CNN recipe differs materially, port it as a new catalog family, not as an ad hoc notebook workflow.
- Candidate future family name: `shreyash_cnn_dqn_backbone`.
- Candidate future eval method name: `dqn_osr_expanded5`.

## Porting checklist

- [ ] Extract exact CNN architecture.
- [ ] Extract preprocessing/input tensor assumptions.
- [ ] Extract optimizer/lr/batch/epochs/dropout/regularization.
- [ ] Extract DQN state vector.
- [ ] Extract action semantics.
- [ ] Extract reward/centroid/update logic.
- [ ] Compare against `dqn_osr.py`.
- [ ] Decide whether to port only DQN OSR head or also CNN backbone training.
- [ ] Add catalog family only after a tiny PA smoke validation.
