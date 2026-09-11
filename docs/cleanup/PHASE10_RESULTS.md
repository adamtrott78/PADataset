# Phase 10 validation results

This file records the completed cold-start/operator validation defined by
[PHASE10_OPERATOR_VALIDATION.md](PHASE10_OPERATOR_VALIDATION.md).

The validation target was the exact repository tree:

`0807d91d10b4baf6602442a83efdfdf4f19cc7d2`

The evaluator package itself was intentionally created after that tree so the
blank-chat readers could not obtain the hidden rubric from the repository state
being tested.

Phase 10 establishes **documentation/operator usability only**. It does not
establish RF hardware execution, preprocessing reproduction, model reproduction,
figure reproduction, accepted-paper numerical reproduction, or correctness of
uninspected local-only runtime artifacts.

## Test protocol actually completed

Five independent blank chats were run against the same pinned tree:

1. `ITERATIVE_GIT_WORKFLOW`
2. `PIPELINE_ORCHESTRATION`
3. `LONG_RUNNING_SWEEP_RECOVERY`
4. `NEW_PA_JOURNAL_EXTENSION`
5. `DQNGUARD_LINEAGE_PROVENANCE`

Each chat started from the pinned `README.md` and was instructed to follow only
the repository's task routes and required owning/executable sources.

The first `PIPELINE_ORCHESTRATION` response missed one required rubric fact and
was therefore not silently accepted. A new independent blank-chat retest of that
case was performed against the same pinned commit.

## Initial evaluation

| Case | Score | Result | Critical failure |
|---|---:|---|---|
| `ITERATIVE_GIT_WORKFLOW` | 6/6 | PASS | none |
| `PIPELINE_ORCHESTRATION` | 5/6 | FAIL | none |
| `LONG_RUNNING_SWEEP_RECOVERY` | 6/6 | PASS | none |
| `NEW_PA_JOURNAL_EXTENSION` | 6/6 | PASS | none |
| `DQNGUARD_LINEAGE_PROVENANCE` | 6/6 | PASS | none |

The initial `PIPELINE_ORCHESTRATION` answer correctly recovered the mature
same-host capture architecture, deterministic-plan versus transport-shard
distinction, paired TX tape/spec contract, RAM-first/pre-touched capture,
quality-gated persistence, TX-index-driven resplicing, bank/relabel/cache
sequence, and historical BUH orchestration role.

It failed criterion 3 because it did **not explicitly state the actual mature
capture rate of 12.5 MS/s**.

That fact was already explicitly documented in `txrx/CONTEXT.md`: the mature
capture uses a 100-MHz master clock with integer interpolation/decimation factor
8, so the actual OTA rate is 12.5 MS/s and a 400,000-sample transport payload
spans 32 ms.

Therefore the initial miss was classified as:

`READER_ERROR`

not `DOC_DEFECT`.

No documentation correction was made before the retest.

### Initial access-trace observation

The first pipeline-orchestration reader also reported that a GitHub code-search
operation briefly surfaced an unpinned default-branch `bank_worker.m` snippet
while locating the file. The reader disclosed the incident, discarded that
snippet, fetched the complete file at the pinned commit, and stated that no
conclusion depended on the unpinned result.

This was retained as an audit observation rather than hidden. It did not trigger
a critical failure because the answer's substantive evidence was reread from the
required pinned tree.

## Pipeline-orchestration retest

A fresh blank chat reran only:

`PIPELINE_ORCHESTRATION`

against the unchanged validation target:

`0807d91d10b4baf6602442a83efdfdf4f19cc7d2`

The retest recovered all six required criteria.

In particular, it explicitly established:

- the dataset-generation plan as deterministic scientific/sample identity;
- transport sharding as packaging rather than semantic identity;
- paired TX tape and exact TX spec/`tx_index` authority;
- mature same-host `txrx_capture` / `capture_batch` ownership instead of the
  historical separate-TX/RX path;
- **100 MHz / 8 = 12.5 MS/s** actual OTA capture rate;
- a 400,000-sample OTA transport payload duration of 32 ms;
- campaign-specific RF/timing settings rather than universalizing old defaults;
- RAM-first/pre-touched TX/RX memory;
- no live disk writes in the RF hot loop;
- capture-event/fill quality gating before accepted persistence;
- exact TX-index evidence during resplicing;
- resplice → bank → global relabel → manifest → feature-cache ownership;
- artifact/content validation rather than filename/process-exit authority;
- historical BUH as architecture/provenance rather than a current one-click
  future-campaign executable;
- artifact-derived queues, worker pools, logs, retries, surgical resume, and
  small-pilot-before-scale operation.

The retest score was:

`PIPELINE_ORCHESTRATION | 6/6 | PASS | none`

No documentation patch was required to obtain that result.

## Final evaluation

```text
PHASE10_EVALUATION

Validation target:
0807d91d10b4baf6602442a83efdfdf4f19cc7d2

Case results:
ITERATIVE_GIT_WORKFLOW        | 6/6 | PASS | none
PIPELINE_ORCHESTRATION        | 6/6 | PASS | none
LONG_RUNNING_SWEEP_RECOVERY   | 6/6 | PASS | none
NEW_PA_JOURNAL_EXTENSION      | 6/6 | PASS | none
DQNGUARD_LINEAGE_PROVENANCE   | 6/6 | PASS | none

Failed-criterion evidence:
NONE

Classification:
NONE

Smallest correction:
NONE

Retest cases:
NONE

Overall:
PASS_DOCUMENTATION_ONLY

Runtime reproduction:
NOT ESTABLISHED
```

Final score: **30/30 rubric criteria**, with no critical failure in the accepted
case results.

## What Phase 10 establishes

At the tested tree, a new reader can start from `README.md` without a prior
handoff and recover the documented operating model for:

- safe ChatGPT ↔ terminal ↔ GitHub iteration;
- dirty-checkout/worktree/SSH/Jupyter safety;
- deterministic PA generation and physical acquisition architecture;
- same-host RAM-first OTA capture and provenance-aware resplicing;
- banking, global relabeling and feature-cache construction;
- long-running GPU sweep diagnosis and surgical recovery;
- incremental addition of a genuinely new PA;
- DQNGuard's VarMax / surrogate-open / DQN-IDS design lineage;
- current DQNGuard calibration semantics;
- the surviving 16,384 experiment lineage versus the accepted-manuscript
  8,192 provenance conflict.

The test therefore demonstrates that the repository context hierarchy is usable
for cold-start documentation/operator recovery at the tested commit.

## What Phase 10 does not establish

`PASS_DOCUMENTATION_ONLY` must not be upgraded into a runtime/scientific
reproduction claim.

Phase 10 did **not**:

- operate SDR hardware;
- generate a new RF collection;
- reproduce OTA captures;
- rerun resplicing, banking or cache construction;
- retrain a backbone;
- rerun DQNGuard or comparison methods;
- regenerate the Target–Surrogate numerical results;
- reproduce accepted-paper tables or figures;
- resolve the accepted-manuscript 8,192 statement by inventing an unobserved
  rerun;
- establish correctness of ignored/local artifacts that were not inspected.

Accordingly:

**Runtime reproduction: NOT ESTABLISHED.**

## Closure

No Phase-10 documentation defect remains demonstrated by the completed tests.
The one initial 5/6 result was successfully isolated as a reader miss because an
independent retest recovered the required fact from the unchanged documentation.

This closes Phase 10 and the context/operator refactor at the
**documentation-validation level**.

Future runtime reproduction, new-PA implementation, journal experiments and
paper reconciliation remain separate scientific/engineering tasks and must
retain their own provenance and validation.
