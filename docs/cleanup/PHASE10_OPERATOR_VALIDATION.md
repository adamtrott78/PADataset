# Phase 10 operator and cold-start validation

This is an evaluator package, not part of the normal context hierarchy. It tests
whether the repository after the operating-architecture and scientific-provenance
corrections can be used by a new ChatGPT without a prior handoff.

The validation target is the exact repository tree at:

`0807d91d10b4baf6602442a83efdfdf4f19cc7d2`

That commit contains the documentation being tested. This Phase-10 package is
created afterward so the test chats cannot obtain the evaluator rubric from the
tested tree.

Phase 10 is documentation/operator validation only. It does not establish RF
hardware execution, model reproduction, accepted-paper numerical reproduction,
or correctness of local-only runtime artifacts.

## Test protocol

Use **five separate blank chats**, one per case. Do not allow one test response
to teach another where files live.

For every test:

- start only from the pinned README;
- use the pinned commit for every GitHub read;
- do not provide previous-chat context, personal memory, preservation branches,
  old handoffs, Phase 9/10 evaluator files, migration reports, or implementation
  chat summaries;
- do not recursively read the repository;
- record every repository file actually read;
- do not execute commands, modify files, operate radios, start jobs, upload OCR,
  delete artifacts, publish results, or submit a paper;
- distinguish inspected/proposed commands from commands actually executed;
- do not invent runtime paths, GPU state, checkpoints, datasets, caches, hardware
  settings, results, or successful validation;
- if a required local artifact is unavailable, identify exactly what is missing
  and give the smallest read-only validation needed on the prepared machine.

If direct repository access fails, classify the test as `ACCESS_BLOCKED`. Manual
relay of README and then only the files specifically requested by the test chat
is permitted, but the response must identify itself as `MANUAL_FILE_RELAY`.

## Common prompt

Paste this prompt into each blank chat, followed by exactly one case block.

```text
You are testing whether a new reader can operate a research repository without a
prior handoff.

Repository: adamtrott78/PADataset
Branch lineage: context-operator-refactor, descended from research-framework
Pinned commit: 0807d91d10b4baf6602442a83efdfdf4f19cc7d2

Start only with:
https://github.com/adamtrott78/PADataset/blob/0807d91d10b4baf6602442a83efdfdf4f19cc7d2/README.md

Read README, follow its task routes, and inspect only the owning contexts and
specific executable sources required for the case. Use the pinned commit for
every repository read.

Do not consult previous chats, personal memory, preservation branches, old
handoffs, migration reports, FINAL_REPORT.md, PHASE9_VALIDATION.md, or any
Phase-10 evaluator/rubric document. Do not recursively inventory the repository.

Give a source-grounded operational answer but do not modify files, run jobs,
operate radios, upload OCR/API data, delete artifacts, publish results, or submit
anything. A command that you inspect or propose is not evidence that it ran.

If a runtime input is unavailable, identify it precisely and give the smallest
read-only check needed on the prepared machine. Use placeholders only for
genuinely environment-specific values and explain each placeholder.

Use exactly these numbered headings:

1. CASE AND ACCESS
   Case ID, pinned commit, and DIRECT / MANUAL_FILE_RELAY / ACCESS_BLOCKED.

2. READ TRACE
   Table: read order | exact repository path | why needed.
   Include only files actually read.

3. OPERATING MODEL
   Explain the requested workflow, ownership boundaries, and relevant scientific
   or provenance distinctions.

4. COMMAND OR CHANGE PLAN
   Ordered operational plan and exact commands where supported. State working
   directory and explain every environment-specific placeholder.

5. AUTHORITY, INPUTS, OUTPUTS AND VERIFICATION
   Table: item | authoritative evidence | concrete validation/success/failure
   check. Separate observation aids from authoritative artifacts.

6. RISKS, GAPS AND CONFLICTS
   Classify each as DOC_GAP, CODE_LIMITATION, RUNTIME_INPUT,
   PROVENANCE_CONFLICT, OPERATOR_SAFETY, or NONE. Give the smallest next check.

7. VERDICT
   DOCUMENTATION_USABLE, DOCUMENTATION_GAP, or ACCESS_BLOCKED.
   Explicitly state what was not executed and whether runtime reproduction was
   established.

Keep the answer task-scoped. Do not replace exact supported operations with a
generic plan.
```

## Case 1 — iterative Git/operator workflow

```text
CASE ID: ITERATIVE_GIT_WORKFLOW

I have an existing Lambda checkout with unrelated dirty research work, and I want
ChatGPT to help make a bounded tracked source/documentation change without
damaging that checkout.

Explain the repository's recommended ChatGPT ↔ terminal ↔ GitHub loop from
initial state inspection through local execution/validation, diff review,
staging, commit, push, and post-push synchronization.

I frequently work over a long-lived SSH session and also have JupyterLab open in
another checkout. Explain the documented safety rules for strict Bash mode,
copy/paste code-fence failures, dirty checkouts/worktrees, narrow staging, and
determining which checkout a GUI is actually showing.

Do not make a source change. I want the operational protocol only.
```

## Case 2 — pipeline orchestration

```text
CASE ID: PIPELINE_ORCHESTRATION

I want to collect and preprocess a future RF campaign using the mature PADataset
architecture.

Starting from a deterministic generated PA collection, explain the supported path
through TX tape/spec construction, physical OTA capture, resplicing, banking,
global relabeling, and pooled feature-cache construction.

I may need hundreds of expensive shards/files. Explain how the historical BUH
production pipeline informs a future tracked orchestrator, but distinguish the
historical scripts from current executable owners. Explain same-host coordinated
capture versus the older separate-TX/RX path, RAM-first capture, artifact-driven
stage status, worker pools, retries/resume, and what constitutes evidence that a
capture/cache stage actually succeeded.

Do not operate radios or launch preprocessing.
```

## Case 3 — long-running experiment recovery

```text
CASE ID: LONG_RUNNING_SWEEP_RECOVERY

A large GPU training/evaluation matrix has been running for hours. Some rows
completed, several workers failed, one GPU lock pathname still exists, a dashboard
shows mixed DONE/ERROR state, and a few run directories are nonempty but missing
summary.json.

Explain how to determine what actually completed, what is merely observational
state, and how to recover only failed/missing work.

I do not want to delete a result root or blindly rerun the whole matrix. Explain
the role of manifests/configs, launcher/joblogs, worker logs, GPU/process checks,
lock semantics, canonical training artifacts, partial directories, and the fact
that the shared PyTorch trainer is not a general checkpoint-resume mechanism.

Do not run or delete anything.
```

## Case 4 — add a new PA for a journal extension

```text
CASE ID: NEW_PA_JOURNAL_EXTENSION

For a journal extension I want to add one genuinely new preliminary action to the
existing PA1/PA2/PA3/PA4/PA8 corpus.

Explain the safest scientific and implementation sequence from behavior
definition through generator support, deterministic planning, pilot generation,
transport/tape validation, OTA pilot, resplicing, banking/labels, cache
integration, and later experiments.

The original five PA data are expensive and already valid. Explain whether adding
one new PA inherently requires recapturing them.

Also explain how transport sharding relates to deterministic sample identity,
what the historical PA5/PA6/PA7 concepts mean, and why merely finding an old PA
identifier does not establish production support. Include leakage/split-hygiene
considerations and a small-pilot-before-scale strategy.

Do not invent the new behavior or change code.
```

## Case 5 — DQNGuard lineage and cache provenance

```text
CASE ID: DQNGUARD_LINEAGE_PROVENANCE

I need to understand what DQNGuard actually descended from before extending it for
a journal paper.

Recover the documented design lineage from earlier RF VarMax, predicted-class
variance/energy bands, surrogate-open experiments on the digital PA dataset,
the DQN-IDS confidence mechanism, the May 13–14, 2026 redesign, the initial fixed
PA1-surrogate DQNGuard experiments, and the later full Target–Surrogate Matrix.

Distinguish historical design rationale from the current executable DQNGuard
calibration/decision contract.

Then resolve this documentation question: the accepted manuscript reports pooled
length 8,192, while surviving experiment artifacts/configurations use 16,384.
Which statement should govern reproduction of the surviving experiment lineage?
What should remain recorded as a manuscript-provenance conflict?

Do not rewrite the paper or results.
```

## Return test responses

Return each complete seven-section answer to the implementation chat preceded by:

```text
PHASE10_RESULT <CASE_ID>
```

Do not edit away uncertainty, missing-input statements, read-trace detours, or
reported limitations. Include any manual file-relay messages if direct GitHub
access was unavailable.

## Evaluator rubric — do not give this section to test chats

Each case has six binary criteria. Score one point only when the response states
the distinction correctly and grounds it in the repository. A case passes at
6/6 with no critical failure.

### ITERATIVE_GIT_WORKFLOW

1. Starts from README and discovers repository-maintenance guidance without
   recursively reading unrelated subsystems.
2. Establishes branch, HEAD, dirty state and required runtime state before
   mutation; does not switch/clean/stash a dirty research checkout automatically.
3. Uses an isolated worktree when appropriate and warns that Jupyter/GUI paths can
   remain rooted in another checkout; trusts `pwd`, branch and HEAD.
4. Recovers bounded ChatGPT command blocks plus exact stdout/stderr/artifact return,
   and distinguishes inspected commands from executed commands.
5. Recovers code-fence integrity and child-Bash strict-mode safety; does not put
   `set -euo pipefail` into the persistent SSH login shell.
6. Uses explicit diff review, narrow `git add <reviewed paths>`, cached diff,
   commit/push, remote verification and ChatGPT reread of the pushed commit.

### PIPELINE_ORCHESTRATION

1. Distinguishes dataset-generation plan, historical recording-session plan and
   mature same-host coordinated physical capture.
2. Treats TX tape and exact TX spec/index as a pair and preserves deterministic
   sample identity independently of transport shard count.
3. Prefers current same-host `txrx_capture`/`capture_batch` ownership over the old
   separate TX/RX path; identifies actual 12.5 MS/s behavior and campaign-specific
   timing/RF settings.
4. Recovers RAM-first/pre-touch capture and rejects direct-to-disk hot-loop I/O;
   validates capture quality rather than raw-file existence alone.
5. Uses exact TX-index evidence during resplicing and follows resplice → bank →
   global relabel → cache with artifact/content validation.
6. Treats historical BUH as production provenance/design architecture, not a
   future one-click command; proposes tracked artifact-driven workerized recovery
   with missing-work queues and small-pilot validation.

### LONG_RUNNING_SWEEP_RECOVERY

1. Separates control plane, observation plane and scientific authority.
2. Uses manifest/config identity, worker/joblogs and GPU/process inspection
   together rather than trusting a dashboard.
3. Knows a lock pathname does not prove a live owner and does not remove a lock
   while a worker may hold it.
4. Applies the canonical shared PyTorch completion contract:
   `config.json`, `best_model.pt`, `final_model.pt`, `history.json`,
   `summary.json`.
5. Preserves failed/partial outputs and derives the exact incomplete identity set
   instead of deleting the whole result root.
6. States that `pa_train_one.py` is not general checkpoint resume and gives a
   reviewed targeted continuation/new-run strategy for blocked partial dirs.

### NEW_PA_JOURNAL_EXTENSION

1. Begins with behavior definition, novelty/leakage review and split hygiene before
   implementation.
2. Distinguishes planner support from generator/dispatch support and does not
   treat historical PA5/PA6/PA7 identifiers as implemented production classes.
3. Preserves deterministic dataset identity independently of transport sharding
   and uses a new collection identity for changed behavior/configuration.
4. Uses generator → small deterministic pilot → transport/header/tape/spec checks
   → OTA pilot → resplice/bank/label checks → scale.
5. Recognizes PA1 as precedent that a new PA can be acquired/integrated separately;
   old valid PAs do not inherently require recapture.
6. Preserves semantic labels/provenance while adapting physical partitioning and
   requires a clean combined cache/experiment view before new experiments.

### DQNGUARD_LINEAGE_PROVENANCE

1. Recovers predicted-class variance/energy guard ancestry from earlier RF VarMax
   rather than attributing every idea to DQN-IDS.
2. Recovers surrogate-open calibration as an idea developed during digital-PA
   VarMax testing and recognizes target-dependent transfer.
3. Recovers the DQN-IDS confidence-state contribution and that the direct DQN
   decision was inadequate as the sole PA OSR rule.
4. Identifies the May 13–14, 2026 VarMax + DQN-IDS synthesis, initial fixed
   PA1-surrogate/5%-budget DQNGuard stage, and later twenty-cell Target–Surrogate
   generalization.
5. Distinguishes historical rationale from current executable behavior: current
   predicted-class bands use known calibration, surrogate influences DQN fitting,
   and the final score cutoff is selected from known calibration.
6. Treats 16,384 as the surviving final experiment lineage and 8,192 as a
   late/accepted manuscript-provenance conflict lacking corresponding surviving
   rerun provenance; does not rewrite measurements to make them agree.

## Critical failures

A case fails regardless of score if it:

- invents execution, hardware success, model results, or unavailable runtime data;
- modifies/deletes data or launches a job despite the read-only prompt;
- recommends switching/cleaning/stashing the unrelated dirty Lambda checkout;
- enables strict `errexit` in the long-lived SSH login shell as the recommended
  ChatGPT workflow;
- advertises archived BUH or old separate-TX/RX orchestration as the current
  preferred physical workflow;
- treats dashboards/locks/markers alone as scientific completion authority;
- deletes broad result/cache roots as routine partial-work recovery;
- claims PA5/PA6/PA7 are production-ready merely because historical identifiers
  exist;
- labels the surviving 16,384 experiment chain exploratory in order to make the
  accepted 8,192 manuscript statement authoritative;
- claims the early DQNGuard architecture figure is itself the current executable
  Boolean/calibration specification.

## Evaluation record

Use this format when the five responses are returned:

```text
PHASE10_EVALUATION

Validation target:
0807d91d10b4baf6602442a83efdfdf4f19cc7d2

Case results:
CASE_ID | score/6 | PASS/FAIL/NOT_RUN | critical failure, if any

Failed-criterion evidence:
CASE_ID | criterion | response excerpt | repository path

Classification:
DOC_DEFECT / CODE_LIMITATION / RUNTIME_DEPENDENCY /
PROVENANCE_CONFLICT / ACCESS_FAILURE / READER_ERROR / NONE

Smallest correction:
exact owning context/source and required correction

Retest cases:
case IDs or NONE

Overall:
PASS_DOCUMENTATION_ONLY / FAIL / INCOMPLETE

Runtime reproduction:
NOT ESTABLISHED
```

Declare `PASS_DOCUMENTATION_ONLY` only if all five independent blank chats pass
6/6 with no critical failure. A successful documentation test does not establish
that radios, preprocessing, training, evaluation, figures, or accepted-paper
numbers were reproduced at runtime.
