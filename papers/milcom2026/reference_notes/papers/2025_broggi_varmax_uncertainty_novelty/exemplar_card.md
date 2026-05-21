# Exemplar Card: varMax: Uncertainty and Novelty Management in Deep Neural Networks

## 1. Bibliographic Identity

Title: varMax: Uncertainty and Novelty Management in Deep Neural Networks
Authors: Alexandre Broggi, Nicholas Costagliola, Gaspard Baye, Nathaniel Bastian, Priscila Silva, Gokhan Kul
Venue:
Year: 2025
Length: longer paper
DOI / URL:
PDF slug: 2025_broggi_varmax_uncertainty_novelty
Citation status: cited

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; LAB_CONTINUITY; NEGATIVE_MODEL
Paper action labels: introduce_method; benchmark_methods

## 3. Why This Paper Is Included

This paper is included because it is a major varMax technical-lineage reference and gives a longer explanation of uncertainty, novelty, top-two confidence gaps, logit variance, and comparison to energy-based OOD methods.

## 4. Relation to Our Paper

DQNGuard inherits the confidence-evidence vocabulary and varMax comparison context, but should not inherit the full pacing or breadth of this paper. This reference is valuable for explaining why balanced known/unknown rejection matters and why confidence evidence is meaningful.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 0 | Not RF |
| OSR / OOD / calibration relevance | 3 | Direct |
| ML method similarity | 3 | Direct confidence-layer relation |
| Experimental setup similarity | 3 | Open-set fold evaluation |
| Operational / military / cyber relevance | 3 | Cyber/NIDS relevance |
| Total | 12 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 1 | Not our exact format |
| MILCOM / ComSoc / adjacent venue | 0 | Not MILCOM |
| Six-to-eight-page length | 1 | Less relevant |
| Similar figure/table density | 1 | Mixed |
| Similar reviewer audience | 3 | Cyber/ML overlap |
| Total | 6 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 2 | Useful but broad |
| Introduction flow | 1 | Long and repetitive |
| Method explanation | 2 | Useful for mechanics |
| Experiment explanation | 1 | Not our best model |
| Results narration | 1 | Secondary use |
| Figure/table design | 1 | Not primary use |
| Discussion/limitations | 1 | Not primary use |
| Total | 9 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | low | Technical lineage only |
| Introduction | medium | Balanced OSR framing |
| Related Work | high | Direct varMax lineage |
| Methodology | high | VarMax mechanics |
| Experimental Design | low | Less useful |
| Results | medium | Comparison language |
| Discussion | low | Not primary |
| Conclusion | low | Not primary |
| Figures | low | Not primary |
| Tables | low | Not primary |

## 7. Do Emulate

- Explain why unknown samples should not be missed and known samples should not be over-rejected.
- Use the known/unknown balance framing.
- Use the variance-confidence explanation when defining varMax lineage.
- Use this paper to justify why energy-based comparisons matter.

## 8. Do Not Emulate

- Do not adopt long literature-review pacing.
- Do not repeat closed-set softmax limitations multiple times.
- Do not include algorithmic detail beyond what the MILCOM paper needs.
- Do not let the method section become varMax documentation.

## 9. Useful Pages for Visual Analysis

Page 1: abstract and introduction.
Page 2: OSR definition and background.
Key method pages: VarMax execution and thresholding.
Key figure pages: VarMax diagrams.
Key table pages: benchmark/result tables.
Results pages: bias and performance comparison.
Discussion/conclusion pages: use selectively.

## 10. Extracted Heuristics

- The phrase balanced open-set recognition is useful, but must be operationalized.
- Longer technical lineage papers can support definitions without dictating paper structure.
- DQNGuard should state its improvement over varMax as calibration/threshold policy, not just another score.

## 11. Relevance to Our Current Revision

Use for related work and method-background precision. Avoid using it as a pacing model. It should help define what DQNGuard inherits and what it changes.

## 12. Decision

Decision: TECHNICAL_REFERENCE and SECTION_MODEL

Rationale: Important technical lineage, but weak fit for six-page MILCOM pacing.
