# Exemplar Card: Energy-based Out-of-distribution Detection

## 1. Bibliographic Identity

Title: Energy-based Out-of-distribution Detection
Authors: Weitang Liu, Xiaoyun Wang, John D. Owens, Yixuan Li
Venue: NeurIPS
Year: 2020
Length: conference paper
DOI / URL:
PDF slug: 2020_liu_energy_ood_detection
Citation status: should cite

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; RESULTS_NARRATIVE_MODEL
Paper action labels: introduce_method; diagnose_failure_mode; benchmark_methods

## 3. Why This Paper Is Included

This paper is included because it is the core energy-score OOD reference. It explains why softmax confidence can be overconfident on OOD samples and defines energy as a scalar score derived from logits.

## 4. Relation to Our Paper

DQNGuard uses energy-style evidence as part of its guard evidence. Liu et al. gives the technical lineage for energy scoring and helps us explain why logit-space evidence can be more informative than softmax confidence alone.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 0 | Not RF |
| OSR / OOD / calibration relevance | 3 | Direct OOD scoring |
| ML method similarity | 3 | Logit-derived energy evidence |
| Experimental setup similarity | 1 | Different domain |
| Operational / military / cyber relevance | 3 | Open-world reliability transfers |
| Total | 10 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 0 | NeurIPS |
| MILCOM / ComSoc / adjacent venue | 0 | Not adjacent |
| Six-to-eight-page length | 1 | Not target format |
| Similar figure/table density | 1 | Useful but ML-style |
| Similar reviewer audience | 2 | ML/OOD overlap |
| Total | 4 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 3 | Strong |
| Introduction flow | 3 | Clear failure mode |
| Method explanation | 3 | Energy derivation is useful |
| Experiment explanation | 2 | Clear OOD setup |
| Results narration | 2 | Good score comparison |
| Figure/table design | 1 | Dense |
| Discussion/limitations | 1 | Not primary |
| Total | 15 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | energy/OOD wording |
| Introduction | high | softmax overconfidence failure |
| Related Work | high | direct energy citation |
| Methodology | high | energy score definition |
| Experimental Design | medium | threshold and AUROC/FPR framing |
| Results | medium | energy-vs-softmax comparisons |
| Discussion | medium | score limitations |
| Conclusion | low | not primary |
| Figures | medium | conceptual energy figure |
| Tables | medium | OOD score tables |

## 7. Do Emulate

- Explain energy as a scalar logit-derived score.
- Contrast energy with softmax confidence.
- Treat energy as evidence, not probability.
- Use thresholding language carefully.

## 8. Do Not Emulate

- Do not import image-domain benchmark framing.
- Do not claim energy alone solves open-set RF detection.
- Do not over-explain energy-bounded training if we only use inference-time evidence.

## 9. Useful Pages for Visual Analysis

Page 1: abstract and OOD motivation.
Page 2: energy framework figure.
Key method pages: energy score derivation.
Key figure pages: softmax-vs-energy comparison.
Key table pages: OOD benchmark results.
Results pages: score comparisons.
Discussion/conclusion pages: limited.

## 10. Extracted Heuristics

- Softmax confidence and energy encode different information.
- Energy should be described as logit-space evidence.
- DQNGuard should say energy-style evidence contributes to guard scoring, not that it is the whole OSR rule.

## 11. Relevance to Our Current Revision

Use this paper to tighten DQNGuard's guard-evidence explanation and to justify energy-style scoring in Related Work and Methodology.

## 12. Decision

Decision: TECHNICAL_REFERENCE and SECTION_MODEL

Rationale: Essential energy-score lineage and useful method exposition, but not a venue/style exemplar.
