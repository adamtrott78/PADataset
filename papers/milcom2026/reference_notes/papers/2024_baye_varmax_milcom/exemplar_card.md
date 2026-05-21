# Exemplar Card: varMax: Towards Confidence-Based Zero-Day Attack Recognition

## 1. Bibliographic Identity

Title: varMax: Towards Confidence-Based Zero-Day Attack Recognition
Authors: Gaspard Baye, Priscila Silva, Alexandre Broggi, Nathaniel D. Bastian, Lance Fiondella, Gokhan Kul
Venue: MILCOM
Year: 2024
Length: short IEEE conference paper
DOI / URL:
PDF slug: 2024_baye_varmax_milcom
Citation status: cited

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: TECHNICAL_LINEAGE; VENUE_STYLE_MODEL; RESULTS_NARRATIVE_MODEL; NEGATIVE_MODEL
Paper action labels: introduce_method; benchmark_methods; evaluate_system_component

## 3. Why This Paper Is Included

This paper is included because it is the direct MILCOM predecessor for varMax-style confidence-based open-set recognition. It introduces the lineage of top-two softmax difference, logit variance, and energy-based OOD evidence used by later work in this project.

## 4. Relation to Our Paper

DQNGuard inherits part of its evidence vocabulary from the varMax lineage, but changes the decision structure. Our paper should treat Baye et al. as a technical ancestor and baseline reference, not as the final writing model. DQNGuard uses predicted-class calibration and a known-rejection budget to make the decision layer more controlled for RF preliminary-action sensing.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 1 | Cyber intrusion rather than RF, but OSR task is analogous |
| OSR / OOD / calibration relevance | 3 | Direct varMax and OSR lineage |
| ML method similarity | 3 | Confidence-layer method over DNN outputs |
| Experimental setup similarity | 3 | Open-set evaluation with known and unknown classes |
| Operational / military / cyber relevance | 3 | MILCOM and zero-day cyber framing |
| Total | 13 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 3 | Directly relevant |
| MILCOM / ComSoc / adjacent venue | 3 | MILCOM |
| Six-to-eight-page length | 3 | Directly relevant |
| Similar figure/table density | 2 | Useful but not ideal |
| Similar reviewer audience | 3 | Directly relevant |
| Total | 14 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 1 | Useful content but rough prose |
| Introduction flow | 2 | Correct broad movement but generic |
| Method explanation | 2 | Technically relevant but verbose |
| Experiment explanation | 1 | Less useful for RF paper |
| Results narration | 2 | Useful comparison framing |
| Figure/table design | 1 | Mixed |
| Discussion/limitations | 1 | Not the main strength |
| Total | 10 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | low | Technical lineage only |
| Introduction | medium | Useful closed-set to zero-day transition |
| Related Work | high | Direct predecessor |
| Methodology | medium | varMax evidence mechanics |
| Experimental Design | medium | Open-set comparison setup |
| Results | medium | Baseline comparison framing |
| Discussion | low | Not a strong limitation model |
| Conclusion | low | Avoid broad claims |
| Figures | low | Not a strong visual model |
| Tables | medium | Baseline comparison logic |

## 7. Do Emulate

- Move quickly from closed-set DNN failure to OSR motivation.
- State concrete components of the decision layer.
- Use the paper as a baseline and lineage anchor for varMax-style evidence.

## 8. Do Not Emulate

- Do not copy broad robustness or trustworthiness claims.
- Do not overuse generic cybersecurity motivation.
- Do not use long explanatory captions as a model.
- Do not let the method sound like it solves all zero-day detection.

## 9. Useful Pages for Visual Analysis

Page 1: abstract, introduction, contribution pacing.
Page 2: OSR background and early figures.
Key method pages: methodology figure and varMax decision logic.
Key figure pages: architecture and result figures.
Key table pages: results comparison tables if present.
Results pages: result and discussion pages.
Discussion/conclusion pages: use cautiously.

## 10. Extracted Heuristics

- MILCOM readers tolerate direct operational motivation, but contribution claims must stay bounded.
- A confidence-based OSR paper should state the closed-set failure mode before naming the method.
- A varMax derivative should distinguish its calibration/thresholding change from the original varMax logic.

## 11. Relevance to Our Current Revision

Use this paper to anchor related work and explain why DQNGuard is not merely reusing varMax. In the introduction, borrow the movement from closed-set failure to open-set decision need, but rewrite with stronger RF-specific precision.

## 12. Decision

Decision: TECHNICAL_REFERENCE and SECTION_MODEL

Rationale: Essential for lineage and baseline comparison, but not polished enough to serve as a broad prose exemplar.
