# Exemplar Card: Towards Open Set Deep Networks

## 1. Bibliographic Identity

Title: Towards Open Set Deep Networks
Authors: Abhijit Bendale, Terrance E. Boult
Venue: CVPR
Year: 2016
Length: conference paper
DOI / URL:
PDF slug: 2016_bendale_open_set_deep_networks
Citation status: should cite

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; PROBLEM_FRAMING_MODEL
Paper action labels: introduce_method; define_problem; diagnose_failure_mode

## 3. Why This Paper Is Included

This paper is included because it is the canonical deep-network OSR reference. It explains why softmax-based deep networks are closed-set systems and introduces OpenMax as a post-hoc layer for unknown rejection.

## 4. Relation to Our Paper

DQNGuard is not OpenMax, but it shares the same broad structure: a closed-set backbone produces internal outputs, and an OSR decision layer uses those outputs to decide whether to retain a known label or reject the input as unknown.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 0 | Vision domain |
| OSR / OOD / calibration relevance | 3 | Deep OSR canonical paper |
| ML method similarity | 3 | Post-hoc decision layer over neural outputs |
| Experimental setup similarity | 2 | Unknown-class evaluation transfers |
| Operational / military / cyber relevance | 3 | Deployment unknowns transfer |
| Total | 11 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 2 | CVPR two-column |
| MILCOM / ComSoc / adjacent venue | 0 | Not MILCOM |
| Six-to-eight-page length | 1 | Longer than target |
| Similar figure/table density | 1 | Dense |
| Similar reviewer audience | 1 | ML audience |
| Total | 5 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Very strong problem-method-result abstract |
| Introduction flow | 3 | Strong closed-world failure framing |
| Method explanation | 3 | Useful staged method exposition |
| Experiment explanation | 2 | Useful but vision-specific |
| Results narration | 2 | Strong comparison framing |
| Figure/table design | 1 | Figure is informative but dense |
| Discussion/limitations | 1 | Not primary |
| Total | 15 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | high | problem-method-result shape |
| Introduction | high | softmax failure and open-world deployment |
| Related Work | high | canonical deep OSR reference |
| Methodology | high | decision-layer over backbone outputs |
| Experimental Design | medium | unknown-class protocol |
| Results | medium | compare softmax thresholding vs OSR layer |
| Discussion | low | not primary |
| Conclusion | low | not primary |
| Figures | medium | activation-space visual explanation |
| Tables | low | not primary |

## 7. Do Emulate

- Explain why thresholding softmax is insufficient.
- Present the OSR method as a layer added to a closed-set deep network.
- Separate known-class accuracy from unknown rejection.
- Use internal network evidence rather than only output probability.

## 8. Do Not Emulate

- Do not import vision/fooling-image framing too heavily.
- Do not overuse OpenMax-specific EVT notation.
- Do not imply DQNGuard provides formal open-space-risk guarantees.

## 9. Useful Pages for Visual Analysis

Page 1: abstract and softmax failure framing.
Page 2: OpenMax figure and contribution list.
Key method pages: OpenMax and activation-vector calibration.
Key figure pages: activation-vector diagrams.
Key table pages: open-set accuracy tables.
Results pages: softmax threshold comparison.
Discussion/conclusion pages: not primary.

## 10. Extracted Heuristics

- A closed-set neural network can be made open-set by adding a decision layer rather than retraining the backbone.
- Softmax confidence thresholding is a weak baseline, not a complete OSR method.
- Internal feature/logit structure can provide stronger unknown evidence.

## 11. Relevance to Our Current Revision

Use this paper in Related Work and Methodology to explain DQNGuard as a decision-layer approach over a closed-set PA CNN.

## 12. Decision

Decision: TECHNICAL_REFERENCE and SECTION_MODEL

Rationale: Essential deep OSR lineage and good method-exposition model, but not RF or MILCOM style.
