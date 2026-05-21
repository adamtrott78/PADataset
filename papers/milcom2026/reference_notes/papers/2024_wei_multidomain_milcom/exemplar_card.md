# Exemplar Card: Exploiting Multi-Domain Features for Detection of Unclassified Electromagnetic Signals

## 1. Bibliographic Identity

Title: Exploiting Multi-Domain Features for Detection of Unclassified Electromagnetic Signals
Authors: Xue Wei, Dola Saha, Anna Quach
Venue: MILCOM
Year: 2024
Length: short IEEE conference paper
DOI / URL:
PDF slug: 2024_wei_multidomain_milcom
Citation status: cited

## 2. Library Classification

Primary decision: CORE_MODEL
Secondary decisions: SECTION_MODEL
Role tags: VENUE_STYLE_MODEL; METHOD_EXPOSITION_MODEL; EXPERIMENT_DESIGN_MODEL; FIGURE_MODEL; TECHNICAL_LINEAGE
Paper action labels: introduce_method; evaluate_system_component; diagnose_failure_mode

## 3. Why This Paper Is Included

This paper is included because it is the closest current seed exemplar for our venue, RF domain, and multi-domain signal representation strategy. It directly addresses unknown electromagnetic signals under open-set assumptions and uses multiple signal domains to improve detection.

## 4. Relation to Our Paper

DQNGuard uses multi-domain RF representations and RF open-set motivation, but changes the decision layer and task. Wei et al. is useful for communicating why unknown RF signals matter, why image OSR does not transfer directly to wireless signals, and why multi-domain representations are plausible for RF novelty detection.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Direct RF/EMS open-set paper |
| OSR / OOD / calibration relevance | 3 | Direct OSR framing |
| ML method similarity | 2 | Multi-domain model but different GAN mechanism |
| Experimental setup similarity | 3 | RF classes, SNR, signal representations |
| Operational / military / cyber relevance | 3 | Warfare/SIGINT framing |
| Total | 14 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 3 | Directly relevant |
| MILCOM / ComSoc / adjacent venue | 3 | MILCOM |
| Six-to-eight-page length | 3 | Directly relevant |
| Similar figure/table density | 3 | Strong reference |
| Similar reviewer audience | 3 | Directly relevant |
| Total | 15 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 2 | Strong shape, some rough wording |
| Introduction flow | 3 | Very useful problem-to-gap flow |
| Method explanation | 2 | Useful but architecture-heavy |
| Experiment explanation | 2 | Useful RF setup model |
| Results narration | 2 | Useful but not perfect |
| Figure/table design | 2 | Early method figure is useful |
| Discussion/limitations | 1 | Not the main strength |
| Total | 14 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | RF open-set motivation shape |
| Introduction | high | Best current RF/MILCOM intro model |
| Related Work | high | Direct RF open-set/multi-domain reference |
| Methodology | high | Multi-domain representation explanation |
| Experimental Design | high | RF classes, SNR, setup language |
| Results | medium | Useful result interpretation |
| Discussion | medium | Operational implications |
| Conclusion | low | Not primary use |
| Figures | high | Early pipeline figure and page placement |
| Tables | medium | Architecture and parameter tables |

## 7. Do Emulate

- Open with concrete uses for unknown electromagnetic signal detection.
- Explain why closed-set waveform classifiers are unrealistic in the field.
- State that image OSR does not transfer directly to wireless signals.
- Use an early pipeline figure to anchor the method.
- Tie multi-domain RF representations to signal-domain knowledge.

## 8. Do Not Emulate

- Do not inherit the GAN framing.
- Do not over-explain architecture at the expense of the decision layer.
- Do not copy rough phrasing.
- Do not let the paper become a generic RF waveform paper rather than a DQNGuard decision-layer paper.

## 9. Useful Pages for Visual Analysis

Page 1: RF unknown-signal problem framing.
Page 2: contribution list and early method figure.
Key method pages: multi-domain feature extraction and fusion.
Key figure pages: DUNES schema and result plots.
Key table pages: architecture and training parameter tables.
Results pages: SNR and sample-size comparisons.
Discussion/conclusion pages: use selectively.

## 10. Extracted Heuristics

- For MILCOM, RF unknown detection should be motivated operationally before introducing ML details.
- Multi-domain representations should be justified as RF domain knowledge, not arbitrary feature stacking.
- The first method figure should let the reader understand the pipeline before the equations arrive.
- A strong RF paper distinguishes signal-domain constraints from generic image ML assumptions.

## 11. Relevance to Our Current Revision

Use this paper as the strongest current model for revising our Introduction, Methodology opening, and figure placement. It helps ensure DQNGuard sounds native to RF/EMS and MILCOM rather than generic OSR.

## 12. Decision

Decision: CORE_MODEL and SECTION_MODEL

Rationale: Best current match for venue, RF domain, open-set motivation, and multi-domain representation. Should guide the RF-facing parts of the rewrite.
