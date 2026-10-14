# MILCOM 2026 DQNGuard - Presenter Study Guide

Read this front to back before full-deck rehearsal. This is the conceptual version of the talk: it is deliberately more detailed than the speaker script so you can recover from a forgotten line or answer technical questions without memorizing wording.

## 1. CWoS -> Preliminary Actions -> OSR

### Mission-level motivation

QR-CWoS is the broader decision setting, not something DQNGuard itself creates. The relevant point is that timing-sensitive cyber/EMS reasoning benefits from early, uncertainty-aware evidence. RF sensing is one possible evidence source.

The causal chain for the talk is:

RF observation -> behavioral evidence -> downstream cyber/EW or CWoS reasoning.

DQNGuard lives at the sensing/evidence boundary.

### What a Preliminary Action is

A Preliminary Action is an observable RF behavior that may precede, enable, or contextualize a later cyber, EMS, or cyber-physical effect.

The five evaluated behaviors are Scan, Burst, Sustain, Hop, and Replay.

These five labels are a research taxonomy / operationally motivated behavioral abstraction. Do not present them as a standardized MITRE, NATO, or universal EW ontology.

The safe claim is:

PA = observable precursor-level RF behavior.

PA != final attack-technique attribution.

"Preliminary" does not mean every instance literally occurs before an attack. A PA may precede, enable, or contextualize later activity.

### Why OSR matters here

Closed-set classification asks: which known behavior is this?

Open-set recognition adds: does this observation belong to any known behavior at all?

Without OSR:

unfamiliar RF -> forced known label -> potentially false behavioral evidence downstream.

With OSR:

unfamiliar RF -> UNKNOWN -> ambiguity preserved for later analysis.

UNKNOWN does not mean "definitely malicious" or "new enemy attack." It means the sample does not conform to the known PA decision structure.

## 2. VarMax -> DQN-IDS -> DQNGuard

### Backbone first

The closed-set PA backbone processes an RF window and emits a predicted PA plus logits, softmax probabilities, and intermediate features.

OSR is a decision layer over those outputs.

### VarMax mental model

VarMax is deterministic output-conformance logic around the closed-set classifier.

Important evidence channels include:

- top-two softmax probability gap;
- logit variance;
- energy.

The top-two gap measures how decisively the classifier prefers its first choice over its second choice.

Logit variance measures dispersion in the absolute logits. Energy summarizes another aspect of raw logit geometry. These retain information that softmax alone can hide.

The key RF insight was that unknownness is not globally "high variance" or "low variance." Different predicted classes naturally have different output distributions.

So VarMax uses predicted-class-conditioned ranges: if the backbone predicts Burst, ask whether the evidence looks normal for things predicted as Burst.

Mental shortcut:

VarMax = deterministic class-conditioned guardrails around the classifier.

### DQN-IDS-style mental model

The inherited DQN confidence state is:

[P1, P1-P2, entropy]

where P1 is maximum softmax probability, P1-P2 is the top-two gap, and entropy measures how spread out the probability mass is.

The DQN outputs Q-values for unknown and known actions. These Q-values are not probabilities.

DQNGuard uses Q(unknown) - Q(known) as a learned unknownness signal.

This is offline/validation-time calibration. Do not describe the system as a deployment-time RL agent exploring the RF environment.

### Why combine them

The direct DQN hard action was not reliable enough as the sole final OSR rule. Confidence can also be misleading because unfamiliar neural-network inputs may still receive very high softmax confidence.

DQNGuard therefore combines:

- a learned DQN confidence signal;
- class-conditioned deterministic nonconformity evidence;
- an explicit known-only operating threshold.

### Exact current guard distinction

The DQN state contains top-two gap.

DQNGuard also fits predicted-class bands for top-two gap, logit variance, and energy.

In the `var_energy` hard-guard mode, the hard guard itself requires variance and energy to be inside their bands.

However, the continuous DQNGuard unknown score used by the 5% score-threshold workflow still includes normalized distances for gap, variance, and energy.

Therefore avoid the sloppy phrase "three hard guards." The safe phrasing is:

- DQN confidence state: P1, gap, entropy;
- VarMax-derived class-conditioned guard ancestry: especially variance and energy;
- continuous score: DQN Q-value difference + class-conditioned gap/variance/energy nonconformity.

### The known-rejection budget

The main DQNGuard operating point uses beta = 0.05.

The final cutoff is the 95th percentile of DQNGuard scores on known calibration samples.

Samples with scores at or above the cutoff are routed UNKNOWN.

This is a calibration operating point, not a mathematical guarantee that exactly 5.000% of held-out known test data will be rejected.

The scientific question is not "how many unknowns can I reject at any cost?" It is "how much unknown detection can I get under a controlled cost to known evidence?"

## 3. Surrogate-open calibration

### The core problem

If the true future unknown is used during calibration, it is no longer genuinely unseen.

So DQNGuard uses a different withheld behavior as surrogate-open calibration evidence.

### Concrete example

Surrogate = Scan.

Target unknown = Sustain.

Known taxonomy = Burst, Hop, Replay.

The backbone is trained only on Burst, Hop, and Replay. Both Scan and Sustain are absent from backbone training.

### What Scan does

Scan passes through the frozen three-class backbone and produces confidence states [P1, gap, entropy].

Known calibration states and Scan surrogate states are concatenated for DQN fitting.

The DQN-IDS procedure forms high-/low-P1 anchor regions and learns known/unknown confidence geometry from that mixed population.

Important precision: Scan is not simply fed in with a supervised semantic label that says "UNKNOWN." It shapes the confidence-state population and therefore the learned DQN geometry.

### What remains known-only

Predicted-class guard bands are fitted from known calibration only.

The final 5% numerical cutoff is selected from known calibration scores only.

The surrogate changes the fitted DQN and therefore changes the score space indirectly, but it does not directly choose the percentile cutoff.

Safe phrasing:

"The surrogate shapes the fitted scorer; the numerical operating threshold inside that score space is then selected from known calibration only."

### What Sustain does

Nothing until test.

Sustain is the true target unknown and remains unseen through backbone training and OSR calibration.

The final question is whether unknownness structure learned with Scan transfers to Sustain.

### Why this is not cheating

The explicit assumption is not "we have no open calibration evidence of any kind." The assumption is "we can have one out-of-taxonomy surrogate behavior, but we do not have labeled examples of the future target unknown."

The paper then tests whether surrogate-derived structure transfers to different unknowns.

## 4. Reading the Target-Surrogate Matrix

Burn this into memory:

ROW = target unknown.

COLUMN = surrogate-open behavior.

OTHER THREE = known backbone taxonomy.

CELL = Unknown F1.

Example: row Sustain, column Scan means target Sustain, surrogate Scan, known Burst/Hop/Replay.

The diagonal is invalid because target and surrogate must be different.

Five targets x four different surrogates = 20 ordered experiments.

### Why ordered matters

Target Sustain / surrogate Scan is different from target Scan / surrogate Sustain.

Even when the same three classes remain known, the role of the two withheld behaviors reverses: one shapes calibration and the other measures generalization.

### What a row means

One fixed target, different surrogate choices. But changing the surrogate also changes which remaining classes are known, so do not claim the row isolates surrogate identity perfectly.

### What a column means

One fixed surrogate across different target/known-taxonomy configurations.

### Correct scientific interpretation

Do not say "Scan is a universally good surrogate."

Say performance depends on the relationship among target unknown, surrogate-open behavior, and the remaining known taxonomy.

The matrix shows strong directional calibration transfer and several near-failure combinations.

## 5. Target-blind diagnostics

Slide 9 is retrospective: after running every pair, you know which surrogate worked best.

Deployment is prospective: the future target unknown has not appeared, so you need a proxy for surrogate quality that does not use the target.

That is what target-blind diagnostics attempt to do.

### Spearman rho

Spearman rho is a rank-correlation coefficient from -1 to +1.

+1: the diagnostic ranking and actual performance ranking match.

0: essentially no monotonic ranking relationship.

-1: the diagnostic ranking is reversed relative to performance.

rho is not a p-value.

Pearson r is also -1 to +1 but measures linear numerical association rather than rank association.

### Diagnostic 1: surrogate calibration performance

Question: if I reject the surrogate well, will I reject the true unknown well?

Result: rho about -0.075, Pearson r about -0.047, best-surrogate selection 2/5.

Interpretation: being easy to reject does not make a surrogate representative of a different future unknown.

### Diagnostic 2: confidence geometry

Question: does the surrogate look especially informative in the P1 / gap / entropy confidence space?

Result: combined rho about -0.552.

Interpretation: the intuitive rule tended to rank transfer in the wrong direction overall.

Do not claim causality. A plausible hypothesis is that a surrogate can be very geometrically distinct yet teach a form of novelty that does not resemble the future target.

### Diagnostic 3: feature geometry

Question: can the surrogate's position relative to known feature-space centroids identify a good transfer surrogate?

Best simple positive metric: rho about +0.406, but it selected the actual best surrogate for only 1/5 targets.

Interpretation: some signal may exist, but the simple feature metric is not reliable enough as a selector.

### Overall conclusion

The Target-Surrogate Matrix is not random. Rather, the simple target-blind proxies tested do not capture its transfer structure reliably enough to select one surrogate prospectively.

## 6. VarMax surrogate-all and multi-surrogate DQNGuard

### VarMax surrogate-all

VarMax surrogate-all uses one frozen backbone and one fixed deterministic decision architecture.

Known classes take turns as pseudo-unknowns within calibration/validation score subsets.

Each pseudo-unknown choice generates candidate gap thresholds and predicted-class variance/energy band settings.

Candidates from all surrogate specifications compete in the same search. One final rule is selected.

It is not a deployed ensemble.

It does not average thresholds.

The pseudo-unknown class remains a backbone-known class in this VarMax procedure; it is only treated as pseudo-open for the calibration search.

### Why it does not port directly to DQNGuard

Current DQNGuard uses an external surrogate that is excluded from backbone training.

More importantly, the surrogate participates in DQN fitting:

Scan surrogate -> DQN A.

Burst surrogate -> DQN B.

Hop surrogate -> DQN C.

These are different learned nonlinear score functions. A score or cutoff from DQN A is not automatically comparable to the same numeric value in DQN B.

Also, with only five PAs, withholding many external surrogate classes at once would rapidly collapse the known backbone taxonomy.

Therefore multi-surrogate DQNGuard is an architectural problem, not a simple switch that reuses VarMax surrogate-all.

### Option A: pooled multi-surrogate DQN

Pool confidence states from multiple surrogate behaviors and fit one DQN.

Advantage: one learned score space; the known-only 5% threshold concept remains straightforward.

Risk: heterogeneous surrogate geometries may blur a strong single-surrogate signal.

### Option B: surrogate-specific DQN ensemble

Fit one DQN per surrogate and aggregate their outputs.

Advantage: preserve specialized surrogate-specific novelty signals.

Problems: normalize incompatible score spaces, choose an aggregation rule, and recalibrate one global known-rejection budget.

### Option C: hybrid VarMax / DQNGuard

Keep one learned DQN confidence signal and place multi-surrogate reasoning in the deterministic VarMax-style guard/calibration side.

Advantage: deterministic candidate evidence is easier to compare while preserving one learned DQN score function.

This is conceptually natural because DQNGuard was already created by combining DQN confidence evidence with VarMax-derived guards.

All three are future work. Do not claim they were implemented or evaluated.

## 7. Final scope and takeaways

The three scientific takeaways are:

1. DQNGuard gives a useful thresholded open-world operating point under controlled known-sample cost.
2. Surrogate transfer is directional and target/taxonomy dependent, and simple target-blind selectors were not reliable.
3. Multi-surrogate DQNGuard is the next architectural problem.

The most important scope sentence:

"DQNGuard decides whether to retain an RF observation as known PA evidence or route it as unknown; it does not make the final attack attribution or response decision."

DQNGuard does not itself:

- identify the final ATT&CK/EW technique;
- determine the full attack chain;
- generate the final semantic label for novel behavior;
- predict the complete CWoS;
- select a response action;
- autonomously perform EW response planning.

Those are downstream consumers / related system context.

The contribution is evidence integrity at the RF sensing layer:

without OSR: novel behavior -> forced known PA -> potentially false evidence.

with DQNGuard: novel behavior -> UNKNOWN -> ambiguity preserved.

## 8. Fast Q&A rescue answers

### "Are Preliminary Actions standardized?"

No. In this work they are a research taxonomy of observable RF behaviors intended as precursor-level evidence, not a standardized final EW attack ontology.

### "Does UNKNOWN mean malicious?"

No. It means the sample does not conform to the known PA decision structure. Cooperative radios, protocol variants, channel/hardware effects, or genuinely novel adversarial behavior can all be outside the training distribution.

### "What did DQNGuard inherit from VarMax?"

Predicted-class-conditioned output-conformance logic, especially variance/energy guard reasoning, plus the project's surrogate-open calibration lineage.

### "What did it inherit from DQN-IDS?"

The learned confidence-state decision over P1, top-two gap, and entropy. DQNGuard uses the DQN's Q-value difference as one unknownness signal rather than trusting the hard DQN action alone.

### "Is 5% rejection guaranteed at test time?"

No. Five percent is the calibration operating point. Held-out test rejection can differ because of finite samples, ties, interpolation, and distribution shift.

### "Why not calibrate on the actual target unknown?"

That becomes target-open / oracle-style calibration and violates the deployment assumption that the future target has not yet been observed. It is useful diagnostically but not the open-world condition being claimed.

### "Why Scan as the main surrogate?"

It was the fixed external surrogate used to establish the primary method comparison. The later Target-Surrogate Matrix explicitly tested whether that choice generalized and showed surrogate quality is target-dependent.

### "Why show diagnostics that failed?"

Because the matrix exposes a practical sensitivity. If a trivial target-blind proxy solved surrogate selection, that would largely resolve the limitation. Testing the obvious proxies and finding them insufficient shows that the selection problem is genuinely nontrivial.

### "Why can't you just use VarMax surrogate-all in DQNGuard?"

VarMax compares parameter candidates inside one fixed deterministic scorer. In DQNGuard, changing the surrogate changes the fitted nonlinear DQN score function, so separately fitted score spaces are not directly interchangeable.
