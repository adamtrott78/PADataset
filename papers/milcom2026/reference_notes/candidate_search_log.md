# Candidate Search Log

This file tracks targeted searches for additional reference and exemplar papers for the MILCOM 2026 DQNGuard paper.

The purpose is not to collect papers randomly. Each candidate must be attached to a specific library gap.

---

## 1. Current Seed Library Status

The seed library currently contains processed cards for:

- 2024_baye_varmax_milcom
- 2024_wei_multidomain_milcom
- 2025_broggi_varmax_uncertainty_novelty
- 2026_tiwari_dqn_ids
- 2026_trott_rf_modulation_varmax
- energy_based_open_world_uncertainty_modeling_for_confidence_calibration

Current strengths:

- varMax lineage is covered.
- DQN-IDS comparison lineage is covered.
- RF multi-domain representation lineage is covered.
- closed-world softmax and energy/open-world uncertainty framing is covered.
- Wei gives one useful MILCOM/RF/multi-domain exemplar.

Current gaps:

- Need a stronger MILCOM or IEEE short-paper writing exemplar.
- Need a stronger results-narrative exemplar.
- Need a stronger claim-boundary or systems/security exemplar.
- Need a stronger table-design exemplar.
- Need a stronger polished first-page exemplar.

---

## 2. Admission Rule

Before a paper is ingested, answer:

What specific gap does this paper fill?

Allowed gap labels:

- VENUE_STYLE_MODEL
- PROBLEM_FRAMING_MODEL
- METHOD_EXPOSITION_MODEL
- EXPERIMENT_DESIGN_MODEL
- RESULTS_NARRATIVE_MODEL
- FIGURE_MODEL
- TABLE_MODEL
- CLAIM_BOUNDARY_MODEL
- TECHNICAL_LINEAGE
- LAB_CONTINUITY
- NEGATIVE_MODEL

If no gap can be named, do not ingest the paper.

---

## 3. Search Lanes

### Lane A: MILCOM / IEEE Short-Paper Style

Goal: find six-to-eight-page IEEE/MILCOM or ComSoc papers with strong first-page pacing, good figure/table economy, and clear contribution structure.

Candidate search phrases:

- MILCOM best paper RF machine learning spectrum sensing
- MILCOM accepted papers RF machine learning spectrum sensing PDF
- MILCOM electronic warfare machine learning detection PDF
- IEEE Military Communications Conference spectrum sensing machine learning
- IEEE MILCOM cyber electromagnetic spectrum machine learning detection

Admission target:

- VENUE_STYLE_MODEL
- PROBLEM_FRAMING_MODEL
- FIGURE_MODEL
- TABLE_MODEL

### Lane B: Results-Narrative Models

Goal: find papers that use one table, one heatmap, one ablation, or one matrix-style result to support a clear argument.

Candidate search phrases:

- open set recognition heatmap unknown detection results analysis
- OOD detection calibration heatmap results analysis
- IEEE machine learning ablation table results narrative
- RF machine learning ablation study table IEEE
- spectrum sensing machine learning comparison table IEEE

Admission target:

- RESULTS_NARRATIVE_MODEL
- TABLE_MODEL
- FIGURE_MODEL

### Lane C: Claim-Boundary / Systems Component Models

Goal: find papers that introduce a component of a larger operational system without overclaiming that the full system is solved.

Candidate search phrases:

- cyber physical sensing pipeline detection component limitations IEEE
- wireless security machine learning detection component limitations
- cyber electromagnetic spectrum decision support detection pipeline
- machine learning wireless security operational limitations IEEE
- RF sensing decision support system limitations paper

Admission target:

- CLAIM_BOUNDARY_MODEL
- DISCUSSION_MODEL
- PROBLEM_FRAMING_MODEL

### Lane D: Technical Reinforcement

Goal: fill missing citation or definition gaps, not prose/style gaps.

Candidate search phrases:

- Towards Open Set Deep Networks OpenMax PDF
- Toward Open Set Recognition PDF
- Energy-based out-of-distribution detection Liu PDF
- On Calibration of Modern Neural Networks Guo PDF
- open set recognition survey deep neural networks

Admission target:

- TECHNICAL_LINEAGE
- METHOD_EXPOSITION_MODEL
- REFERENCE_ONLY

---

## 4. Early Candidate Notes

These are not admitted papers yet. They are candidates to inspect.

### Candidate: The RFML Ecosystem

Possible roles:

- CLAIM_BOUNDARY_MODEL
- PROBLEM_FRAMING_MODEL
- TECHNICAL_LINEAGE
- NEGATIVE_MODEL if too survey-like

Reason to inspect:

This paper discusses the unique challenges of applying deep learning to RF applications, including trust, security, hardware, and deployment constraints. It may help bound our claims about RFML deployment, but because it is a survey-like paper it should not become a six-page MILCOM pacing model.

Admission status: candidate only.

### Candidate: Adversarial Machine Learning for 5G Communications Security

Possible roles:

- PROBLEM_FRAMING_MODEL
- CLAIM_BOUNDARY_MODEL
- TECHNICAL_LINEAGE

Reason to inspect:

This paper connects machine learning, wireless communications, spectrum sharing, and adversarial settings. It may help operationally motivate why RF ML systems must handle adversarial or out-of-distribution behavior.

Admission status: candidate only.

### Candidate: Joint Detection and Classification of Communication and Radar Signals in Congested RF Environments Using YOLOv8

Possible roles:

- RF sensing exemplar
- RESULTS_NARRATIVE_MODEL
- FIGURE_MODEL

Reason to inspect:

This paper focuses on RF detection/classification under congested environments. It may help with RF sensing result narration, but it is not obviously a MILCOM style model.

Admission status: candidate only.

### Candidate: Deep Learning Classification of 3.5 GHz Band Spectrograms with Applications to Spectrum Sensing

Possible roles:

- EXPERIMENT_DESIGN_MODEL
- RESULTS_NARRATIVE_MODEL
- RF sensing exemplar

Reason to inspect:

This paper uses real spectrum/spectrogram data and compares classical and deep methods for spectrum sensing. It may help with experimental setup and result interpretation.

Admission status: candidate only.

### Candidate: Spectrum Prediction and Interference Detection for Satellite Communications

Possible roles:

- EXPERIMENT_DESIGN_MODEL
- RESULTS_NARRATIVE_MODEL
- CLAIM_BOUNDARY_MODEL

Reason to inspect:

This paper frames ML-based anomaly/interference detection as an operational spectrum-monitoring component. It may help with component-level claim boundaries.

Admission status: candidate only.

---

## 5. Search Notes

For each future search, record:

Search date:
Search lane:
Search query:
Candidate title:
Venue/year:
URL or DOI:
Why it might fill the gap:
Initial decision:
Next action:

---

## 6. Next Search Targets

Priority order:

1. Find two stronger MILCOM or IEEE short-paper style exemplars.
2. Find one strong results-narrative/table exemplar.
3. Find one strong claim-boundary systems/security exemplar.
4. Only then add more technical lineage papers.

The goal is to process a small, high-quality batch rather than a large uncontrolled pile.

---

## 7. ScholarGPT Polished Short-Paper Search Pass

Search source: ScholarGPT fresh exemplar pass.
Search purpose: fill the remaining style/library gaps after technical OSR/OOD lineage was already covered.

Main conclusion:

The useful candidates from this pass are not primarily OSR papers. They are RF, spectrum, wireless security, and operational sensing papers that can teach MILCOM/IEEE page economy, component framing, practical RF experiment reporting, and claim boundaries.

### Highest-priority candidates

| Candidate | Initial decision | Main roles | Notes |
|---|---|---|---|
| Adversarial Machine Learning for Enhanced Spread Spectrum Communications | process now | VENUE_STYLE_MODEL; PROBLEM_FRAMING_MODEL; METHOD_EXPOSITION_MODEL; CLAIM_BOUNDARY_MODEL | Strong MILCOM RF/security pacing candidate |
| SpecForce | process now | PROBLEM_FRAMING_MODEL; FIGURE_MODEL; CLAIM_BOUNDARY_MODEL; EXPERIMENT_DESIGN_MODEL | Best system-component and battlefield IoT/spectrum-sensor framing |
| Stealth Spectrum Sensing Data Falsification Attacks | process now if PDF available | PROBLEM_FRAMING_MODEL; EXPERIMENT_DESIGN_MODEL; RESULTS_NARRATIVE_MODEL; CLAIM_BOUNDARY_MODEL | Strong battlefield sensing failure-mode candidate |
| Searchlight | process now if PDF available | METHOD_EXPOSITION_MODEL; EXPERIMENT_DESIGN_MODEL; RESULTS_NARRATIVE_MODEL; TABLE_MODEL | Strong practical RF detector/results-reporting model |
| Stitching the Spectrum | process now | METHOD_EXPOSITION_MODEL; FIGURE_MODEL; RESULTS_NARRATIVE_MODEL | Strong pipeline and visual model |
| HyperAdv | process now | VENUE_STYLE_MODEL; METHOD_EXPOSITION_MODEL; CLAIM_BOUNDARY_MODEL; RESULTS_NARRATIVE_MODEL | RFML security component and claim-boundary model |

### Second-wave candidates

| Candidate | Initial decision | Main roles | Notes |
|---|---|---|---|
| WRIST | hold for second wave | EXPERIMENT_DESIGN_MODEL; FIGURE_MODEL; RESULTS_NARRATIVE_MODEL | Longer RF system paper; useful for setup/results |
| Practical Training for RF Fingerprinting of Commercial Transmitters at the Edge | hold for second wave | EXPERIMENT_DESIGN_MODEL; METHOD_EXPOSITION_MODEL; TABLE_MODEL | Compact RF capture/evaluation candidate |
| Sensing-Throughput Tradeoffs with GANs for NextG Spectrum Sharing | process if results exemplar needed | RESULTS_NARRATIVE_MODEL; TABLE_MODEL; CLAIM_BOUNDARY_MODEL | Useful for tradeoff/result narration |
| IoT-Enabled Machine Learning for an Algorithmic Spectrum Decision Process | hold for decision-layer framing | METHOD_EXPOSITION_MODEL; CLAIM_BOUNDARY_MODEL; PROBLEM_FRAMING_MODEL | Useful conceptual analogue for sensing-to-decision handoff |

### Hold candidates

Channel-Aware Adversarial Attacks, DeepWiFi, and The Best Defense Is a Good Offense are useful RFML/security references but are longer journal papers and not immediate six-page MILCOM style models.

Tri-Hybrid MIMO is polished but too tutorial/architecture-oriented for the current revision pass.

### Award-note policy

Do not record award-winning status unless verified from a primary source. Several candidate notes mention author-level awards rather than paper-specific awards.
