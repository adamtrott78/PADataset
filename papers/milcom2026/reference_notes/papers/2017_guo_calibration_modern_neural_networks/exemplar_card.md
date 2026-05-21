# Exemplar Card: On Calibration of Modern Neural Networks

## 1. Bibliographic Identity

Title: On Calibration of Modern Neural Networks
Authors: Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger
Venue: ICML
Year: 2017
Length: conference paper
DOI / URL:
PDF slug: 2017_guo_calibration_modern_neural_networks
Citation status: should cite

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; TABLE_MODEL
Paper action labels: diagnose_failure_mode; benchmark_methods

## 3. Why This Paper Is Included

This paper is included because it provides the standard modern calibration framing: a confidence value should reflect the probability that the model's prediction is correct.

## 4. Relation to Our Paper

DQNGuard uses predicted-class calibration, but it is not merely confidence calibration. Guo et al. helps us distinguish calibrated confidence from unknown detection and avoid conflating accuracy, confidence, and OSR evidence.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 0 | Not RF |
| OSR / OOD / calibration relevance | 3 | Canonical calibration paper |
| ML method similarity | 2 | Post-hoc calibration over logits/probabilities |
| Experimental setup similarity | 1 | Different task |
| Operational / military / cyber relevance | 2 | Larger decision-pipeline framing transfers |
| Total | 8 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 0 | ICML format |
| MILCOM / ComSoc / adjacent venue | 0 | Not adjacent |
| Six-to-eight-page length | 1 | Short-ish but different format |
| Similar figure/table density | 1 | Good calibration figures |
| Similar reviewer audience | 2 | ML reviewers |
| Total | 4 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Very clear |
| Introduction flow | 3 | Excellent decision-pipeline framing |
| Method explanation | 3 | Strong definitions |
| Experiment explanation | 2 | Clear |
| Results narration | 2 | Good figure interpretation |
| Figure/table design | 2 | Reliability diagrams are strong |
| Discussion/limitations | 1 | Not primary |
| Total | 16 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | confidence reliability language |
| Introduction | high | larger decision-pipeline framing |
| Related Work | high | calibration reference |
| Methodology | high | calibration definitions |
| Experimental Design | medium | validation/calibration distinction |
| Results | medium | calibration-vs-accuracy logic |
| Discussion | medium | avoid overclaiming confidence |
| Conclusion | low | not primary |
| Figures | medium | reliability diagrams |
| Tables | medium | calibration tables |

## 7. Do Emulate

- Define calibration precisely.
- Distinguish accuracy from confidence reliability.
- Use examples where model outputs feed a larger decision process.
- Explain calibration before metrics.

## 8. Do Not Emulate

- Do not imply calibration alone solves OSR.
- Do not bring in ECE/MCE unless needed.
- Do not replace unknown-detection metrics with calibration metrics.

## 9. Useful Pages for Visual Analysis

Page 1: confidence calibration motivation.
Page 2: reliability diagram explanation.
Key method pages: definitions and metrics.
Key figure pages: calibration diagrams.
Key table pages: calibration method comparisons.
Results pages: temperature scaling results.
Discussion/conclusion pages: not primary.

## 10. Extracted Heuristics

- Calibration means confidence reflects correctness likelihood.
- A classifier can be accurate but miscalibrated.
- DQNGuard should not conflate calibrated probability with unknownness.

## 11. Relevance to Our Current Revision

Use this paper to tighten the language around predicted-class calibration and known calibration samples.

## 12. Decision

Decision: TECHNICAL_REFERENCE and SECTION_MODEL

Rationale: Essential calibration vocabulary and high-quality exposition, but not an OSR or RF style model.
