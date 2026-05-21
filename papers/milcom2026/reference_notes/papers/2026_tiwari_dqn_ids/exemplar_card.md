# Exemplar Card: DQN-IDS: A Deep Reinforcement Learning Approach for Open Set-Enabled Intrusion Detection

## 1. Bibliographic Identity

Title: DQN-IDS: A Deep Reinforcement Learning Approach for Open Set-Enabled Intrusion Detection
Authors: Shreyash Tiwari, Nathaniel D. Bastian, Gokhan Kul
Venue: SDIoTSec / NDSS workshop
Year: 2026
Length: conference/workshop paper
DOI / URL:
PDF slug: 2026_tiwari_dqn_ids
Citation status: cited

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; LAB_CONTINUITY; NEGATIVE_MODEL
Paper action labels: introduce_method; evaluate_system_component

## 3. Why This Paper Is Included

This paper is included because it defines the DQN-style confidence-state decision head used as a comparison point for DQNGuard. It uses softmax-derived confidence metrics such as maximum probability, probability gap, and entropy to drive a learned known/unknown decision.

## 4. Relation to Our Paper

DQNGuard compares against a DQN-IDS-style head but does not claim deployment-time reinforcement learning as its main contribution. The paper is useful for explaining what a learned confidence-state OSR head is and why our known-budget calibration is different.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 0 | NIDS rather than RF |
| OSR / OOD / calibration relevance | 3 | Direct |
| ML method similarity | 3 | DQN-style decision layer |
| Experimental setup similarity | 2 | Open-set known/unknown testing |
| Operational / military / cyber relevance | 3 | Cyber/NIDS relevance |
| Total | 11 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 2 | Similar but not MILCOM |
| MILCOM / ComSoc / adjacent venue | 0 | Not MILCOM |
| Six-to-eight-page length | 2 | Somewhat comparable |
| Similar figure/table density | 1 | Mixed |
| Similar reviewer audience | 2 | Security/ML overlap |
| Total | 7 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 2 | Clear baseline idea |
| Introduction flow | 1 | Dense and repetitive |
| Method explanation | 2 | Useful confidence-state details |
| Experiment explanation | 1 | Not ideal |
| Results narration | 1 | Not primary |
| Figure/table design | 1 | Not primary |
| Discussion/limitations | 0 | Not primary |
| Total | 8 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | low | Baseline only |
| Introduction | low | Avoid pacing |
| Related Work | high | Direct DQN comparison |
| Methodology | medium | Confidence-state tuple |
| Experimental Design | medium | Baseline framing |
| Results | medium | Comparison interpretation |
| Discussion | low | Avoid broad deployment claims |
| Conclusion | low | Not primary |
| Figures | low | Not primary |
| Tables | low | Not primary |

## 7. Do Emulate

- Define the DQN state using P1, P1-P2, and entropy.
- Treat the DQN as a decision layer over CNN outputs.
- Use it as a contrast to static thresholding.
- Use it to justify why confidence-state baselines matter.

## 8. Do Not Emulate

- Do not overclaim real-time deployment unless directly supported.
- Do not repeat adaptive/scalable language without evidence.
- Do not let related work become a long sequence of method summaries.
- Do not frame DQNGuard as an RL system if the current paper evaluates it as a calibrated decision layer.

## 9. Useful Pages for Visual Analysis

Page 1: abstract and DQN-IDS motivation.
Page 2: related work and comparison framing.
Key method pages: confidence-state and DQN design.
Key figure pages: DQN-IDS flowchart.
Key table pages: architecture and split tables.
Results pages: known/unknown performance.
Discussion/conclusion pages: use cautiously.

## 10. Extracted Heuristics

- A DQN comparison should be described as an OSR decision head, not as the center of our contribution.
- Confidence-state features are interpretable and should be named clearly.
- DQNGuard should emphasize controlled known-rejection budget as its differentiator.

## 11. Relevance to Our Current Revision

Use this paper in Related Work and baseline explanation. It should not control the introduction or discussion style.

## 12. Decision

Decision: TECHNICAL_REFERENCE and SECTION_MODEL

Rationale: Important for DQN-style baseline framing, but not a strong prose model.
