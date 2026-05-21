# Exemplar Card: Model Evaluation for Radio-Frequency Signal Modulation Classifiers in the Existence of Novel Samples

## 1. Bibliographic Identity

Title: Model Evaluation for Radio-Frequency Signal Modulation Classifiers in the Existence of Novel Samples
Authors: Adam Trott, Henry Thompson, Gokhan Kul
Venue:
Year: 2026
Length: draft or conference-style paper
DOI / URL:
PDF slug: 2026_trott_rf_modulation_varmax
Citation status: cited

## 2. Library Classification

Primary decision: TECHNICAL_REFERENCE
Secondary decisions: SECTION_MODEL
Role tags: LAB_CONTINUITY; TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; PROBLEM_FRAMING_MODEL; NEGATIVE_MODEL
Paper action labels: evaluate_system_component; diagnose_failure_mode; introduce_method

## 3. Why This Paper Is Included

This paper is included because it is the direct internal bridge between varMax, RF signal classification, multi-domain CNN representations, and per-predicted-class threshold bands. It also documents the important lesson that RF open-set behavior can be highly target-dependent.

## 4. Relation to Our Paper

The DQNGuard paper builds on the same broad intuition but changes the task from modulation unknowns to RF preliminary-action behavior and changes the decision layer to predicted-class calibration, evidence scoring, and a known-budget threshold. The prior Trott paper is a lab-continuity reference and a warning about RF heterogeneity.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Direct RF |
| OSR / OOD / calibration relevance | 3 | Direct |
| ML method similarity | 3 | Multi-domain CNN and varMax lineage |
| Experimental setup similarity | 3 | RF known/unknown folds |
| Operational / military / cyber relevance | 3 | Related RF sensing motivation |
| Total | 15 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 1 | Not currently the target model |
| MILCOM / ComSoc / adjacent venue | 0 | Not MILCOM |
| Six-to-eight-page length | 2 | Somewhat comparable |
| Similar figure/table density | 2 | Related |
| Similar reviewer audience | 2 | RF/ML overlap |
| Total | 7 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 2 | Useful but dense |
| Introduction flow | 2 | Useful RF motivation |
| Method explanation | 2 | Directly relevant |
| Experiment explanation | 1 | Needs compression |
| Results narration | 1 | Useful for target dependence |
| Figure/table design | 1 | Not primary |
| Discussion/limitations | 1 | Useful warning |
| Total | 10 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | Multi-domain RF OSR language |
| Introduction | medium | RF unknown motivation |
| Related Work | high | Lab continuity |
| Methodology | high | Multi-domain CNN and banded thresholds |
| Experimental Design | medium | RF folds and target dependence |
| Results | high | Target dependence lesson |
| Discussion | high | Surrogate/unknown dependence |
| Conclusion | medium | Claim boundary |
| Figures | medium | RF evidence visualizations |
| Tables | medium | Architecture and grouping tables |

## 7. Do Emulate

- Preserve the RF-specific open-set motivation.
- Use the multi-domain representation language.
- State clearly that RF OSR performance depends on the open/closed set makeup.
- Use per-predicted-class evidence bands as lineage for DQNGuard calibration.

## 8. Do Not Emulate

- Do not overload the contribution list.
- Do not make the paper feel like only a varMax extension.
- Do not put too much method detail before defining the task.
- Do not let modulation-specific details leak into preliminary-action framing.

## 9. Useful Pages for Visual Analysis

Page 1: abstract, RF motivation, contribution bullets.
Page 2: system design and modulation grouping.
Key method pages: varMax decision logic, threshold bands.
Key figure pages: variance and energy spread figures.
Key table pages: architecture and modulation grouping.
Results pages: fold-dependent performance.
Discussion/conclusion pages: limitations and target dependence.

## 10. Extracted Heuristics

- RF unknown detection may not obey generic OOD score directionality.
- Per-class and banded thresholds are necessary when evidence distributions are class-dependent.
- A strong DQNGuard paper should make target dependence a result, not an embarrassment.
- Lab-continuity papers can preserve insight while still requiring complete prose revision.

## 11. Relevance to Our Current Revision

Use this paper to ensure the DQNGuard paper preserves the key RF insight: unknown behavior detection is target-dependent and calibration-sensitive. This should directly inform the Results and Discussion sections.

## 12. Decision

Decision: TECHNICAL_REFERENCE and SECTION_MODEL

Rationale: Highest technical relevance, but should be treated as raw lineage and insight rather than a polished final prose model.
