# MILCOM 2026 Paper Ground Truth

This file connects experiment evidence to LaTeX paper content. Do not add paper claims here unless they are confirmed from code, logs, metadata, result files, or explicit Adam confirmation.

## Confirmed dataset facts

| Field | Value | Evidence |
|---|---|---|
| Protocols | WiFi, Bluetooth, Zigbee | OTA file inventory and Adam confirmation |
| Paper-facing classes | Scan, Burst, Sustain, Hop, Replay | PA naming policy |
| Generated windows per protocol/action | 10,000 | Adam confirmation and shard policy |
| Burst/Sustain/Hop/Replay shards | 20 shards/protocol, 500 windows/class/shard | OTA spliced file inventory |
| Scan shards | 5 shards/protocol, 2,000 windows/shard | Adam confirmation and shard policy |
| Window samples | 400,000 complex I/Q samples | Representative spliced OTA metadata |
| OTA sample rate | 12.5 MS/s | Representative spliced OTA metadata |
| Window duration | 32 ms | 400,000 / 12.5e6 |
| Center frequency | 2.437 GHz | Representative spliced OTA metadata |
| TX/RX gain | 30/10 dB | Representative spliced OTA metadata and Adam confirmation |
| Radios | 2x Ettus USRP N210 | Adam confirmation |
| Daughterboards | SBX and CBX | Adam confirmation |
| Antennas | VERT2450 omnidirectional | Adam confirmation |
| Radio separation | approx. 11 inches | Adam confirmation |
| Switch | NETGEAR ProSAFE GS108 Gigabit | Adam confirmation |
| Workstation | Lambda Vector Pro | Adam confirmation |

## Confirmed model / training facts

| Field | Value | Evidence |
|---|---|---|
| Source type | OTA | run configs |
| Protocol tag | all | run configs |
| Dataset tag | ota_core_high_run01 | run configs |
| Cache length | 16,384 | run configs |
| Seed | 0 | run configs |
| Learning rate | 2e-4 | run configs |
| Entropy loss weight | 0.05 | run configs |
| Split mode | open_pa | data setup/configs |
| Known split | 70/15/15 train/validation/test | prep/eval config evidence |
| Open validation fraction | 15% | config evidence |
| Main known-reject budget | 5% | OSR eval commands/results |
| Calibration caps | 625 known / 625 open where applicable | OSR eval commands/results |

## Method definition

DQNGuard is a three-stage open-set decision layer that uses predicted-class conditional calibration, variance/energy evidence, and known-only budgeted thresholding to reject samples that do not conform to the learned known-class decision structure.

## Experiment regime definitions

### Regime A: Scan-surrogate method ablation

Fixed surrogate-open class is Scan. Target unknowns are Burst, Sustain, Hop, and Replay. Purpose: compare VarMax and DQNGuard under the same single-surrogate condition.

### Regime B: Target--Surrogate Matrix

One class is withheld as the target unknown, one different class is used as the surrogate-open calibration class, and the remaining three classes form the known set. Purpose: measure surrogate transfer structure.

### Regime C: Target-open calibration

A small labeled subset of the held-out target-open class is available for OSR calibration but not for closed-set backbone training. Use "target-open calibration", not "oracle calibration."

## Paper-facing replacements

### Replace old Research Questions in sections/4-experiments.tex

\begin{itemize}
    \item \textbf{RQ1.} Under a fixed Scan-surrogate calibration condition, does DQNGuard improve open-set preliminary-action detection relative to VarMax?
    \item \textbf{RQ2.} How sensitive is DQNGuard to the choice of surrogate-open class in the Target--Surrogate Matrix?
    \item \textbf{RQ3.} Does target-open calibration with 625 held-out target-open examples explain failures of surrogate-open calibration?
    \item \textbf{RQ4.} Can surrogate quality be predicted from calibration recall, confidence geometry, feature geometry, or route alignment diagnostics?
\end{itemize}

### Dataset paragraph candidate

The OTA corpus spans WiFi, Bluetooth, and Zigbee emissions and five preliminary-action classes: Scan, Burst, Sustain, Hop, and Replay. For each protocol/action pair, the generation target is 10,000 windows. Burst, Sustain, Hop, and Replay were generated together per protocol and split across 20 shards; each shard therefore contains 2,000 windows, or 500 windows per class. Scan was generated separately under the same seed schedule and capture setup and split across 5 shards of 2,000 windows. Each spliced OTA window contains 400,000 complex I/Q samples. At the recorded sample rate of 12.5 MS/s, this corresponds to a 32 ms analysis window.

### Hardware paragraph candidate

The OTA capture setup used two Ettus USRP N210 radios equipped with SBX/CBX daughterboards and VERT2450 omnidirectional antennas. The radios were separated by approximately 11 inches and connected through a NETGEAR ProSAFE GS108 Gigabit switch to a Lambda Vector Pro workstation. The captures used a 2.437 GHz center frequency with TX/RX gains fixed at 30/10 dB.

### DQNGuard method paragraph candidate

DQNGuard is a three-stage OSR decision layer placed on top of a closed-set backbone. First, it conditions calibration on the class predicted by the backbone rather than fitting a single global rejection model. Second, it computes variance/energy guard evidence, including top-two confidence gap, logit/feature variance, and energy-derived scores, and fits predicted-class percentile bands. Third, it converts the guard evidence into an unknown score and selects the final operating threshold from known calibration scores only. The main experiments use a 5% known-rejection budget, so the threshold is set at the 95th percentile of known calibration scores.
