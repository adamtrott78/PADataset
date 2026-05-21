# Exemplar Card: Searchlight

## 1. Bibliographic Identity

Title: Searchlight: An Accurate, Sensitive, and Fast Radio Frequency Energy Detection System
Authors: Richard Bell, Kyle Watson, Tianyi Hu, Isamu Poy, fred harris, Dinesh Bharadia
Venue: MILCOM
Year: 2023
PDF slug: 2023_searchlight_rf_energy_detection_milcom
Citation status: candidate cite / core exemplar

## 2. Library Classification

Primary decision: CORE_MODEL
Secondary decisions: SECTION_MODEL
Role tags: VENUE_STYLE_MODEL; PROBLEM_FRAMING_MODEL; METHOD_EXPOSITION_MODEL; EXPERIMENT_DESIGN_MODEL; RESULTS_NARRATIVE_MODEL; FIGURE_MODEL; CLAIM_BOUNDARY_MODEL
Paper action labels: overturn_naive_assumption; define_practical_requirements; position_system_component

## 3. Why This Paper Is Included

This is the strongest direct style exemplar in the batch. It opens by saying RF energy detection is often treated as solved, then explains why practical spectral monitoring is not solved: detection must localize energy in time and frequency, handle hardware impairments, work blindly, and support downstream classification.

## 4. Relation to Our Paper

DQNGuard should use the same rhetorical structure. Closed-set RF classification might appear solved, but practical OTA RF sensing for QR-CWoS is not solved because unknown behaviors must be routed as unknowns rather than forced into known PA classes.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Direct RF sensing |
| OSR / OOD / calibration relevance | 1 | Anomaly/unknown RF monitoring |
| ML method similarity | 1 | Supports downstream ML, not OSR |
| Experimental setup similarity | 3 | Synthetic and OTA RF data |
| Operational / military / cyber relevance | 3 | RF anomaly monitoring and SCISRS-style motivation |
| Total | 11 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 3 | Direct MILCOM style |
| MILCOM / ComSoc / adjacent venue | 3 | Direct MILCOM |
| Six-to-eight-page length | 2 | Close enough |
| Similar figure/table density | 3 | Strong RF pipeline figures |
| Similar reviewer audience | 3 | Very close |
| Total | 14 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Excellent practical failure framing |
| Introduction flow | 3 | Strong naive-assumption reversal |
| Method explanation | 3 | Stepwise system pipeline |
| Experiment explanation | 3 | Synthetic plus OTA evaluation |
| Results narration | 3 | Practical performance story |
| Figure/table design | 3 | Strong system/pipeline visuals |
| Discussion/limitations | 2 | Useful boundaries |
| Total | 20 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | high | practical RF sensing failure framing |
| Introduction | high | best intro model |
| Related Work | medium | RF detection context |
| Methodology | high | stepwise pipeline |
| Experimental Design | high | synthetic and OTA reporting |
| Results | high | practical RF result narration |
| Discussion | high | downstream component framing |
| Figures | high | system diagram model |
| Tables | medium | not the main table exemplar |

## 7. Do Emulate

- Start from a practical RF failure mode, not generic ML progress.
- Define what the system must output for downstream use.
- Treat the method as an enabler for later classification or monitoring.
- Explain why simple baselines fail in real RF conditions.
- Use a pipeline figure to structure the paper.

## 8. Do Not Emulate

- Do not go as deep into hardware-impairment processing as Searchlight does.
- Do not let the method section become a signal-processing implementation manual.
- Do not overclaim downstream classification if our paper only routes samples.

## 9. Extracted Heuristics

- The paper should explicitly state the operational product of DQNGuard.
- DQNGuard emits known PA evidence or unknown-behavior routing, plus guard evidence.
- Figure 1 should be referenced as the organizing structure of the methodology.
- Results should be narrated as practical operating behavior, not just metric tables.

## 10. Decision

Decision: CORE_MODEL

Rationale: Best direct RF/MILCOM writing and system-component exemplar for the DQNGuard paper.
