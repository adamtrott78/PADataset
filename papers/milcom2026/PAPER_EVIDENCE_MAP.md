> **Historical evidence.** Snapshot preserved from the pre-modularization paper records. Draft replacements, suggested next experiments and build expectations below are not current instructions. Author-confirmed final paper pooling is 8192; the recorded 16384 configurations describe recovered exploratory runs. Their linkage to final 8192 results remains unresolved. Comparative labels must be interpreted using the RF-adapted DQN-IDS context. Current workflow: [owning context](CONTEXT.md).

---

# OTA physical capture setup

The OTA recordings used two Ettus USRP N210 radios. One radio used an SBX daughterboard and the other used a CBX daughterboard. Each radio used a VERT2450 omnidirectional antenna. The radios were separated by approximately one sheet of US letter paper along the long edge, i.e., about 11 inches. TX gain was 30 dB and RX gain was 10 dB. Both radios were connected through a Netgear 1 GbE switch, which was connected to the Lambda Vector Pro workstation used for control/capture.

Paper-facing setup sentence:

The OTA capture setup used two Ettus USRP N210 radios, equipped with SBX/CBX daughterboards and VERT2450 omnidirectional antennas, connected through a Netgear 1 GbE switch to a Lambda Vector Pro workstation. The radios were separated by approximately 11 inches, with TX/RX gains fixed at 30/10 dB.

---

# OTA network hardware correction

The Ethernet switch used for the OTA capture setup was a NETGEAR ProSAFE GS108 Gigabit switch.

Updated paper-facing setup sentence:

The OTA capture setup used two Ettus USRP N210 radios, equipped with SBX/CBX daughterboards and VERT2450 omnidirectional antennas, connected through a NETGEAR ProSAFE GS108 Gigabit switch to a Lambda Vector Pro workstation. The radios were separated by approximately 11 inches, with TX/RX gains fixed at 30/10 dB.

---

# Target--Surrogate surrogate-selection analysis

The L2O terminology is deprecated for paper-facing writing. The paper should use **Target--Surrogate Matrix** or **TS matrix**.

We tested three candidate surrogate-selection rule families:

1. Guard-score calibration rule:
   - choose the surrogate with highest calibration-open recall at the known-only threshold.

2. Confidence-geometry rule:
   - choose the surrogate with stronger softmax uncertainty separation from known calibration samples, using P1, P1-P2 gap, and entropy.

3. Feature-geometry rule:
   - choose the surrogate based on nearest known-centroid distances and centroid-margin statistics in backbone feature space.

Result:
- Guard-score calibration recall did not predict target unknown F1.
- Confidence-geometry scores were negatively correlated with target unknown F1.
- Simple feature-geometry metrics gave only weak signal; the best positive metric was surrogate centroid-margin median, but it selected the true best surrogate for only 1/5 targets.

Conclusion:
The TS matrix shows that surrogate choice matters strongly, but simple calibration-recall, confidence-geometry, and centroid-distance rules do not yet provide a reliable automatic surrogate-selection policy. This supports treating surrogate selection as a nontrivial learned-geometry problem rather than a simple confidence-thresholding problem.

---

# Model, training, and calibration description draft

## Method name

The method name is **DQNGuard**.

Paper definition:

DQNGuard is a three-stage open-set decision layer that uses predicted-class conditional calibration, variance/energy evidence, and known-only budgeted thresholding to reject samples that do not conform to the learned known-class decision structure.

## Backbone training

The closed-set backbone is trained only on the known preliminary-action classes for each fold. The backbone outputs logits, softmax probabilities, predicted known labels, and intermediate features. These outputs are consumed by the OSR decision layer.

Current evaluated configuration facts:
- source type: OTA
- protocol tag: all
- dataset tag: ota_core_high_run01
- cache length: 16,384
- seed: 0
- learning rate: 2e-4
- entropy loss weight: 0.05
- split mode: open_pa
- known split: 70/15/15 train/validation/test
- open validation fraction: 15%

## DQNGuard stages

1. Predicted-class conditional calibration:
   DQNGuard groups calibration evidence by the class predicted by the backbone. This avoids using a single global rejection region for all known classes.

2. Variance/energy guard evidence:
   DQNGuard computes open-set evidence using softmax/logit and feature-derived statistics, including top-two probability gap, variance, and energy. Percentile bands are fit per predicted class.

3. Known-only budgeted thresholding:
   DQNGuard computes an unknown score and selects the final operating threshold from known calibration scores only. The main experiments use a 5% known-rejection budget, implemented as the 95th percentile of known calibration unknown scores.

## Relation to DQN-IDS

DQNGuard is related to DQN-IDS, which uses softmax-derived states P1, P1-P2, and entropy with centroid-guided DQN training. DQNGuard extends this idea by adding predicted-class conditional calibration, variance/energy guard bands, and deterministic known-rejection budgeting.

The paper should avoid claiming deployment-time continual learning unless a separate streaming update experiment is added. The uploaded DQN-IDS notebook supports validation-time DQN calibration/adaptation followed by held-out test evaluation.

## Experiment regime names

Regime A: Scan-surrogate method ablation.
- Fixed surrogate-open class: Scan.
- Target unknowns: Burst, Sustain, Hop, Replay.
- Purpose: compare DQNGuard against VarMax under the same single-surrogate condition.

Regime B: Target--Surrogate Matrix.
- One class is the target unknown.
- One different class is the surrogate-open calibration class.
- The remaining three classes form the known set.
- Purpose: measure surrogate-transfer structure and identify whether surrogate quality can be predicted.

Regime C: Target-open calibration.
- A small labeled subset of the held-out target-open class is available for OSR calibration but not for closed-set backbone training.
- Use the term target-open calibration rather than oracle calibration.

## Surrogate-selection follow-up

Rules A--C did not produce a reliable surrogate-selection rule. The next candidate is pseudo-target surrogate validation:

Pseudo-target surrogate validation estimates surrogate quality by repeatedly withholding one known class as a pseudo-unknown, calibrating with the candidate surrogate, and measuring whether the candidate surrogate produces a guard that rejects the pseudo-target while preserving the remaining known classes.
