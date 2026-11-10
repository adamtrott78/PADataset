# Stage 01 — Multi-Surrogate DQNGuard Evidence Partitions

Status: **FROZEN DESIGN — implementation not yet started**

Authority:
- task: `mth602-final-multisurrogate-dqnguard-v1`
- Stage 00 provenance: `stage00_baseline_provenance.json`
- Stage 00 commit: `025f73632609891ee5292880b0efe25f5d50df04`

## Non-negotiable partition rules

For every held-out target fold (T):

1. **Target quarantine**
   - No labeled target example may influence backbone gradient training, checkpoint
     selection, DQN fitting, deterministic guard fitting, score normalization,
     aggregation, architecture selection, or the 5% threshold.
   - Target-open calibration remains a separately labeled diagnostic/control only.
   - Target examples are first consumed by the final frozen test evaluator.

2. **Backbone taxonomy**
   - The backbone known taxonomy is the four non-target PA classes.
   - New architecture runs use **known-only checkpoint selection**. Do not use the
     historical `open_conf` selection path when it consumes withheld-target
     validation evidence.
   - The backbone output interface remains logits, softmax probabilities,
     predicted class, and the 256-value MLP embedding.

3. **Calibration sample partition**
   - Each non-target known class is deterministically split by sample identity into
     disjoint calibration roles before any architecture-specific fitting:
     `K_fit`, `K_guard`, `K_norm`, and `K_threshold`.
   - Any class temporarily treated as an internal pseudo-open surrogate uses a
     dedicated `P_s` slice disjoint from all of that class's known-role slices.
   - No physical sample may carry both known and pseudo-open labels within one
     frozen configuration.

4. **Final operating point**
   - Every architecture produces one scalar unknown score where larger means more
     unknown-like.
   - The final threshold is the 95th percentile of **known-only**
     `K_threshold` scores, implementing the 5% calibration rejection budget.
   - Report realized calibration and held-out known-test rejection separately.

5. **Evaluation-only target labels**
   - After configuration freeze, target test labels may be used only to compute
     Unknown precision/recall/F1, OSR macro F1, AUROC, and descriptive per-target
     comparisons.
   - Target-test metrics cannot retroactively change the architecture,
     normalization, aggregation, or threshold.

## Architecture A — pooled multi-surrogate DQN

### Taxonomy
Backbone: all four non-target classes.

### DQN-fit evidence
For each internal surrogate class (s):
- open states: `P_s` from class (s);
- known states: balanced `K_fit` states from the other three classes.

Pool the four surrogate episodes into one balanced DQN training set. Preserve
surrogate source IDs in provenance, but the DQN receives one common binary
known/open objective.

### Deterministic guard evidence
Fit predicted-class gap/absolute-logit-variance/positive-energy bands from
`K_guard` only. No pseudo-open or target samples fit these bands.

### Normalization / aggregation
None across DQNs because there is one DQN. The combined scalar follows the
DQNGuard form:

`Q_unknown - Q_known + band_weight * mean_band_distance`.

### Final threshold
95th percentile of combined scores on `K_threshold`.

### Shared vs surrogate-specific
- shared: backbone, DQN, guard bands, score, threshold;
- surrogate-specific: only the provenance-tagged `P_s` evidence contributions
  entering the pooled DQN fit.

### Main risk
The same semantic PA class is pseudo-open in its own episode but known in other
episodes. Samples remain disjoint, so there is no sample-label collision, but the
distribution-level objective is intentionally contradictory. This must be tested
as a hypothesis, not treated as obviously valid.

## Architecture B — surrogate-specific DQNs + normalized aggregation

### Taxonomy
Backbone: all four non-target classes.

### DQN-fit evidence
Train one DQN (D_s) per internal surrogate class (s):
- open states: `P_s`;
- known states: balanced `K_fit` from the other three classes.

### Deterministic guard evidence
Each (D_s) may use the same shared known-only predicted-class guard bands fitted
from `K_guard`; do not fit bands from target data.

### Score normalization
For each DQN, compute its raw combined score on a dedicated known-only
`K_norm` set. Map raw score to an empirical known-tail scale, e.g. empirical CDF
or exceedance probability, so scores are comparable without target labels.
Normalization parameters are surrogate-specific and frozen before target test.

### Aggregation
Predeclare target-blind candidates:
- max normalized score;
- mean normalized score;
- median normalized score.

Do not choose among them using target-test performance. Configuration selection
must use only allowed calibration evidence or be fixed a priori.

### Final threshold
Apply the selected aggregation to `K_threshold`; use its 95th percentile.

### Shared vs surrogate-specific
- shared: backbone, optional known guard bands, aggregation rule, final threshold;
- surrogate-specific: DQN weights and normalization map.

### Required validation before scale-up
Verify monotone normalized score semantics and comparable known-score
distributions before any full target matrix.

## Architecture C — one DQN + multi-surrogate deterministic guard

**Selected first implementation candidate.**

### Taxonomy
Backbone: all four non-target classes.

### DQN-fit evidence
Fit exactly one DQN from a balanced **generic internal pseudo-open pool**:
- open states: equal-count union of the four disjoint `P_s` slices;
- known states: balanced `K_fit` states;
- surrogate identity is not an input to the DQN.

This gives one learned confidence score space. The multi-surrogate structure is
preserved outside the DQN rather than by training multiple learned score spaces.

### Deterministic multi-surrogate guard evidence
For each surrogate class (s), fit a deterministic pseudo-open guard candidate
using only:
- known fit/guard slices from non-(s) classes;
- the dedicated `P_s` slice as pseudo-open evidence where the guard procedure
  requires it.

Candidate guard parameters may include gap, absolute-logit-variance, and positive
energy bands/penalties. Preserve each candidate's surrogate identity.

### Guard aggregation
Before target testing, combine surrogate-specific deterministic guard evidence
with a fixed target-blind rule. First implementation candidate:

`guard_multi(x) = max_s normalized_guard_s(x)`

where each guard is normalized using known-only `K_norm` evidence. Max is
chosen a priori as an OR-like "any surrogate recognizes unknownness" rule; it is
not selected from target F1.

The single scalar architecture score is:

`score_C(x) = DQN_margin(x) + guard_multi(x)`

with direction fixed so larger is more unknown-like.

### Final threshold
95th percentile of `score_C` over known-only `K_threshold`.

### Shared vs surrogate-specific
- shared: backbone, one DQN, final scalar score, final threshold;
- surrogate-specific: deterministic guard parameters and known-only
  normalization maps.

### Why C is first
It preserves one learned DQN score space, avoids cross-DQN comparability as an
initial problem, moves the explicit multi-surrogate reasoning into the
deterministic side where VarMax already demonstrates competing pseudo-unknown
candidates, and remains falsifiable with a small source change.

## Historical baseline compatibility

B0/B1 are retained as historical baselines, not copied as the new data
partition:
- historical Target–Surrogate runs excluded both target and external surrogate
  from the backbone, leaving three known classes;
- the new multi-surrogate architectures keep all four non-target classes in the
  backbone taxonomy;
- historical backbone `open_conf` selection may consume target validation and
  therefore cannot be used for new no-target-leakage architecture selection.

B2 VarMax surrogate-all is a design clue, not a budget-matched comparator. Its
internal pseudo-unknown classes remain backbone-known and its historical
surrogate-all sweep is not equivalent to DQNGuard's 5% known-budget threshold.

## Frozen Stage 01 decision

- A: executable but high-risk because pooled DQN training gives class
  distributions both known and pseudo-open roles across disjoint episodes.
- B: executable but deferred until score normalization is validated.
- C: **first implementation candidate**.
- No architecture code is authorized by this document alone until the common
  Stage 02 result/provenance contract is defined.
