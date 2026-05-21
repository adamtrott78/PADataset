# Exemplar Card: Stealth Spectrum Sensing Data Falsification Attacks

## 1. Bibliographic Identity

Title: Stealth Spectrum Sensing Data Falsification Attacks Affecting IoT Spectrum Monitors on the Battlefield
Authors: Pedro Miguel Sánchez Sánchez, Enrique Tomás Martínez Beltrán, Alberto Huertas Celdrán, Robin Wassink, Gérôme Bovet, Gregorio Martínez Pérez, Burkhard Stiller
Venue: MILCOM-style / IEEE conference paper
Year: 2023
PDF slug: 2023_stealth_spectrum_sensing_data_falsification_milcom
Citation status: candidate cite / section model

## 2. Library Classification

Primary decision: SECTION_MODEL
Secondary decisions: PROBLEM_FRAMING_MODEL
Role tags: PROBLEM_FRAMING_MODEL; CLAIM_BOUNDARY_MODEL; RESULTS_NARRATIVE_MODEL; EXPERIMENT_DESIGN_MODEL
Paper action labels: diagnose_failure_mode; evaluate_detector_failure; bound_component_claim

## 3. Why This Paper Is Included

This paper is included because it is a strong failure-mode exemplar. It argues that existing SSDF detectors look promising under older attacks, but stealthier attacks manipulate spectrum data with reduced behavioral impact and evade detection.

## 4. Relation to Our Paper

This maps directly to our Target--Surrogate Matrix story. A calibration surrogate can appear useful, but failures emerge when the target unknown behavior differs from the surrogate. Our Figure 2 should be narrated as a failure analysis of a deployment assumption, not merely a heatmap.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Spectrum sensor attacks |
| OSR / OOD / calibration relevance | 1 | Detector failure under novel attacks |
| ML method similarity | 1 | Detection systems, not OSR |
| Experimental setup similarity | 2 | Sensor-level experiments |
| Operational / military / cyber relevance | 3 | Direct battlefield IoBT framing |
| Total | 10 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 3 | IEEE-style |
| MILCOM / ComSoc / adjacent venue | 2 | MILCOM-like RF/security setting |
| Six-to-eight-page length | 2 | Compact enough |
| Similar figure/table density | 2 | Good comparison table and algorithms |
| Similar reviewer audience | 3 | RF/cyber/defense overlap |
| Total | 12 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Strong failure claim |
| Introduction flow | 3 | Excellent battlefield sensing stakes |
| Method explanation | 2 | Attack algorithms are clear |
| Experiment explanation | 2 | Useful |
| Results narration | 3 | Strong detector-failure narrative |
| Figure/table design | 2 | Related work and algorithms useful |
| Discussion/limitations | 2 | Good claim boundary |
| Total | 17 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | failure-mode language |
| Introduction | high | battlefield sensing failure framing |
| Related Work | medium | RF sensor security |
| Methodology | low | attack algorithms not central |
| Experimental Design | medium | detector evaluation framing |
| Results | high | failure-analysis narrative |
| Discussion | high | component boundary and risk framing |
| Figures | medium | not primary |
| Tables | medium | compact related-work table |

## 7. Do Emulate

- State the operational failure mode plainly.
- Compare against existing methods under a harder condition.
- Use results to expose a deployment assumption.
- Keep the claim narrow: this is a detector/failure analysis, not a full battlefield system.

## 8. Do Not Emulate

- Do not overload our paper with algorithm boxes.
- Do not let related work dominate the early pages.
- Do not overfocus on attacks when our contribution is sensing/triage.

## 9. Extracted Heuristics

- Figure 2 should be described as surrogate-transfer failure analysis.
- Target-dependent surrogate behavior is a deployment risk, not just a numerical curiosity.
- The paper should distinguish optimistic calibration assumptions from deployable calibration assumptions.

## 10. Decision

Decision: SECTION_MODEL

Rationale: Strong problem-framing and results-narrative exemplar for explaining surrogate-transfer failures.
