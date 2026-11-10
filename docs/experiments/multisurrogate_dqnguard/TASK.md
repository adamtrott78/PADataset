# Multi-Surrogate DQNGuard Research Task

## Task identity

- Task ID: `mth602-final-multisurrogate-dqnguard-v1`
- Research repository: `adamtrott78/PADataset`
- Working branch: `mth602-final-multisurrogate-dqnguard-v1`
- Branch base: `a8f952c7cf964730a01b2dc5c6cd75850912f94f`
- Course role: MTH 602 final-project research implementation
- Status: ACTIVE — design/baseline freeze
- Scientific owner: PADataset
- Class-facing owner: `adamtrott78/MTH602-AdamTrott/project/`

## Research question

Can DQNGuard be redesigned to learn from **multiple surrogate unknown behaviors**
rather than depending on one favorable surrogate, while retaining one coherent
unknown score and the paper's explicit **5% known-rejection calibration budget
(95% known retention)**?

The target unknown must remain genuinely unseen during the main calibration
procedure. Target-open calibration is a separate diagnostic/control regime, not
the primary method.

## Why this task exists

The MILCOM 2026 result chain established three facts:

1. DQNGuard provides a strong thresholded operating point under fixed
   Scan-surrogate calibration:
   - mean Unknown F1: 0.865
   - mean OSR macro F1: 0.881
   - realized mean known rejection: 0.050
   - mean Unknown AUROC: 0.891
2. Surrogate transfer is strongly target-dependent. The best surrogate changes
   across the 20 ordered Target-Surrogate cells, and some mismatched pairings
   nearly fail.
3. The tested target-blind single-surrogate selectors were not reliable:
   surrogate calibration performance was essentially uncorrelated with later
   target performance; confidence-geometry diagnostics ranked transfer poorly;
   simple feature geometry was only weakly useful.

VarMax surrogate-all provides a useful design clue because multiple known classes
can act as pseudo-unknowns in one **fixed** decision architecture. Candidate
calibration settings compete in one common score space.

DQNGuard cannot copy that procedure mechanically. In current DQNGuard, surrogate
states participate in fitting the DQN itself. Different surrogates therefore
produce different nonlinear score functions and different threshold spaces.
The current external-surrogate design also excludes the surrogate from backbone
training, so withholding several external surrogates at once would collapse the
five-class known taxonomy.

The final-project problem is therefore architectural, not merely a larger
threshold sweep.

## Evidence anchors

Read before design or implementation:

- `README.md`
- `experiments/CONTEXT.md`
- `experiments/context/BACKBONE.md`
- `experiments/context/DQNGUARD.md`
- `experiments/context/VARMAX.md`
- `experiments/context/RESULTS.md`
- `papers/milcom2026/PAPER_GROUND_TRUTH.md`
- `papers/milcom2026/PAPER_EVIDENCE_MAP.md`
- `papers/milcom2026/sections/5-results.tex`
- `papers/milcom2026/sections/6-discussion.tex`
- `papers/milcom2026/sections/7-conclusion.tex`

MILCOM presentation evidence further names the three architecture hypotheses
below. Those are future-work hypotheses, not prior evaluated results.

## Fixed scientific constraints

1. **Known-budget semantics**
   - Preserve DQNGuard's known-only thresholding logic.
   - The calibration operating budget is 5% known rejection / 95% known
     retention.
   - Do not claim this guarantees exactly 5% rejection on held-out known test
     data; report realized held-out rejection separately.

2. **No target leakage**
   - Main multi-surrogate methods may not use labeled target-open validation.
   - Target-open calibration can be run only as a clearly labeled diagnostic
     upper-bound/control.

3. **Known/open separation**
   - Backbone training, surrogate evidence, threshold calibration, and target
     testing remain distinct evidence partitions.
   - Do not silently reuse test target evidence for architecture selection,
     normalization, aggregation, or threshold choice.

4. **Taxonomy integrity**
   - Do not solve multi-surrogate calibration by simply withholding several
     external classes if that destroys the intended known taxonomy.
   - Any internal pseudo-open construction must be labeled as such and must not
     be described as equivalent to an externally withheld unknown.

5. **Provenance**
   - Preserve source commit/diff, cache identity, pooled length, split identity,
     seed, checkpoint, target, surrogate evidence construction, DQN fit
     configuration, normalization/aggregation parameters, threshold rule, and
     output summaries.
   - The surviving authoritative MILCOM experiment lineage uses pooled length
     16,384. Preserve the accepted-paper 8,192 wording as a provenance conflict;
     do not rewrite the experiment identity.

6. **Scale-up**
   - New architectures follow smoke -> small real run -> full matrix.
   - A process exit or attractive plot is not scientific completion.

## Baselines

### B0 — fixed-surrogate DQNGuard

Paper-facing reference:
- fixed Scan surrogate
- targets Burst, Sustain, Hop, Replay
- 5% known-rejection calibration budget
- Unknown F1 0.865 average
- OSR macro F1 0.881 average
- known rejection 0.050 average
- Unknown AUROC 0.891 average

This is the primary thresholded-operating-point baseline.

### B1 — full Target-Surrogate DQNGuard matrix

Twenty ordered target/surrogate cells across Scan, Burst, Sustain, Hop, Replay.
Use this as the transfer-variance diagnostic and for worst-case/best-case
reference. Do not select a method using target-test F1.

### B2 — VarMax surrogate-all

Historical comparison:
- Unknown F1 0.745 average
- OSR macro F1 0.778 average
- known rejection 0.128 average
- Unknown AUROC 0.951 average

Important: this is not scientifically identical calibration to fixed-surrogate
DQNGuard. Treat it as a multi-surrogate design/control reference, not a
budget-matched head-to-head claim.

## Architecture hypotheses

### A — pooled multi-surrogate DQN

Pool multiple surrogate-open confidence-state sets and fit **one DQN**.

Goal:
- one learned score function;
- one common nonlinear score space;
- one known-only budgeted final threshold.

Central design question:
How can multiple surrogate state sets be constructed without collapsing the
known taxonomy or leaking target information?

Do not implement until the evidence-partition design is written and reviewed.

### B — surrogate-specific DQNs + normalized aggregation

Train one DQN per surrogate evidence source, then map each DQN's output into a
common calibrated scale before aggregation.

Candidate aggregation families are proposals only until validated:
- normalized maximum / OR-like evidence;
- normalized mean;
- robust quantile/median;
- learned target-blind combiner using only allowed calibration evidence.

The normalization must be fitted without target labels. Raw thresholds from
different DQNs are not directly comparable.

### C — hybrid: one DQN + multi-surrogate deterministic guard

Keep one learned DQN confidence signal and move multi-surrogate reasoning into
the VarMax-derived deterministic guard/calibration side.

Goal:
- smallest architectural departure from current DQNGuard;
- retain one DQN score space;
- exploit multiple pseudo-open behaviors in deterministic gap/variance/energy
  calibration;
- retain the final known-only 5% threshold.

This is the preferred **first implementation candidate** because it is closest
to the current executable contract and should produce the fastest falsifiable
result.

## Evaluation protocol

For each candidate architecture, evaluate at minimum:

- realized held-out known rejection;
- Unknown precision / recall / F1;
- OSR macro F1;
- Unknown AUROC;
- per-target metrics;
- mean across target folds;
- standard deviation across target folds;
- **worst-target Unknown F1**;
- calibration feasibility/fallback status;
- score distributions and threshold provenance.

Primary scientific question is not only whether the mean rises. A method that
reduces catastrophic target-specific failures or target-to-target variance while
preserving the budget may be valuable even if mean F1 changes modestly.

## Selection rule for the final-project candidate

Do not select by target-test performance during tuning.

After all candidate configurations are frozen using allowed calibration evidence,
compare held-out target folds using this priority:

1. valid evidence partition and no leakage;
2. preserved 5% known-rejection calibration budget;
3. improved worst-target Unknown F1 / reduced catastrophic transfer failure;
4. mean Unknown F1;
5. OSR macro F1;
6. realized known-test rejection;
7. AUROC and secondary diagnostics.

A scientifically well-supported negative result is acceptable. Do not force a
"win" by changing the evaluation protocol after seeing target labels.

## Staged execution plan

### Stage 00 — freeze provenance and reproduce references

- confirm branch base and local Lambda checkout/worktree state;
- identify exact existing B0/B1/B2 result artifacts and source summaries;
- record cache/checkpoint identities used by the relevant lineage;
- reconstruct the exact 5% threshold semantics from current source;
- create a compact baseline table with provenance links;
- do not retrain unless existing evidence is insufficient.

Exit:
- baseline metrics and identities are machine-readable and reviewable;
- no unresolved target/surrogate naming ambiguity.

### Stage 01 — architecture/evidence-partition design

For A, B, and C specify:

- backbone taxonomy;
- which examples fit the DQN;
- which examples fit deterministic guard bands;
- which examples fit normalization/aggregation;
- which known examples set the 5% threshold;
- which target examples are completely untouched until test;
- score definition and direction;
- what is shared vs surrogate-specific.

Also identify the minimum source changes required for each architecture.

Exit:
- three executable designs with no target leakage;
- taxonomy integrity explicitly checked;
- C selected as the first implementation unless evidence shows it is invalid.

### Stage 02 — common evaluation/provenance contract

Before architecture code proliferates:

- define one result schema for B0/A/B/C;
- persist calibration identity, score normalization, threshold, metrics, and
  fallback status;
- add deterministic smoke fixtures where possible;
- preserve compatibility with existing reducer/analysis workflow or provide a
  small adapter.

Exit:
- one smoke result can be reduced and compared without manual reinterpretation.

### Stage 03 — architecture C smoke + small real run

Implement the hybrid candidate first.

Run:
1. synthetic/unit smoke where possible;
2. one reviewed real target fold;
3. compare against the matching fixed-surrogate DQNGuard cell.

Exit:
- common score and threshold are valid;
- budget semantics are preserved;
- no target leakage;
- result is interpretable enough to decide whether to scale.

### Stage 04 — architecture A smoke + small real run

Implement pooled multi-surrogate DQN only after the evidence-partition design is
settled.

Exit criteria mirror Stage 03.

### Stage 05 — architecture B smoke + small real run

Implement surrogate-specific DQN normalization/aggregation.

The stage must explicitly validate that normalization creates comparable score
semantics before any full matrix is allowed.

### Stage 06 — controlled architecture bake-off

Freeze one or more defensible configurations per architecture using calibration
evidence only.

Run the same target-fold set and seed policy.

Exit:
- no missing/duplicate target identities;
- consistent metrics/provenance;
- candidate chosen using the predeclared selection rule.

### Stage 07 — full multi-target evaluation

Run the selected architecture across the intended target set, preserving the
same scientific partitions and known-budget semantics.

If runtime permits, add multiple seeds only after the single-seed identity matrix
is complete and validated.

### Stage 08 — MTH 602 final-project analysis

Class-facing analysis should answer:

- why single-surrogate DQNGuard fails to generalize uniformly;
- why VarMax surrogate-all is easy under a fixed scorer but DQNGuard is not;
- which multi-surrogate architecture was tested;
- how the 5% known-rejection budget was preserved;
- whether target dependence was reduced;
- what happened to mean and worst-case Unknown F1;
- what the experiment teaches about learned calibration and generalization.

Reusable research implementation/results remain in PADataset. The MTH 602 repo
contains the pinned research source, class-specific analysis, figures, and final
report/presentation.

## First executable next action

Do **Stage 00 only**:

1. establish the prepared Lambda PADataset checkout/worktree state;
2. locate the exact B0 fixed-Scan DQNGuard summaries, B1 20-cell Target-Surrogate
   matrix source, and B2 VarMax surrogate-all summaries;
3. record source/cache/checkpoint/evaluator identities;
4. write a baseline-provenance artifact for review.

Do not implement architecture A/B/C until Stage 00 is complete and Stage 01
evidence partitions are explicit.


## Stage 00 current status

**COMPLETE — provenance frozen from the prepared Lambda evidence checkout.**

Machine-readable artifact:

- `docs/experiments/multisurrogate_dqnguard/stage00_baseline_provenance.json`

Recovered and verified:

- clean execution authority is `17e1147614f27702e43565089d618182ff71c5af`;
- historical evidence checkout is preserved read-only at
  `leaf2026-review-1571342865@b5a09cede6680b9e2a53eac244db4fbd7eaf76ec`;
- the historical tracked diff touches only `experiments/pa_dashboard.py` and two
  manuscript sections; the Git index is clean;
- the surviving run/config/checkpoint/cache lineage is 16,384 samples and the
  later 8,192 manuscript wording remains an explicit provenance conflict;
- B0 fixed-Scan DQNGuard is bound to all four evaluator summaries, configs and
  `best_model.pt` hashes;
- B1 is bound to all 20 ordered Target–Surrogate evaluator summaries, configs and
  checkpoints, and all 20 evaluator `unknown_f1` values exactly match the
  accepted rendered matrix;
- B2 VarMax surrogate-all is bound to all four evaluator summaries and the same
  underlying four OG backbone runs;
- the accepted paper main-results summary and rendered TS matrix are SHA-256
  pinned in the provenance artifact;
- the two historical aggregate-input CSVs named by `experiments/context/RESULTS.md`
  are absent from the current evidence checkout. They were **not recreated or
  invented**; the recovered per-run evidence chains and accepted rendered
  outputs are preserved instead.

Stage 00 exit conditions are satisfied: baseline metrics and identities are
machine-readable/reviewable and target/surrogate naming is unambiguous.

**Next:** Stage 01 only — write the explicit A/B/C evidence partitions and
taxonomy/leakage checks. Do not implement architecture A/B/C until Stage 01 is
reviewed.


## Stage 01 current status

**COMPLETE — evidence partitions frozen.**

Design artifact:

- `docs/experiments/multisurrogate_dqnguard/STAGE01_EVIDENCE_PARTITIONS.md`

The design enforces target quarantine, known-only backbone checkpoint selection,
disjoint calibration roles, one known-only 5% final threshold, and explicit
shared-vs-surrogate-specific state for A/B/C. Architecture C is selected as the
first implementation candidate, but implementation remains blocked on Stage 02's
common evaluation/provenance contract.

**Next:** Stage 02 only — define the common result schema and deterministic smoke
contract before architecture code proliferates.
