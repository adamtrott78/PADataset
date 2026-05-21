# Exemplar Card: Deep Learning for RF Signal Classification in Unknown and Dynamic Spectrum Environments

## 1. Bibliographic Identity

Title: Deep Learning for RF Signal Classification in Unknown and Dynamic Spectrum Environments
Authors: Yi Shi, Kemal Davaslioglu, Yalin E. Sagduyu, William C. Headley, Michael Fowler, Gilbert Green
Venue: IEEE DySPAN
Year: 2019
Length: conference paper
DOI / URL:
PDF slug: 2019_shi_dyspan_unknown_dynamic_rf
Citation status: candidate cite

## 2. Library Classification

Primary decision: SECTION_MODEL
Secondary decisions: TECHNICAL_REFERENCE
Role tags: EXPERIMENT_DESIGN_MODEL; RESULTS_NARRATIVE_MODEL; FIGURE_MODEL; TECHNICAL_LINEAGE
Paper action labels: evaluate_system_component; diagnose_failure_mode; position_architecture

## 3. Why This Paper Is Included

This paper is included because it is a close RF/EMS exemplar for unknown and dynamic spectrum environments. It explicitly considers unknown signal types, replay/spoofing, superimposed signals, and downstream scheduling decisions.

## 4. Relation to Our Paper

DQNGuard similarly treats RF classification as a sensing layer for a downstream operational pipeline. Shi et al. is useful for describing why RF unknowns, replay behavior, and dynamic spectrum conditions matter operationally.

## 5. Scores

### Technical Relevance

| Criterion | Score | Notes |
|---|---:|---|
| RF / EMS / communications relevance | 3 | Direct RF spectrum paper |
| OSR / OOD / calibration relevance | 3 | Unknown signal/outlier detection |
| ML method similarity | 3 | CNN over IQ and feature-based outlier detection |
| Experimental setup similarity | 3 | RF signal classes and SNR |
| Operational / military / cyber relevance | 3 | DSA and jammer setting |
| Total | 15 |  |

### Format Relevance

| Criterion | Score | Notes |
|---|---:|---|
| IEEE two-column format | 3 | IEEE format |
| MILCOM / ComSoc / adjacent venue | 2 | DySPAN adjacent |
| Six-to-eight-page length | 1 | Longer than target |
| Similar figure/table density | 2 | Dense but useful |
| Similar reviewer audience | 1 | RF/comms audience |
| Total | 9 |  |

### Exemplar Quality

| Criterion | Score | Notes |
|---|---:|---|
| Abstract clarity | 2 | Useful but overloaded |
| Introduction flow | 2 | Strong cases but too many |
| Method explanation | 2 | Detailed |
| Experiment explanation | 2 | Useful RF setup |
| Results narration | 2 | Good result figures/tables |
| Figure/table design | 1 | Dense |
| Discussion/limitations | 1 | Limited |
| Total | 12 |  |

## 6. Section Utility Matrix

| Our section or artifact | Utility | Notes |
|---|---|---|
| Abstract | medium | RF unknown/dynamic spectrum motivation |
| Introduction | high | realistic RF failure modes |
| Related Work | high | RF unknown/dynamic signal classification |
| Methodology | medium | CNN over IQ and outlier logic |
| Experimental Design | high | SNR, modulation, known/unknown setup |
| Results | high | result figures/tables under RF conditions |
| Discussion | medium | downstream scheduling analogy |
| Conclusion | low | not primary |
| Figures | high | many RF result figures |
| Tables | medium | SNR/result tables |

## 7. Do Emulate

- List concrete RF deployment violations of closed-set assumptions.
- Connect RF sensing outputs to downstream channel-access decisions.
- Treat unknown signals as operationally expected.
- Use RF-specific examples: jammers, replay, superposition, dynamic spectrum.

## 8. Do Not Emulate

- Do not overload the paper with four separate problem cases.
- Do not make DQNGuard sound like a full spectrum-scheduling system.
- Do not copy dense figure/table layout.
- Do not let the paper drift from PA evidence into generic modulation classification.

## 9. Useful Pages for Visual Analysis

Page 1: unknown/dynamic RF problem framing.
Page 2: four RF cases and downstream scheduling motivation.
Key method pages: unknown signal outlier detection.
Key figure pages: RF cases and confusion matrices.
Key table pages: SNR accuracy tables.
Results pages: unknown/outlier detection and scheduling results.
Discussion/conclusion pages: limited use.

## 10. Extracted Heuristics

- RF unknowns should be motivated with concrete spectrum events.
- A sensing layer becomes more credible when tied to a downstream operational decision.
- DQNGuard should state that it provides evidence, not final response selection.

## 11. Relevance to Our Current Revision

Use this paper to strengthen RF/EMS motivation, experimental design language, and result narration around unknown behavior in dynamic environments.

## 12. Decision

Decision: SECTION_MODEL and TECHNICAL_REFERENCE

Rationale: Strong RF relevance and useful operational framing, but too broad/dense to serve as a polished six-page model.
