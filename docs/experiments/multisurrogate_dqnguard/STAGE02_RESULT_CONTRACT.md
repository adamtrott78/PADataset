# Stage 02 — Common Evaluation and Provenance Contract

Status: **FROZEN**

This contract applies to B0 and new architectures A/B/C. It exists so a smoke
run, small real run, and full evaluation can be reduced without manual
reinterpretation.

## Canonical machine-readable record

Schema:

- `docs/experiments/multisurrogate_dqnguard/stage02_result_schema.v1.json`

Every evaluated target fold emits one JSON record satisfying that schema.

## Mandatory identity fields

Each record must bind:

- exact PADataset Git SHA;
- cache length and cache root;
- seed;
- backbone run directory;
- backbone config SHA-256;
- checkpoint path and SHA-256;
- known-class taxonomy;
- checkpoint-selection regime;
- architecture ID;
- target PA;
- evidence-partition identity;
- score definition/direction;
- normalization and aggregation parameters;
- final known-only threshold and calibration rejection;
- evaluator command;
- output/result SHA-256;
- fallback/feasibility state.

## Metrics

Required per target fold:

- realized held-out known rejection;
- Unknown precision;
- Unknown recall;
- Unknown F1;
- OSR macro F1;
- Unknown AUROC.

Reducers may additionally compute mean, sample standard deviation, and
worst-target Unknown F1 across a frozen target set. They must never choose a
configuration by target-test performance.

## Threshold contract

For A/B/C:

- one scalar score, larger = more unknown-like;
- final threshold source = known-only `K_threshold`;
- budget = 0.05;
- quantile = 0.95;
- persist the numeric threshold and measured calibration known rejection;
- held-out known-test rejection is a metric, not a threshold fitting input.

Historical B0 records may preserve their exact historical 0.0512 finite-sample
calibration rejection while declaring the intended 0.05 budget.

## Architecture-specific payload

### A

Persist:
- all contributing pseudo-open surrogate IDs;
- per-surrogate sample counts;
- pooled DQN seed/config;
- guard-band identity.

### B

Persist:
- each surrogate-specific DQN identity;
- each normalization map identity;
- aggregation rule and parameters;
- shared guard-band identity if used.

### C

Persist:
- one DQN identity;
- each surrogate-specific deterministic guard identity;
- each guard normalization identity;
- fixed guard aggregation rule;
- final DQN+guard score definition.

## Deterministic smoke contract

A smoke run is valid only if all checks below pass:

1. **Partition identity**
   - target sample IDs are absent from all fit/calibration partitions;
   - no sample ID appears in more than one calibration role;
   - every pseudo-open sample is absent from the known-role slices of the same
     frozen configuration.

2. **Score direction**
   - synthetic/fixture unknown-like perturbation increases the scalar score;
   - repeated evaluation with identical seed/config produces identical scores.

3. **Known-only threshold**
   - threshold is computed only from `K_threshold`;
   - changing target-test labels or target-test ordering cannot alter it.

4. **Normalization**
   - B/C normalization parameters are fitted without target examples;
   - normalized score mappings are monotone in raw unknown score.

5. **Aggregation**
   - aggregation is deterministic and predeclared;
   - no target metric participates in selecting max/mean/median/etc.

6. **Provenance**
   - config, checkpoint, result and source identities are present;
   - result validates against the JSON schema;
   - failure/fallback state is explicit rather than inferred from process exit.

## Reducer contract

A reducer may combine records only when these identities match the intended
comparison:

- source schema version;
- architecture configuration ID;
- cache identity;
- seed policy;
- target set;
- score semantics;
- threshold budget.

The reducer must reject duplicate architecture/target/seed identities unless an
explicit multi-seed aggregation mode is requested.

Outputs:

- per-target table;
- mean/std table;
- worst-target Unknown F1;
- realized known rejection summary;
- provenance index containing source record hashes.

## Stage 02 exit

Stage 02 is complete when:

- the result schema is committed;
- deterministic smoke invariants are frozen;
- architecture C can emit one record without inventing architecture-specific
  output semantics.

No architecture implementation is included in this stage.
