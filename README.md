# PADataset Research Framework

PADataset supports RF preliminary-action research: deterministic waveform
generation, over-the-air (OTA) capture, resplicing, feature caching, closed-set
training, open-set recognition (OSR), result analysis, and evidence-grounded paper
composition. Work on `research-framework` unless the task names another branch.

## Start here

Read this page, choose the task below, and load only its owning context and the
additional sources it names. Each context explains the model, executable owners,
inputs, commands, expected outputs, and verification limits. Inspect the relevant
code/configuration before changing a command or interpreting a default.

Before modifying an existing checkout, establish its state:

```bash
git branch --show-current
git log -1 --format='%H %s'
git status --short
```

The research machine has historically used
`~/adamArchives/Adam/varMax/PADataset`. A dirty or differently branched Lambda
checkout needs inspection before integration; see
[repository maintenance](docs/cleanup/CONTEXT.md). Do not switch it automatically
just because this page describes `research-framework`.

## Choose a task

| Task | Read first | Continue when needed |
|---|---|---|
| Generate a WiFi Burst PA shard; change a behavior or dataset plan | [PA generation](protocol/CONTEXT.md) | [OTA capture](txrx/CONTEXT.md) to build tapes, record and resplice |
| Capture generated RF over the air or recover captured windows | [OTA capture](txrx/CONTEXT.md) | [Banking and caches](scripts/preprocess/CONTEXT.md) |
| Build a bank, inspect PA labels, or create an 8,192-length cache | [Banking and caches](scripts/preprocess/CONTEXT.md) | [Experiment framework](experiments/CONTEXT.md) |
| Configure a run, add a run group, launch a matrix or recover a partial run | [Experiment framework](experiments/CONTEXT.md) | Method context below and [results](experiments/context/RESULTS.md) |
| Change training, inspect model dimensions, or load a checkpoint | [Backbone](experiments/context/BACKBONE.md) | [Experiment framework](experiments/CONTEXT.md) |
| Run DQNGuard with a held-out target and explicit 5% operating budget | [DQNGuard](experiments/context/DQNGUARD.md) | [Results](experiments/context/RESULTS.md) for matrix/table prerequisites |
| Evaluate VarMax or inspect its calibration sweep | [VarMax](experiments/context/VARMAX.md) | [Experiment framework](experiments/CONTEXT.md) |
| Train/evaluate the RF-adapted DQN-IDS comparator or distinguish its DQN head | [DQN-IDS adaptation](experiments/context/DQN_IDS.md) | [Backbone](experiments/context/BACKBONE.md) |
| Regenerate the Target–Surrogate Matrix or comparison table; trace a result | [Results and analysis](experiments/context/RESULTS.md) | [MILCOM paper tools](papers/milcom2026/CONTEXT.md) |
| Begin a new paper from experiment results or revise its argument | [Paper methodology](papers/CONTEXT.md) | [MILCOM paper tools](papers/milcom2026/CONTEXT.md) for reusable operations |
| Edit LaTeX/figures, compile, review sources or prepare an Overleaf package | [MILCOM paper tools](papers/milcom2026/CONTEXT.md) | [Paper methodology](papers/CONTEXT.md) for analysis and composition |
| Inspect ignored/local-only files, preserve source, or recover historical evidence | [Repository maintenance](docs/cleanup/CONTEXT.md) | The relevant subsystem context |

For a complete WiFi Burst capture, follow generation → capture; continue through
banking/caching only if model-ready inputs are part of the task. Regenerating a
plot from existing result CSVs and rerunning the experiments that produce those
CSVs are different workflows, both described by the results context.

## Scientific model

PA means **preliminary action / precursor RF behavior**. It is not a final cyber
technique label. The DQNGuard work spans WiFi, Bluetooth, and Zigbee:

| PA identifier | Behavior |
|---|---|
| PA1 | Scan |
| PA2 | Burst |
| PA3 | Sustain |
| PA4 | Hop |
| PA8 | Replay |

Other historical generator IDs do not automatically belong to this paper's
taxonomy. Experiment PA universes and label mappings are defined by the
experiment/preprocessing contexts and their code owners.

The shared RF backbone combines complementary I/Q, FFT, DCT, and polar
representations. Closed-set PA classification and open-set acceptance/rejection
are separate operations. DQNGuard uses predicted-class conditional calibration,
variance/energy guard evidence, and known-only budgeted thresholding. The main
paper operating budget is 5% known rejection during calibration; this does not
guarantee 5% rejection on held-out data. Select the documented mode and budget
explicitly rather than assuming evaluator defaults reproduce the paper.

Surrogate-open calibration is target dependent: one surrogate is not a universal
proxy for unknown behavior. Known PA evidence can support downstream reasoning;
rejected unknowns remain behavior candidates rather than being forced into a
known semantic class. DQNGuard is an RF sensing and triage component of QR-CWoS,
not the full response or semantic-labeling system.

The comparator adapted from the peer's DQN-IDS work uses an RF-adapted Keras
backbone. See its method context before assuming a comparison changes only the
decision head over one shared backbone.

## Environment and artifact boundaries

| Workflow | Environment needed |
|---|---|
| Waveforms, tapes, banking and resplicing | MATLAB and the toolbox/path setup described by the owner |
| Physical OTA capture | Compatible SDR hardware/support, site-specific RF settings and operator coordination |
| Caches and PyTorch experiments | Prepared Python environment, required datasets/caches, and compatible compute |
| Adapted DQN-IDS model | Its TensorFlow/Keras environment and model-specific inputs |
| Parallel launchers | GNU Parallel and the launcher's GPU/lock policy |
| Paper build and review | LaTeX/latexmk, PDF rendering tools, Python dependencies, and configured Mathpix OCR access |

The historical Python environment is `~/adamArchives/venvs/DNNs`; its existence
does not guarantee every workflow's dependencies. Check the owning context and
local environment before installing or upgrading packages.

GitHub contains the tracked portion of the research environment. Lambda can also
contain ignored datasets, tapes, caches, checkpoints, CSVs and uncommitted source.
The ignore rules are based on paths/extensions, not just size. A fresh checkout
is not a prepared experimental environment; establish required inputs before
promising a reproduction. Generated data can be essential evidence without
being normative documentation.

For implementation mechanics, inspect current executable source and effective
configuration. For a particular run, trace saved configuration, cache headers,
checkpoint/evaluator summaries and result provenance. If they disagree with an
intended setting or paper claim, report the discrepancy and investigate it.
Do not silently rewrite either side to make them match. Author-confirmed paper
pooling is **8,192**; recovered exploratory artifacts use **16,384**. The supplied
historical CSVs' connection to the final 8,192 results remains unresolved; see
[results provenance](experiments/context/RESULTS.md).

## Paper workflow and preserved history

The repository produced **DQNGuard: Towards Open-World RF Preliminary-Action
Detection**, accepted at MILCOM 2026. The successful writing methodology is
preserved in [papers/CONTEXT.md](papers/CONTEXT.md): ground truth, evidence draft,
role-based exemplars, individual analysis, heuristic synthesis, targeted writing,
reviewer scoring, clarity-per-line triage, hostile-reader audit, human proofread,
and mechanical verification. Reference papers and each newly compiled manuscript
revision are reviewed using the raw PDF, one PNG per page, and Mathpix OCR
Markdown together. A placeholder conversion is not a completed analysis package.

Create a separate `papers/<project>/` for a new paper. Preserve the accepted
`milcom2026-final-handin` snapshot and the pre-refactor
`context-pre-modularization` branch; use Git history to recover retired documents.
Historical notebooks, inventories, incident reports and exemplar analyses are
optional evidence, not a required startup reading list. Old handoffs, placeholder
READMEs and comparative-framework instructions do not govern current work.

Keep commands close to their code owner. Update that context when behavior
changes, and keep transient run/chat progress in commits, logs, run metadata or
task tracking. A documented command checked against source is not proof that
hardware execution, model training or final-paper reproduction has been tested.
