# MILCOM 2026 Presentation Script

This file contains the spoken script for slides whose concepts are stable enough to narrate.

The script should remain conversational and clear. It is not intended to be read as a paper paragraph. Preserve the scientific claim boundaries in the slide plan.

---

# Slide 2 — Closed-set RF classifiers cannot say "I don't know"

## Target speaking time

Approximately **45-55 seconds**.

## Script

On the left is the conventional closed-set problem. If the receiver observes a behavior the classifier already knows, everything works as expected. A Burst is classified as Burst.

The problem is the second case. If genuinely unfamiliar RF behavior appears, the classifier still has to choose one of its existing labels. "Unknown" simply is not in its output space. And that prediction can still be made with high confidence.

What we want is the behavior on the right. Known observations should remain useful known classifications, while observations that do not fit the trained taxonomy should be routed as unknown.

That distinction matters because these classifications are intended to become evidence for downstream decision-making. A confidently mislabeled novel behavior can be more damaging than admitting that the system does not recognize what it is seeing.

So what exactly are the RF behaviors we're trying to recognize?

## Delivery notes

- Do not rush the two examples. Let the audience visually compare left and right.
- Stress **"Unknown simply is not in its output space."**
- The phrase **"Known observations should remain useful known classifications"** is important because it sets up the later known-rejection budget.
- Do not introduce DQNGuard yet.
- The final sentence is the direct transition to Slide 3.

---

# Slide 3 — Preliminary Actions capture RF behavior, not final attack labels

## Target speaking time

Approximately **55-65 seconds**.

## Script

The behaviors we're classifying are what we call Preliminary Actions, or PAs.

A Preliminary Action is not a final attack-technique label. It is observable RF behavior that may precede, enable, or contextualize a later cyber or Electronic Warfare attack technique. That makes it useful as precursor evidence for downstream reasoning, including MITRE ATT&CK-style reasoning.

In this work we evaluate five behaviors. Scan represents discovery-like RF activity. Burst is repeated short transmissions separated by quiet gaps. Sustain is persistent channel occupancy. Hop captures frequency-agile dwell and revisit behavior. And Replay captures repeated waveform or template structure.

The important distinction is the level of the claim. At this stage we're asking, "What behavior can I observe in the RF signal?" We're not yet claiming, "I know exactly what attack technique is occurring."

That makes these detections useful as precursor evidence for downstream reasoning while still preserving uncertainty where appropriate.

We evaluated this same behavioral taxonomy across WiFi, Bluetooth, and Zigbee.

To test that in the real RF environment, we built an over-the-air dataset spanning all three protocol families.

## Delivery notes

- Define **Preliminary Action** before using the acronym PA repeatedly.
- Stress that the labels describe **observable RF behavior**, not final ATT&CK/EW attribution.
- Use **cyber or Electronic Warfare attack technique** rather than the vaguer term `effect`.
- Do not imply that every PA literally occurs before an attack; preserve the broader "precede, enable, or contextualize" framing.
- Give each of the five behavior cards enough time for the audience to connect the label to its RF pattern.
- The final sentence is the direct transition to Slide 4.

---

# Slide 4 — We evaluate the same five behaviors over-the-air across three protocol families

## Target speaking time

Approximately **50-60 seconds**.

## Script

We evaluate these behaviors using over-the-air captures rather than treating this as a purely synthetic classification problem.

The dataset spans three protocol families: WiFi, Bluetooth, and Zigbee. For each protocol, we generate and capture the same five Preliminary Action behaviors—Scan, Burst, Sustain, Hop, and Replay.

That distinction is important. The label we're trying to recognize is the behavior, not the protocol itself. A Burst expressed through WiFi and a Burst expressed through Zigbee are different RF signals, but they represent the same behavioral class.

On the capture side, we transmit and receive using two USRP N210 software-defined radios at 2.437 gigahertz. Each classifier input is a 32-millisecond over-the-air RF window containing 400,000 complex IQ samples at 12.5 mega-samples per second.

So the open-set problem we're about to evaluate is grounded in captured RF across multiple protocol families rather than in a single waveform family.

With that dataset in place, the next question is how to decide when the classifier's prediction should actually be trusted.

## Delivery notes

- Stress **behavior, not protocol**.
- Keep hardware narration short; the point is OTA credibility, not acquisition-system detail.
- Use **USRP N210 software-defined radios**. Do not say "Ettus N210."
- Pause briefly on the 3 × 5 matrix so the audience registers that every protocol spans the same five behaviors.
- The final sentence transitions directly into the OSR decision-layer motivation.

---

# Slide 5 — Unknown detection is only useful if known behavior stays usable

## Target speaking time

Approximately **55-65 seconds**.

## Script

Once we have a closed-set PA classifier, the next problem is deciding when its prediction should be rejected.

We explored two useful directions that informed DQNGuard.

The first is VarMax. VarMax uses structure in the classifier outputs—including confidence, variance, and energy-style evidence—to assign an unknownness score and threshold that score. That gives us useful evidence for novelty, but the operating point still depends heavily on where that threshold is placed.

The second direction is a DQN-style confidence head. Here, features such as maximum softmax probability, the gap between the top two predictions, and entropy are treated as a confidence state, and a learned decision head chooses between known and unknown.

Both approaches are useful, but for our application there is one requirement we want to make explicit: detecting more unknowns cannot come at the cost of arbitrarily rejecting known Preliminary Actions.

So instead of asking only, "How well can I separate known from unknown?" we ask, "How well can I detect unknown behavior while staying inside a fixed known-rejection budget?"

That operating constraint is the central idea behind DQNGuard.

## Delivery notes

- Present VarMax and the DQN-style head as useful predecessors, not strawmen.
- Keep the DQN-style confidence state simple: `P1`, `P1-P2`, and entropy.
- Do not imply that the DQN-style diagram connects to the known-rejection-budget panel; they are separate conceptual panels.
- Stress the phrase **fixed known-rejection budget** at the end.
- Do not reveal Table I results yet.
- The final sentence transitions directly into Slide 6.

---

# Slide 6 — DQNGuard adds a budgeted open-world decision layer to the PA classifier

## Target speaking time

Approximately **65-75 seconds**.

## Script

That operating constraint is the central idea behind DQNGuard.

DQNGuard does not replace the PA classifier. The existing multi-domain backbone still takes the RF window, builds IQ, FFT, DCT, and polar representations, and produces the Preliminary Action prediction along with logits, softmax probabilities, and intermediate features.

DQNGuard sits on top of those outputs and asks a different question: does this prediction look like the kind of evidence we normally see for the class the backbone predicted?

It does that in three stages.

First, it conditions calibration on the predicted class, because what looks normal for one Preliminary Action may not look normal for another.

Second, it combines several forms of guard evidence—including confidence-gap, entropy, variance-style, and energy-style information—into a nonconformity score.

Third, it applies a threshold selected from known calibration data. In our main operating point, that threshold corresponds to a five-percent known-rejection budget.

So the final output is a routing decision. If the sample conforms, we keep the PA prediction as known evidence. If it does not, we preserve it as unknown behavior for downstream analysis rather than forcing it into the known taxonomy.

But this creates one more problem: if the true unknown has never been seen before, what open-set evidence do we use to calibrate that decision?

## Delivery notes

- Walk the hero figure **left to right**. Do not narrate every visual element at once.
- Make clear that the PA backbone remains the classifier; DQNGuard is the **decision layer**.
- Stress the three DQNGuard stages in order: predicted-class calibration -> guard evidence -> known-budget threshold.
- Explain the **5% budget** in plain language: only a controlled fraction of known calibration samples may be rejected at the operating point.
- Do not introduce surrogate terminology until the final question.
- Keep the downstream boxes in the narration brief; they reinforce system boundary, not the main algorithm.
- The final question is the direct setup for Slide 7.

## Visual asset

Use the final paper hero figure source:

`papers/milcom2026/figures/hero_figure/hero_dqnguard_pipeline_s22_tikz.tex`

Render/export this authoritative s22 source to a PowerPoint-safe vector asset. Do not substitute an older SVG revision.

---

# Slide 7 — A surrogate unknown shapes the DQN; the true unknown remains unseen until test

## Target speaking time

Approximately **70-80 seconds**.

## Script

There is one remaining problem with open-set calibration: if a behavior is genuinely unknown at deployment, then we cannot use labeled examples of that exact behavior to tune the detector ahead of time.

Our surrogate-open design handles that by withholding two behaviors from the backbone instead of one.

Here is a concrete example. Suppose Scan is the surrogate and Sustain is the true target unknown. The PA backbone is trained only on Burst, Hop, and Replay, so its output taxonomy contains just those three classes. Scan and Sustain are both completely absent from backbone training.

During OSR calibration, we pass Scan through that same three-class backbone. The backbone cannot predict Scan—it has never been trained to do that. Instead, Scan is forced into one of the known labels, and the resulting confidence states become surrogate-open evidence.

Those Scan-derived states are combined with known calibration states to fit the DQN confidence head.

The other DQNGuard pieces remain known-only: the predicted-class guard bands are fitted from known calibration, and the final five-percent operating threshold is selected from known calibration scores.

Only after that calibration do we evaluate on Sustain. Sustain has never been used for backbone training or OSR calibration, and Scan is not included in the final test metrics.

So the transfer question is: can open-set behavior learned from one withheld PA help us reject a different PA that remained genuinely unseen?

For the main comparison, Scan stays fixed as the surrogate while Burst, Sustain, Hop, and Replay each take a turn as the target unknown.

With that fixed-surrogate design, we can now ask whether DQNGuard gives us a better usable operating point than the existing OSR heads.

## Delivery notes

- Emphasize **one leave-two-out backbone**, not two models.
- When showing the concrete example, make clear that the backbone output space is only Burst / Hop / Replay.
- Stress that Scan is not expected to be classified correctly; its forced known-class confidence behavior is what makes it useful as surrogate-open evidence.
- State explicitly that the surrogate affects **DQN fitting**.
- State explicitly that guard bands and the 5% threshold are known-only in the current implementation.
- State explicitly that Scan is absent from the final evaluation.
- The final sentence transitions directly into Slide 8.

---

# Slide 8 — DQNGuard gives the strongest usable operating point at low known rejection

## Target speaking time

Approximately **80-90 seconds**.

## Script

Now we can look at the main comparison.

For this experiment, Scan is fixed as the surrogate condition, and Burst, Sustain, Hop, and Replay each take a turn as the genuinely unseen target. The numbers here are the mean and standard deviation across those four target folds, not across repeated random runs.

The horizontal axis is the operational cost we care about: how many legitimate known samples get incorrectly rejected as unknown. Lower is better. The vertical axis is Unknown F1, so higher is better. The ideal operating region is therefore the upper-left.

DQNGuard reaches an average Unknown F1 of 0.865 while rejecting approximately five percent of known samples. The DQN-IDS-style head reaches 0.701 Unknown F1 at 6.3 percent known rejection. VarMax reaches 0.745 Unknown F1, but at a substantially higher 12.8 percent known rejection.

DQNGuard also produces the highest OSR macro F1 at 0.881, which matters because that metric includes both the known classes and the unknown class.

There is an important caveat here. VarMax actually has the highest AUROC: 0.951 compared with 0.891 for DQNGuard. So VarMax is very good at ranking samples by unknownness.

But ranking quality and the quality of a deployed threshold are not the same thing. At the actual operating point, DQNGuard gives us the strongest combination of unknown detection and preservation of known PA evidence.

But that 0.865 average hides substantial target-to-target variation.

## Delivery notes

- Start with the experiment condition before discussing any number.
- Explicitly define both axes.
- Point out that the desirable operating region is **upper-left**.
- Credit VarMax for the highest AUROC.
- Do not say “DQNGuard wins everything.”
- State that the ± values are across **held-out target PAs**, not repeated seeds.
- Let the final sentence set up the target-dependent analysis on the next slide.

---

# Slide 9 — Surrogate usefulness depends strongly on the unseen target

## Target speaking time

Approximately **85-95 seconds**.

## Consolidated script

The previous slide gave us the main operating-point result: with Scan fixed as the surrogate, DQNGuard achieved an average Unknown F1 of 0.865 with a standard deviation of 0.142 across the four held-out target behaviors.

That variation is important. It is not instability from rerunning the same experiment. It means some target unknowns are simply much easier for this calibration scheme than others.

Figure 2 asks the broader question: what happens if we change the surrogate too?

Here, each row is the true target unknown, each column is the surrogate-open behavior used during calibration, and each cell reports Unknown F1. Because target and surrogate must be different behaviors, the diagonal is omitted.

The first thing to notice is that the best surrogate changes depending on the target. If Scan is the true unknown, Hop is the best surrogate at about 0.71 Unknown F1. If Burst is the target, Replay is best at about 0.61. For Sustain, Hop, and Replay targets, Scan is the strongest surrogate in this matrix.

The second thing to notice is how severe the mismatch can be. Several target-surrogate combinations fall to approximately zero Unknown F1. So this is not just a small tuning effect. A surrogate that gives useful open-set evidence for one target can provide almost no useful transfer for another.

That is the central result of this experiment: surrogate-open calibration is directional and target dependent. There is no universally best surrogate across all five Preliminary Actions.

One provenance detail is worth keeping straight. The fixed-Scan comparison on the previous slide and this full twenty-cell matrix come from distinct reviewed result chains, so I am not claiming that the Scan column here is numerically identical to the four folds used to compute 0.865 plus or minus 0.142. The previous slide establishes target-to-target variation under a fixed surrogate; this figure independently shows that changing the surrogate also materially changes performance.

So the remaining deployment problem is not just finding a surrogate — it is knowing whether that surrogate will transfer to the unknown we have not seen yet.

## Delivery notes

- Start by tying the slide directly to the **0.865 ± 0.142** result from Slide 8.
- Explicitly say that the SD is **across target PAs**, not repeated runs.
- Explain matrix orientation before interpreting any cell: rows are target unknowns, columns are surrogate-open classes.
- Use only a few representative cells verbally; do not read the entire matrix.
- Emphasize both conclusions: **best surrogate changes by target** and **some mismatched pairs nearly fail**.
- Preserve the provenance distinction between the fixed-Scan comparison and the final Target-Surrogate Matrix.
- Do not imply that near-zero cells prove the backbone itself is unusable; the claim is that the surrogate calibration evidence does not transfer well for those pairings.
- End on the deployment problem so Slide 10 can address whether the best surrogate can be predicted automatically.

---

# Slide 10 — No simple target-blind rule reliably predicts the best surrogate

## Target speaking time

Approximately **75-90 seconds**.

## Consolidated script

The matrix raises an obvious deployment question. If surrogate choice matters this much, can we predict which surrogate will transfer best before the real unknown ever appears?

We tested several plausible target-blind diagnostics.

The first was simply surrogate calibration performance. The intuition is straightforward: if DQNGuard does a good job rejecting a behavior while it is acting as the surrogate, maybe that behavior is a useful source of generic unknownness evidence.

It was not. The relationship with eventual target Unknown F1 was essentially zero, with a Spearman correlation of about negative 0.075 and a Pearson correlation of about negative 0.047. This rule selected the actual best surrogate for only two of the five targets.

We then looked at confidence geometry: changes in maximum softmax probability, the top-two probability gap, and entropy. Those relationships were negative overall. Our combined confidence-geometry score had a Spearman correlation of about negative 0.55 with target performance.

We also tested simple feature-space geometry. There were some positive signals, but even the best simple positive rule was weak—about 0.41 correlation—and selected the actual best surrogate for only one of the five targets.

So the important result is not that the matrix is random. It clearly is not. The result is that the structure was not captured reliably by these simple target-blind selection rules.

That leaves us with a deployment problem: if choosing one surrogate is fragile, and we cannot reliably know which one will transfer, the next step is to stop betting on a single surrogate.

## Delivery notes

- Frame this as a direct follow-up experiment to the Target–Surrogate Matrix.
- Explain each diagnostic as a simple deployment intuition before giving its result.
- Do not read every statistic mechanically; the important pattern is **no reliable target-blind selector**.
- State that these are exploratory diagnostics, not a production surrogate-selection algorithm.
- Do not claim the matrix is random or unstructured.
- End by motivating multi-surrogate calibration rather than dwelling on the negative result.

---

# Slide 11 — VarMax can search across surrogates; DQNGuard must learn how to combine them

## Target speaking time

Approximately **95-110 seconds**.

## Consolidated script

There is one more contribution that is important to this story because it directly motivates where we want to take DQNGuard next: VarMax surrogate-all.

VarMax surrogate-all uses one frozen backbone. During validation, each known class takes a turn acting as a pseudo-unknown. For each of those surrogate choices, VarMax searches candidate settings for the top-two probability-gap threshold and the predicted-class variance and energy bands. Those candidates also have to preserve the known-class performance constraints.

The key idea is that we do not choose one pseudo-unknown ahead of time. Candidates generated from all available surrogate classes compete in the same calibration search, and one final VarMax rule is selected.

That works naturally in VarMax because every candidate lives inside the same fixed decision architecture. The surrogate changes numerical thresholds and bands; it does not change the scoring function itself.

DQNGuard is different.

In DQNGuard, the surrogate-open confidence states are used to fit the DQN. So if I calibrate with Scan, I get one learned DQN score function. If I calibrate with Burst, I get a different one. If I calibrate with Hop, I get another one. The final five-percent threshold is then selected inside the score space produced by that fitted DQN.

So we cannot simply generate several DQNGuard thresholds and let them compete the way VarMax does. Those thresholds belong to different learned score spaces and are not directly interchangeable.

There is also a second difference. VarMax surrogate-all can temporarily repurpose classes the backbone already knows. In our current DQNGuard surrogate-open design, the surrogate itself is excluded from backbone training. If we tried to withhold several external surrogates at once, we would progressively shrink the known taxonomy—and with only five PAs, we very quickly stop having a useful closed-set classification problem.

That turns the future-work question into an architectural one: how do we combine several surrogate signals while retaining one coherent unknown score and the explicit known-rejection budget?

There are at least three directions worth testing. We could pool several surrogate-open state sets and train one DQN. We could train surrogate-specific DQNs and develop a principled normalization and aggregation rule. Or we could put the multi-surrogate logic into the VarMax-derived deterministic guard side while keeping one learned DQN confidence signal.

This is particularly interesting because VarMax surrogate-all gave us the strongest AUROC in the comparison, while DQNGuard gave us the stronger thresholded operating point.

So the goal is not to copy surrogate-all mechanically. The goal is to combine VarMax's multi-surrogate calibration philosophy with DQNGuard's strong Unknown F1, strong OSR F1, and explicit control over known rejection.

So the paper leaves us with both a working open-world detector and a concrete architectural question: how do we retain DQNGuard's operating-point advantage while learning from more than one kind of unknown?

## Delivery notes

- Treat **VarMax surrogate-all** as an original methodological contribution, not merely a baseline name.
- Explain the VarMax mechanism before introducing the DQNGuard incompatibility.
- Emphasize that surrogate-all selects **one final VarMax rule**; it is not an ensemble.
- The central architectural contrast is:
  - VarMax surrogate → different calibration parameters in one fixed scorer.
  - DQNGuard surrogate → different learned DQN scorer.
- State the second barrier: current DQNGuard external surrogates are withheld from backbone training, unlike VarMax's backbone-known pseudo-unknowns.
- Present pooled DQN, DQN ensemble, and hybrid guard designs explicitly as **future work — not evaluated**.
- Do not promise that multi-surrogate DQNGuard will reduce target dependence; frame that as the research hypothesis.
- End on the architectural question, then simplify aggressively on the final takeaway slide.

---

# Slide 12 — DQNGuard improves the operating point—but surrogate transfer remains the next challenge

## Target speaking time

Approximately **50-60 seconds**.

## Consolidated script

To close, there are three results I want you to take away from this work.

First, DQNGuard gives us a useful open-world operating point. Under the main fixed-surrogate experiment, it achieved an average Unknown F1 of 0.865 and an OSR macro F1 of 0.881 while keeping known rejection at approximately five percent. So we can expose unfamiliar RF behavior without solving the problem by throwing away the known evidence stream.

Second, the calibration problem is not solved. Across the twenty Target–Surrogate combinations, surrogate usefulness was strongly dependent on the actual unseen behavior. Some pairings worked very well, others nearly failed completely, and the simple target-blind selection rules we tested could not reliably predict the best surrogate.

Third, that gives us a concrete next research problem. VarMax surrogate-all shows how multiple pseudo-unknown behaviors can contribute to calibration when the decision architecture is fixed. DQNGuard gives us the stronger thresholded operating point, but its learned DQN makes multi-surrogate calibration an architectural problem rather than a simple threshold search.

Our next goal is therefore to combine those strengths: preserve DQNGuard's explicit known-rejection budget and strong unknown signal while learning from more than one kind of surrogate behavior.

And throughout this work, DQNGuard should be understood as an RF sensing and triage layer. It preserves known Preliminary Action evidence or routes unfamiliar behavior for downstream analysis; it does not make the final attack attribution or response decision.

Thank you.

## Delivery notes

- Slow down. This slide should feel simpler than Slides 8–11.
- Use the three visible columns as the speaking structure.
- On Column 1, point to the three metrics but do not re-explain the full comparison.
- On Column 2, summarize the Target–Surrogate conclusion rather than revisiting individual cells.
- On Column 3, frame multi-surrogate DQNGuard as a concrete research direction, not a completed result.
- Reinforce the system boundary once, clearly.
- End with **“Thank you.”** and leave the slide displayed for Q&A.

