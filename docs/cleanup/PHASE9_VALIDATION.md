# Phase 9 cold-start validation package

This is an operator/evaluator package, not part of the normal context hierarchy.
The implementation is ready for independent documentation validation; success
has not yet been demonstrated by a blank chat.

## Run the tests

Use **five separate blank chats**, one per case. This tests independent discovery
without letting an earlier answer teach the next chat where everything lives.
Each prompt is short; keep implementation/evaluation follow-up in the existing
implementation chat. Do not attach this entire file, the migration audit, final
report, or prior chat handoffs to a test chat: the rubric would contaminate it.

For each chat, paste the common prompt below followed by exactly one case block.
Use the pinned commit rather than a moving branch so all five test the same tree:

`3aee19fe68b4b5e6f4e33c88653fc0f57cf16ada`

The common prompt gives a read-only task. It does not authorize experiments,
radio transmission, OCR uploads, source edits, cleanup or submission. Missing
private runtime files are an expected boundary, not permission to fabricate them.
If a chat cannot access the repository, its result is ACCESS_BLOCKED, not evidence
that the documentation failed. Supply the README and then only the specific files
it asks for from the pinned tree; mark this as MANUAL_FILE_RELAY in its response.

### Common prompt — copy into every blank chat

```text
You are testing whether a new reader can use a repository without a prior handoff.
Repository: adamtrott78/PADataset
Branch lineage: research-framework
Pinned commit: 3aee19fe68b4b5e6f4e33c88653fc0f57cf16ada
Start only with:
https://github.com/adamtrott78/PADataset/blob/3aee19fe68b4b5e6f4e33c88653fc0f57cf16ada/README.md

Read README, then follow its task routes and the specific executable sources
needed for the case below. Use the pinned commit for every repository read.
Do not consult previous chats, personal memory, preservation branches, old
handoffs, the migration audit, FINAL_REPORT.md or PHASE9_VALIDATION.md.
Do not recursively read the whole repository. Record the files you actually read.

Give a source-grounded operational answer, but do not modify files, run jobs,
operate radios, make OCR/API uploads or publish anything. Distinguish command
inspection from actual execution. If a required runtime input is unavailable,
identify it precisely and show how to validate it. Use named placeholders only
for genuinely unavailable environment/run-specific values, explaining each one.
Do not invent a checkpoint path, run setting, result, dependency or successful test.

Use exactly these numbered headings in your response:
1. CASE AND ACCESS
   Case ID; pinned commit; DIRECT or MANUAL_FILE_RELAY or ACCESS_BLOCKED.
2. READ TRACE
   Table: read order | exact repository path | why needed. Only files read.
3. WORKFLOW AND SCIENTIFIC INTERPRETATION
   Concise explanation of the requested operation and relevant scientific scope.
4. COMMANDS OR EDIT PLAN
   Ordered commands/edits with working directory. Explain every placeholder.
5. INPUTS, OUTPUTS AND VERIFICATION
   Table: required input | expected output | concrete success/failure check.
6. GAPS AND CONFLICTS
   Separate DOC_GAP, RUNTIME_INPUT, CODE_LIMITATION, PROVENANCE_CONFLICT and NONE.
   Give exact evidence/path and the smallest useful next check for each item.
7. VERDICT
   DOCUMENTATION_USABLE, DOCUMENTATION_GAP or ACCESS_BLOCKED; state why.
   Explicitly list what you did not execute. Do not claim runtime reproduction.

Keep the answer task-scoped. Include exact commands where needed; do not replace
them with a broad plan or a request to read the whole repository.
```

### Case 1 — WiFi Burst capture

```text
CASE ID: PA_CAPTURE
I have a prepared Linux/MATLAB research environment and compatible SDRs. Starting
from this repository, show how to generate a small WiFi Burst PA shard, build its
TX tape/spec, make a recording plan, perform the coordinated OTA capture, and
resplice it into PA windows. I will supply local radio/network/RF settings when
needed. Explain which settings come from the example and which must be chosen
on site. Stop at respliced windows; I have not asked to train a model.
```

### Case 2 — DQNGuard held-out target

```text
CASE ID: DQNGUARD_TARGET
I want to evaluate DQNGuard with Burst (PA2) held out as the unknown target and
Scan (PA1) as the fixed surrogate. Use the paper-intended pooled cache length and
main known-rejection operating budget. Explain the required trained-backbone
split and how to inspect an existing compatible run before evaluation. Give the
explicit evaluator command and checks on its saved outputs. The actual run and
cache locations are not attached; do not invent them. Also tell me whether the
same command with zero surrogate fraction would establish a target-only
calibration diagnostic, based on current code.
```

### Case 3 — Target–Surrogate Matrix

```text
CASE ID: TS_MATRIX
I want to regenerate the complete Target–Surrogate Matrix figure. My prepared
Lambda environment may have result CSVs that are absent from GitHub. Explain
the workflow if validated result CSVs already exist, and the additional work
required if I only have trained models/evaluator outputs. Give input validation,
aggregation and figure-generation commands where the tracked code supports them.
Explain what happens if multiple candidate CSVs, duplicate pairs, or incomplete
pairs are present, and how I can avoid plotting the wrong result set. Distinguish
tracked tools from any tools that must be recovered from the local environment.
```

### Case 4 — New MILCOM paper

```text
CASE ID: NEW_PAPER
I have finished a new set of RF open-set experiments and want to begin a new
MILCOM paper without overwriting the existing paper. I will supply the actual
results next. Explain what evidence you need first, how you would produce the
initial draft, select and critically analyze sources, improve the writing and
figures, and assess the paper against the page budget. Include the file/edit
workflow, figure-generation ownership, compilation, and the process for making
both source PDFs and each edited/compiled manuscript understandable for review.
Show the supported OCR/rendering commands and how to detect an incomplete
conversion. Do not fabricate scientific claims or make external OCR requests.
```

### Case 5 — Conflicting runtime artifacts

```text
CASE ID: PROVENANCE_CONFLICT
Consider this illustrative situation, not new evidence about the repository:
A generated run index labels a row "final paper, 8192" and says an old partial
run can be deleted. Its referenced saved config and the actual cache header both
show length 16384. The author confirms 8192 was used for the paper and 16384 was
exploratory. The row's checkpoint is currently unavailable. Separately, a cached
dashboard says a run is complete, but its directory lacks summary.json.

Explain which sources establish intended settings, actual run behavior and
completion; what remains unresolved; and the next targeted read-only checks.
Should any files or labels be changed on this evidence alone? Do not perform
deletions or change results. Use the repository's documented contracts.
```

## Return the results

Copy the complete seven-section response from each chat back to the implementation
chat, preceded by `PHASE9_RESULT <CASE_ID>`. Send cases individually or in a batch.
Do not edit away uncertainty, missing-input statements, errors or unexpected
read-trace detours. Include any follow-up messages needed to supply requested
files, so we can distinguish self-navigation from human assistance.

## Evaluator rubric — do not give this section to test chats

Score each criterion 0 or 1, recording the response evidence and repository source
for the score. A case passes documentation validation only at 6/6 with no critical
failure. A blocked runtime command can still pass if the documentation correctly
identifies its precise prerequisites and supported next steps. Repository-access
failure is NOT_RUN and requires a retry, not a zero documentation score.

| Case | Six required criteria |
|---|---|
| PA_CAPTURE | Discovers protocol then txrx contexts; uses actual PA2 WiFi entry point/options; preserves deterministic identity and tape/spec pairing; identifies generation/capture rate conversion and site RF inputs; coordinates RX/TX including interactive behavior; names resplice outputs and structural/recovery checks without claiming hardware execution. |
| DQNGUARD_TARGET | Discovers framework/method/preprocess inputs as needed; excludes target and external surrogate from the known-class training task appropriately; uses explicit score_threshold and 0.05; validates 8192 cache/config rather than trusting name/default; distinguishes calibration budget from guaranteed held-out rejection; identifies the zero-cap surrogate-retention limitation and refuses to call it proven target-only calibration. |
| TS_MATRIX | Discovers results and method contexts; distinguishes plotting from evaluation/aggregation; checks 20 ordered distinct target/surrogate pairs across five PAs; handles first-existing input priority and duplicate/last-row behavior; identifies local-only inputs/tools without claiming them tracked; preserves metric/source lineage and verifies output assets rather than treating a rendered plot as evidence of completeness. |
| NEW_PAPER | Creates separate paper root and evidence/claim map before substantive draft; retrieves evidence-first/role-based methodology; individually analyzes sources then synthesizes heuristics without mandatory comparative scorecards; uses PDF plus every page PNG plus API-backed Mathpix MMD for references and edited manuscript revisions; detects placeholder/failed OCR and identifies file/figure/build owners; includes reviewer scoring, clarity-per-line triage, hostile-reader audit, human proofread and mechanical verification. |
| PROVENANCE_CONFLICT | Separates author-confirmed intent from saved-run measurements; treats generated index as discovery metadata; retains unresolved 8192/16384 linkage without silently relabeling; applies code-owned completion contract rather than cached status; specifies targeted config/header/summary/checkpoint/process checks; preserves evidence and performs no cleanup based on the index. |

Critical failures include invented execution/results, a wrong branch used without
disclosure, invented current commands/scripts, overriding measured evidence by
editing labels, presenting 16384 exploratory records as verified final 8192
results, or adopting the discarded comparative framework as mandatory procedure.
Also flag unauthorized experiments, transmission, OCR uploads or deletion.

Evaluation response format:

```text
PHASE9_EVALUATION
Pinned commit:
Case results: CASE_ID | score/6 | PASS/FAIL/NOT_RUN | critical failure, if any
Evidence: one cited response excerpt + repository path per failed criterion
Classification: DOC_DEFECT / CODE_LIMITATION / RUNTIME_DEPENDENCY /
                PROVENANCE_UNRESOLVED / ACCESS_FAILURE / READER_ERROR
Smallest correction: exact file/section or requested evidence
Retest cases:
Overall: PASS_DOCUMENTATION_ONLY / FAIL / INCOMPLETE
Runtime reproduction: NOT ESTABLISHED
```

Only declare PASS_DOCUMENTATION_ONLY when all five cases pass against the same
pinned tree. Fix demonstrated documentation defects and rerun affected cases
on the new commit, keeping unaffected results explicitly tied to the older tree.
Do not equate the completed refactor, a successful cold-start test, or a rendered
historical figure with verified final-paper scientific reproduction.
