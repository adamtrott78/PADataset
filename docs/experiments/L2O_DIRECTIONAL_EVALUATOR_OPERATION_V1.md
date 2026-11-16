# Track-A bounded directional evaluator operation — v1 design

Status: candidate design only. This document does **not** grant workflow authority.

## Purpose

Execute exactly one frozen Track-A directional DQNGuard cell from a previously completed canonical backbone artifact while preserving:

- exact GitHub artifact provenance,
- exact canonical backbone/checkpoint/config identity,
- surrogate-only DQN open calibration,
- known-only threshold selection,
- true-target quarantine until final evaluation,
- one immutable result record per directed cell.

The final campaign contains 10 canonical backbones and 20 ordered target/surrogate cells.

## Required sequencing

Do not add or execute this operation until:

1. all 10 canonical backbones are COMPLETE and frozen in
   `manifests/l2o_canonical_backbone_matrix_v1.json`;
2. the final 20 directional request manifests exist;
3. PR #26 contract tests pass through the authorized candidate-execution path;
4. the authority-owned workflow change is separately reviewed.

## Proposed request token

A future authority-owned workflow may accept only:

```
l2o_directional_eval:manifests/configs/l2o_directional_eval_v1/<request>.json
```

The request path must resolve beneath the declared request-manifest root and be a regular repository file.

No evaluator hyperparameters may appear in the trigger comment.

## Frozen inputs

The request manifest binds:

- canonical key,
- artifact ID,
- artifact digest,
- evaluation target,
- evaluation surrogate,
- checkpoint tag,
- frozen policy ID.

The policy is:

`manifests/l2o_directional_eval_policy_v1.json`

The canonical artifact authority is:

`manifests/l2o_canonical_backbone_matrix_v1.json`

## Required execution phases

### 1. Validate request

Use `experiments/l2o_eval_request_contract.py`.

Reject:

- non-COMPLETE canonical backbone,
- target/surrogate outside the canonical excluded pair,
- request artifact drift,
- policy drift,
- any policy permitting true-target calibration,
- any policy permitting target-label tuning.

### 2. Fetch GitHub artifact metadata

Using the authenticated authority-owned workflow token, fetch the artifact metadata for the exact artifact ID.

Persist the returned metadata as JSON in the bounded job workspace.

### 3. Validate transport binding

Use `experiments/l2o_artifact_transport_contract.py`.

Require exact agreement among the request, canonical matrix, and GitHub metadata for:

- artifact ID,
- artifact SHA-256 digest,
- workflow run ID,
- non-expired state.

### 4. Download artifact ZIP

Download only the artifact whose metadata passed phase 3.

The destination must be inside the job's bounded temporary/result workspace.

### 5. Rehydrate and validate backbone

Use `experiments/l2o_artifact_rehydrate.py`.

Fail closed on:

- path traversal or symlink members,
- receipt schema/decision/operation mismatch,
- dataset-profile mismatch,
- candidate-SHA mismatch,
- checkpoint/config hash mismatch,
- target/surrogate/known topology drift,
- non-known-only checkpoint selection,
- target-open validation,
- target test previously consumed,
- target quarantine not preserved.

The resulting run directory becomes the sole evaluator backbone input.

### 6. Execute frozen evaluator

Invoke:

`experiments/pa_eval_dqn_guard_surrogate_open.py`

Arguments must be produced by `experiments/l2o_eval_request_contract.py`, not manually assembled.

The frozen Track-A policy requires:

- checkpoint = best_model,
- band_accept_mode = var_energy,
- decision_mode = score_threshold,
- max_known_reject_cal = 0.05,
- known_cap = 625,
- open_cap = 625,
- state = softmax3,
- evaluator device = cuda,
- batch size = 128,
- no `--mix-true-open`.

The true target may appear only in the final target evaluation split.

### 7. Build provenance-bound result record

Use `experiments/l2o_eval_result_record.py`.

Each cell must produce:

`result_record.json`

The record binds:

- policy ID,
- canonical pair,
- known classes,
- ordered target/surrogate direction,
- directional-reuse flag,
- exact artifact/run/job/candidate/checkpoint/config provenance,
- target-tuning=false,
- surrogate-only calibration=true,
- known-only threshold provenance,
- OSR metrics.

### 8. Upload bounded result artifact

Upload only the current cell's bounded result directory plus its execution receipt.

Do not mutate the canonical matrix from inside the scientific runner.

## Campaign completion

After exactly 20 terminal cell artifacts are collected, materialize them into one reviewed aggregation workspace and run:

`experiments/l2o_eval_matrix_aggregate.py`

This must reject:

- fewer or more than 20 result records,
- duplicate cells,
- missing cells,
- artifact drift,
- policy drift,
- target-label tuning,
- target-open calibration,
- metrics outside [0,1].

Then run:

`experiments/l2o_eval_matrix_report.py`

to produce target×surrogate tables and per-target transfer summaries.

A historical baseline comparison is permitted only when an explicit reviewed 20-cell baseline CSV is supplied. The tool must not discover or choose a baseline implicitly.

## Scheduling

Evaluator cells may use the same two isolated scientific GPU lanes after backbone training is complete.

Scheduling may distribute independent cells across both lanes, but each lane must continue to use its existing GPU UUID isolation and bounded scientific-runner identity.

No cell may alter a backbone artifact or another cell's result directory.

## Authority boundary

This document and PR #26 are candidate implementation evidence only.

They do not authorize:

- modifying default-branch workflows,
- widening accepted workflow trigger grammar,
- downloading arbitrary artifacts,
- running evaluator cells,
- merging any PR.

Those actions require the existing authority-owned review/activation process.
