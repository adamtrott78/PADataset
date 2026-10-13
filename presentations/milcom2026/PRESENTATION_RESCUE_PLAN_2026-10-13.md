# MILCOM 2026 Presentation Rescue Plan — 2026-10-13

Status: **LOCKED FOR EXECUTION**

Purpose: prepare the MILCOM 2026 DQNGuard talk for a physical-layer jamming and defense audience under a 24-hour delivery constraint. This plan does not replace `PRESENTATION_PLAN.md`; it defines the bounded rescue/revision pass to apply to the existing presentation package.

## Success condition

A slide is complete only when all four conditions hold:

1. the scientific claim is defensible from PADataset evidence;
2. Adam can explain every visible object, number, and relationship in plain English;
3. the slide advances the previous slide's question and supports the end-to-end narrative;
4. the full talk remains deliverable in approximately 14–15 minutes, leaving margin inside the 20-minute session for questions.

The talk should let a technically competent MILCOM attendee answer:

1. What military/cyber sensing problem is being solved?
2. What is a Preliminary Action, and what is it not?
3. Why is open-set recognition useful specifically for Preliminary Actions?
4. What does DQNGuard do, including the surrogate-open mechanism?
5. What did the experiments establish, and what remains unsolved?

## Audience

Primary audience: MILCOM attendees in a Physical Layer Jamming and Defense session. Assume RF / communications / physical-layer security competence. Do not spend time motivating the electromagnetic spectrum generically. Spend that attention on the sensing/decision problem, open-world failure mode, and DQNGuard contribution.

## Locked narrative

### Slide 1 — Title / operational hook
Open with the sensing problem: if RF observations are being used as evidence for cyber/EW or CWoS reasoning, what happens when the sensor sees behavior outside its trained taxonomy?

### Slide 2 — Preliminary Actions + operational role
Preserve the PA-first order.

Reframe Preliminary Actions as a **research taxonomy of RF-observable behaviors**, not a standardized MITRE/NATO/EW ontology. Scan, Burst, Sustain, Hop, and Replay are intended as precursor/contextual RF evidence below final attack attribution.

Connect PA sensing to the larger CWoS use case early:

`RF observation -> behavioral evidence -> downstream cyber/EW / CWoS reasoning`

Explicit boundary:

`Preliminary Action != final attack-technique attribution`

### Slide 3 — Why open-set recognition
Plain-language definition:

- closed-set classification asks: which known behavior is this?
- open-set recognition adds: does this observation belong to any known behavior at all?

Operational consequence: a confident false PA label can inject false evidence into downstream reasoning; an UNKNOWN route preserves ambiguity for later analysis.

### Slide 4 — OTA dataset
Keep this concise. Establish that the same five behaviors were captured OTA across WiFi, Bluetooth, and Zigbee. Do not turn the slide into hardware trivia.

### Slide 5 — Design lineage, not exhaustive OSR survey
VarMax and DQN-IDS are the direct technical lines that motivated DQNGuard and the paper's principal comparison methods. Do not imply they exhaust the OSR literature.

Narrative:
- VarMax -> deterministic class-conditioned guard evidence.
- DQN-IDS -> learned confidence-state decision.
- deployment requirement -> explicit known-sample cost / rejection budget.
- DQNGuard -> synthesis.

### Slide 6 — DQNGuard hero figure
Keep the hero figure unless a minimal readability edit is required.

Laser-pointer route:
1. RF input + multi-domain PA backbone: "everything before DQNGuard is the closed-set PA classifier."
2. backbone evidence: predicted class, logits, softmax, learned features.
3. DQNGuard: predicted-class calibration -> guard evidence -> known-budget threshold.
4. evaluated output boundary: Known PA vs Unknown.
5. downstream consumer boxes are intended/theoretical consumers and related program research; DQNGuard itself does not perform final ATT&CK attribution, label-making, attack-chain forecasting, or response planning.

Teach lineage while pointing:
- DQN confidence signal comes from the DQN-IDS line.
- class-conditioned variance/energy guard logic comes from VarMax.
- the final operating point uses an explicit known-rejection budget.

### Slide 7 — Surrogate-open calibration
This is a central contribution and must be explained with one concrete fold.

Example:
- Scan = surrogate unknown.
- Sustain = target unknown.
- Burst/Hop/Replay = known taxonomy.

Core logic:
- the true unknown cannot be used to calibrate a detector that claims not to have seen it;
- therefore a different behavior is deliberately withheld and used as pseudo-open evidence;
- the surrogate influences **DQN fitting**;
- predicted-class guard bands are fitted on known calibration;
- the final 5% cutoff is selected from known calibration only;
- the target unknown remains unseen through training and surrogate-open calibration.

Do not repeat the early prototype rationale as if it were the current implementation.

### Slide 8 — Main result
Explain axes before interpreting methods:
- x-axis = cost: known samples rejected;
- y-axis = benefit: unknown-class F1;
- upper-left is preferable.

State DQNGuard's thresholded operating-point advantage while acknowledging that VarMax surrogate-all has the stronger AUROC. Do not say DQNGuard is best on every metric.

### Slide 9 — Target–Surrogate Matrix
Explain matrix orientation first.

For each cell:
- one PA = target unknown;
- one different PA = surrogate unknown;
- remaining three PAs = known taxonomy.

Interpretation should therefore emphasize the relationship among **known taxonomy, surrogate behavior, and target unknown**, not only an isolated surrogate-target pair.

### Slide 10 — Target-blind diagnostics
Teach the statistics before rehearsal:
- `rho` is Spearman rank correlation, not a p-value.
- Pearson `r` is a linear correlation coefficient, also not a p-value.
- rho ~= -0.075: essentially no monotonic relationship.
- rho ~= -0.552: moderate negative relationship; the confidence-space intuition tends to point the wrong way.
- best positive feature diagnostic rho ~= +0.406: some signal, still not a reliable selector.

Primary spoken conclusion:
**We tried three intuitive target-blind ways to pick a surrogate; none reliably selected the surrogate that transferred best to the unseen target.**

Correlation numbers may be visually de-emphasized if they create more explanation cost than value.

### Slide 11 — Multi-surrogate future architecture
Adam must understand the three candidate directions architecturally.

A. Pooled DQN:
`surrogate A/B/C -> pooled pseudo-open states -> one DQN -> one score space`

B. DQN ensemble:
`surrogate-specific DQNs -> normalization/aggregation -> unified unknown score`

C. Hybrid:
`multi-surrogate VarMax-style deterministic evidence + one DQN -> budgeted score`

Critical distinction:
VarMax surrogate-all does **not** average thresholds. It generates surrogate-specific calibration candidates within one fixed scorer, lets them compete, and selects one final rule.

DQNGuard cannot trivially copy this because a different surrogate changes the fitted nonlinear DQN score function, so separately fitted score spaces / cutoffs are not automatically interchangeable.

All three architectures are future work, not evaluated results.

### Slide 12 — Scientific close
Retain a calm three-part scientific close:
1. useful budgeted open-world operating point;
2. surrogate transfer remains target/taxonomy dependent;
3. multi-surrogate DQNGuard is the next architectural problem.

Reinforce system boundary once:
DQNGuard routes RF evidence; it does not perform final attack attribution or response.

### Slide 13 — Q&A / contact
Add a dedicated final Q&A slide rather than overloading the scientific conclusion.

Preferred title: **Questions?**

Include:
- Adam Trott
- UMass Dartmouth
- contact information / QR code if available
- restrained footer such as: **Seeking Summer 2027 opportunities in RF / cybersecurity / ML research**

Say "Thank you" verbally; do not make it the dominant slide title.

## Speaker-cue policy

Visible talking points are explicitly allowed when they reduce delivery risk.

Use them selectively as **jumping-off prompts**, not as a transcript.

Good uses:
- a 3-item phrase cluster that reminds Adam of the slide's required narrative;
- one short transition question at the bottom of a slide;
- a compact "known / surrogate / target" legend on Slide 7;
- a three-step label on the hero figure;
- a one-line interpretation next to a difficult statistic;
- an occasional bridge slide between dense content sections if a verbal transition is too easy to forget.

Avoid:
- paragraph-sized speaker notes on the visible slide;
- duplicating the full script;
- adding a cue merely because a slide can fit more text;
- introducing extra slides that consume time without changing audience understanding.

Decision rule:
**Add a visible cue only when it lowers the probability of missing an essential narrative point more than it increases visual load.**

Cue decisions will be made slide-by-slide during execution rather than forced uniformly across the deck.

## Timing

Do not target a 16:00 rehearsal.

Target:
- approximately 12:45–13:30 of deliberate scripted content;
- approximately 14:00–15:00 real delivery after pointer movement, transitions, and pauses;
- preserve the remainder of the 20-minute slot for questions.

## Execution waves

### Wave 1 — Truth + speaker understanding
Resolve all scientific/mechanical gaps before visual editing:
- PA / CWoS relationship;
- VarMax;
- DQN-IDS lineage;
- DQNGuard score and guard mechanics;
- surrogate-open calibration;
- Target–Surrogate semantics;
- diagnostic statistics;
- future-work architectures.

### Wave 2 — Narrative + script
Update the canonical slide plan and `SCRIPT.md` so every slide has:
- one audience takeaway;
- a speaking route;
- a transition;
- claim boundaries;
- target time.

Time the script before doing substantial layout work.

### Wave 3 — Minimal necessary visual changes
Prefer minimal visual mutation.

Expected highest-value edit candidates:
- PA/CWoS framing;
- baseline/design-lineage framing;
- surrogate-open explanation;
- Target–Surrogate semantics;
- target-blind diagnostic readability;
- Q&A/contact slide.

Preserve successful existing visuals whenever the narrative can be repaired through labels, cues, or narration.

Rebuild through the existing deterministic SVG/template/PPTX workflow and perform rendered visual QA.

### Wave 4 — Presentation-proofing
Three passes:
1. **content pass:** Adam can explain every visible object and number;
2. **timed pass:** full delivery <= ~15 minutes;
3. **hostile Q&A pass:** test likely questions that expose claim-boundary or mechanism confusion.

## Scope discipline

This is a rescue pass, not a new paper or an uncontrolled redesign.

Do not:
- invent new scientific claims;
- imply Preliminary Actions are a standardized EW ontology;
- imply VarMax/DQN-IDS exhaust OSR;
- imply downstream CWoS consumers are implemented by DQNGuard;
- revert current DQNGuard mechanics to early prototype semantics;
- claim future multi-surrogate architectures have been evaluated;
- trade away rehearsal time for low-value aesthetic polish.
