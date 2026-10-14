# MILCOM 2026 DQNGuard - Final Presentation Script

Target: ~12:30-13:30 scripted, ~14-15 minutes live.

## Slide 1 - Title / operational hook (~25-30 s)

Good morning. I'm Adam Trott from UMass Dartmouth, and this work is DQNGuard: open-world RF Preliminary-Action detection.

The broader motivation is timing-sensitive cyber and electromagnetic-spectrum decision making. RF observations can become useful precursor evidence - but only if the sensing layer knows when it is looking at something outside its trained taxonomy.

So the question for this talk is simple: when an RF classifier sees behavior it has never learned, can it preserve that uncertainty instead of confidently inventing a known label?

Transition: To answer that, I first need to define the level of RF behavior we're trying to recognize.

## Slide 2 - Preliminary Actions capture RF behavior, not final attack labels (~60-70 s)

We use Preliminary Actions, or PAs, as a research taxonomy of RF-observable behaviors. This is not a claim that these five labels are a standardized EW attack ontology.

A Preliminary Action is observable RF behavior that may precede, enable, or contextualize a later cyber, EMS, or cyber-physical effect. The point is to capture useful precursor-level evidence before making a higher-level attack attribution.

The five behaviors in this study are Scan, Burst, Sustain, Hop, and Replay. Scan is discovery-like activity. Burst is short transmissions with quiet gaps. Sustain is persistent channel occupancy. Hop is frequency dwell and revisit behavior. Replay is repeated waveform or template structure.

The important claim boundary is at the bottom: this tells us what RF behavior we observe; it does not tell us the final attack technique.

In the larger QR-CWoS setting, that makes the sensing chain: RF observation, then behavioral evidence, then downstream cyber/EW or CWoS reasoning.

Transition: Once these behaviors become evidence, the dangerous failure is forcing unfamiliar behavior into one of them.

## Slide 3 - Closed-set RF classifiers cannot say "I don't know" (~50-55 s)

On the left is the closed-set problem. If the classifier sees a behavior it knows, a Burst can correctly remain Burst.

But if genuinely unfamiliar RF behavior appears, the classifier still has to choose one of its existing labels. Unknown simply is not in its output space, and a neural classifier can still make that forced prediction with high confidence.

The open-world requirement on the right adds one capability: preserve correct known classifications, but allow behavior outside the learned taxonomy to be routed as UNKNOWN.

That matters because these labels are evidence. A confidently false Hop or Scan can inject a false premise into downstream reasoning. UNKNOWN preserves ambiguity instead of fabricating certainty.

Transition: We evaluate that problem on real over-the-air RF, not just synthetic signals.

## Slide 4 - OTA dataset across three protocol families (~40-45 s)

We captured the same five behaviors over the air across WiFi, Bluetooth, and Zigbee.

The classification target is the behavior, not the protocol. A Burst expressed through WiFi and a Burst expressed through Zigbee are different RF realizations of the same behavioral label.

The capture path uses two USRP N210 SDRs at 2.437 gigahertz. Each classifier input is a 32-millisecond window containing 400,000 complex IQ samples at 12.5 mega-samples per second.

The key point is simply that the open-set problem is evaluated on captured RF across multiple protocol families.

Transition: The next question is what evidence we use to decide whether a closed-set prediction should be trusted.

## Slide 5 - VarMax and DQN-IDS lineages + operating requirement (~50-55 s)

These are the two direct technical lineages that informed DQNGuard; this is not meant to be an exhaustive survey of open-set recognition.

VarMax contributes deterministic, class-conditioned output-conformance evidence. In other words, if the backbone predicts Burst, do statistics like the output gap, logit variance, and energy look normal for samples predicted as Burst?

The DQN-IDS line contributes a learned confidence decision. Its state uses maximum softmax probability, the top-two probability gap, and entropy, and learns a known-versus-unknown confidence signal.

The raw DQN action was not reliable enough to be the sole final OSR rule. And a novelty detector is not useful if it catches unknowns by rejecting too many legitimate known samples.

So DQNGuard combines these ideas under an explicit operating requirement: detect unfamiliar behavior while controlling the cost to known behavior with a known-rejection budget.

Transition: The hero figure shows exactly where those pieces live.

## Slide 6 - DQNGuard architecture (~75-80 s)

[Pointer stop 1: backbone]
Everything before DQNGuard is the closed-set PA classifier. The RF window is represented in IQ, FFT, DCT, and polar domains, fused, and processed by the PA CNN.

[Pointer stop 2: outputs]
The backbone produces a predicted PA plus logits, softmax probabilities, and learned features. Those are evidence for the open-set layer.

[Pointer stop 3: DQNGuard]
DQNGuard has three conceptual stages. First, predicted-class calibration: what counts as normal depends on the class the backbone predicted. Second, it builds unknownness evidence. The learned DQN consumes P1, P1 minus P2, and entropy; class-conditioned band distances use gap, variance, and energy-style evidence. The combined continuous score is the DQN's unknown-versus-known preference plus class-conditioned nonconformity.

Third, we place the final cutoff using known calibration only. At the main operating point, beta equals 0.05, so the threshold is the 95th percentile of known calibration scores.

[Pointer stop 4: Known PA / Unknown]
This is where DQNGuard's evaluated output ends: retain the PA as known evidence, or route it as unknown behavior.

[Pointer stop 5: downstream boxes]
The rightmost boxes are downstream context or intended consumers. DQNGuard itself does not perform final ATT&CK attribution, attack-chain forecasting, label-making, or response planning.

Transition: That leaves one calibration problem: how do we learn anything about unknownness without using the true unknown itself?

## Slide 7 - Surrogate-open calibration (~75-85 s)

The true future unknown cannot participate in calibration without breaking the open-world assumption. So we use a different withheld behavior as surrogate-open evidence.

This example is the whole idea. Scan is the surrogate. Sustain is the actual target unknown. Burst, Hop, and Replay are the known taxonomy.

The three-class backbone is trained only on Burst, Hop, and Replay. Both Scan and Sustain are absent from backbone training.

During OSR calibration, known confidence states and Scan confidence states are combined to fit the DQN confidence head. Scan is not handed to the DQN as a supervised semantic label saying "this is unknown"; it shapes the confidence-state geometry used by the DQN calibration procedure.

The other pieces remain known-only: the predicted-class guard bands are fitted from known calibration, and the final 5% score cutoff is selected from known calibration scores only.

Sustain remains completely unseen until final evaluation, and Scan is not part of the final test metrics.

So the transfer question is: can unknownness structure learned with one withheld behavior help reject a different behavior that the system has never seen?

Transition: With Scan fixed as the surrogate, we can compare the resulting operating point against the baselines.

## Slide 8 - Main results (~65-75 s)

For this primary experiment, Scan is fixed as the surrogate and Burst, Sustain, Hop, and Replay each take a turn as the true target unknown. The error bars are across those held-out target folds, not repeated random runs.

The x-axis is known rejection - the operational cost - so lower is better. The y-axis is Unknown F1, so higher is better. The ideal region is the upper-left.

DQNGuard reaches an average Unknown F1 of 0.865 while rejecting about five percent of known samples. It also reaches an OSR macro F1 of 0.881.

VarMax surrogate-all has the strongest AUROC at 0.951, so it is very good at ranking samples by unknownness. But ranking quality and the quality of one deployed threshold are not the same thing. At the thresholded operating point shown here, DQNGuard gives the strongest combination of unknown detection and preservation of known PA evidence.

The 0.865 average also hides substantial target-to-target variation, which motivates the next experiment.

## Slide 9 - Target-Surrogate Matrix (~55-65 s)

Here's how to read the matrix. Rows are the actual unseen target behavior. Columns are the surrogate behavior used during calibration. Each cell is the resulting Unknown F1. The other three behaviors form the known backbone taxonomy for that cell.

For example, row Sustain and column Scan means Sustain is the true unknown, Scan is the surrogate, and Burst, Hop, and Replay are known.

The diagonal is blank because target and surrogate must be different behaviors. With five classes, that gives 5 times 4, or 20 ordered experiments.

Two things matter. First, the best surrogate changes with the target. Second, some mismatched pairings fall almost to zero Unknown F1.

So the correct interpretation is not that one surrogate is intrinsically good or bad. Transfer depends on the relationship among the target, the surrogate, and the remaining known taxonomy.

And because the target is unknown by definition, we now have a practical problem: can we predict which surrogate will transfer well before that target ever appears?

## Slide 10 - Target-blind diagnostics (~50-60 s)

We tested three intuitive target-blind ways to answer that question.

First: if I reject the surrogate well during calibration, does that imply it will transfer to the true unknown? Essentially no. Spearman rho is about negative 0.075, and Pearson r is about negative 0.047.

A quick note on rho: it is a rank-correlation coefficient from minus one to plus one; it is not a p-value. Near zero means the diagnostic ranking and actual target-performance ranking have almost no useful monotonic relationship.

Second, we tried confidence geometry using P1, P1 minus P2, and entropy. The combined diagnostic had rho around negative 0.552, so the intuitive rule actually tended to rank transfer in the wrong direction overall.

Third, we tried feature-space geometry. The best simple positive diagnostic reached rho around plus 0.406, but it selected the actual best surrogate for only one of five targets.

So the result is not that the matrix is random. It is that none of these simple target-blind proxies reliably tells us which surrogate will transfer best.

Transition: If choosing one surrogate is fragile and we cannot reliably predict the right one, the next question is whether we can stop betting on only one surrogate.

## Slide 11 - VarMax surrogate-all and multi-surrogate DQNGuard (~65-75 s)

VarMax gives us one clue. Its surrogate-all mode uses one frozen backbone and one fixed deterministic VarMax architecture. Different known classes take turns as pseudo-unknowns during calibration, generating candidate gap thresholds and variance/energy bands. All of those candidates compete, and one final rule is selected.

It is not an ensemble, and it does not average thresholds.

DQNGuard is harder. In DQNGuard, the surrogate participates in fitting the DQN itself. Scan gives one learned DQN score function, Burst gives another, and Hop gives another. Those are different nonlinear score spaces, so their numerical thresholds are not automatically interchangeable.

There is also a taxonomy problem: current DQNGuard withholds the external surrogate from backbone training, so simply withholding many surrogates at once would collapse a five-class known taxonomy.

That leaves three future architectures worth testing. One: pool multiple surrogate state sets into one DQN, giving one common score space. Two: train surrogate-specific DQNs, then normalize and aggregate their outputs into one score. Three: keep one DQN and move the multi-surrogate reasoning into the deterministic VarMax-style guard/calibration side.

None of these has been evaluated yet. The common goal is to reduce dependence on a favorable single surrogate while preserving DQNGuard's strong thresholded operating point and explicit known-rejection budget.

Transition: That brings us to the three takeaways.

## Slide 12 - Scientific takeaways (~40-45 s)

There are three things I want you to take away.

First, DQNGuard gives us a useful open-world operating point: 0.865 Unknown F1, 0.881 OSR macro F1, and about 0.050 known rejection in the main comparison.

Second, surrogate transfer is target-dependent, and the simple target-blind selection rules we tested do not reliably solve that problem.

Third, that turns multi-surrogate DQNGuard into a concrete architectural research question rather than a simple parameter-tuning exercise.

And the scope boundary is important: DQNGuard is an RF evidence-routing layer. It retains known Preliminary-Action evidence or routes unfamiliar behavior as unknown; it does not make the final attack attribution or response decision.

Thank you.

## Slide 13 - Questions / contact

No prepared narration. Leave displayed for Q&A.

Optional verbal line if appropriate after questions begin: "I'm also looking for Summer 2027 opportunities in RF, cybersecurity, and machine-learning research."
