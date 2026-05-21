# Exemplar Card: SpecForce

## 1. Bibliographic Identity

Title: SpecForce: A Framework to Secure IoT Spectrum Sensors in the Internet of Battlefield Things
Authors: Pedro Miguel Sánchez Sánchez, Alberto Huertas Celdrán, Gérôme Bovet, Gregorio Martínez Pérez, Burkhard Stiller
Venue: IEEE Communications Magazine / accepted version
Year: 2022
PDF slug: 2022_specforce_battlefield_spectrum_sensors
Citation status: candidate cite

## 2. Library Classification

Primary decision: SECTION_MODEL
Secondary decisions: CLAIM_BOUNDARY_MODEL
Role tags: PROBLEM_FRAMING_MODEL; CLAIM_BOUNDARY_MODEL; EXPERIMENT_DESIGN_MODEL; FIGURE_MODEL
Paper action labels: position_system_component; define_threat_model; evaluate_deployed_sensors

## 3. Why This Paper Is Included

This paper is included because it frames spectrum sensors as battlefield components that support monitoring, interception, decoding, and downstream services. It is valuable for claim boundaries: the paper proposes a security framework for spectrum sensors rather than claiming to solve all battlefield decision-making.

## 4. Relation to Our Paper

DQNGuard should be framed in the same component-oriented way. It is an RF sensing and triage layer for QR-CWoS, not a complete response planner, semantic labeler, or autonomous EW decision system.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Spectrum sensors and RF monitoring |
| OSR / OOD / calibration relevance | 1 | Detection/anomaly framing |
| ML method similarity | 1 | ML/DL detection, not OSR |
| Experimental setup similarity | 2 | Real devices and sensor data |
| Operational / military / cyber relevance | 3 | Direct IoBT/battlefield framing |
| Total | 10 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 2 | IEEE style but not MILCOM proceedings |
| MILCOM / ComSoc / adjacent venue | 2 | ComSoc adjacent |
| Six-to-eight-page length | 1 | Not the same pacing |
| Similar figure/table density | 2 | Useful framework and threat tables |
| Similar reviewer audience | 2 | RF/cyber/IoBT overlap |
| Total | 9 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Strong component summary |
| Introduction flow | 3 | Strong battlefield sensor motivation |
| Method explanation | 2 | Framework is clear |
| Experiment explanation | 2 | Real sensor deployment useful |
| Results narration | 2 | Use-case style reporting |
| Figure/table design | 2 | Useful threat/framework tables |
| Discussion/limitations | 2 | Good boundary for component role |
| Total | 16 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | component-level wording |
| Introduction | high | battlefield spectrum-sensor stakes |
| Related Work | medium | IoBT/spectrum sensor context |
| Methodology | medium | system module structure |
| Experimental Design | high | real sensor deployment framing |
| Results | medium | use-case evaluation structure |
| Discussion | high | claim-boundary model |
| Figures | high | architecture/framework model |
| Tables | medium | threat comparison model |

## 7. Do Emulate

- Describe the operational role of the sensing component.
- Separate the sensing layer from larger battlefield services.
- Define threat families and use cases clearly.
- Use real-device evaluation as credibility support.

## 8. Do Not Emulate

- Do not turn our paper into a broad IoBT framework paper.
- Do not claim QR-CWoS end-to-end response planning.
- Do not dilute the OSR contribution with too many security categories.

## 9. Extracted Heuristics

- Operational system papers become credible when they name what their component sees, emits, and supports.
- A battlefield framing works best when tied to concrete sensor tasks.
- Claim boundaries can strengthen a paper by making the contribution more precise.

## 10. Decision

Decision: SECTION_MODEL

Rationale: Strong operational and claim-boundary exemplar, but not the main six-page MILCOM pacing model.
