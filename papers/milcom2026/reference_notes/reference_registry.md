# Reference Registry

This registry tracks processed reference and exemplar papers for the MILCOM 2026 DQNGuard paper.

These classifications are first-pass provisional audits. They should be updated after deeper section-specific analysis.

| Slug | Cited? | Decision | Primary roles | Best use | Technical score | Format score | Quality score |
|---|---|---|---|---|---:|---:|---:|
| 2024_baye_varmax_milcom | yes | TECHNICAL_REFERENCE; SECTION_MODEL | TECHNICAL_LINEAGE; VENUE_STYLE_MODEL; RESULTS_NARRATIVE_MODEL; NEGATIVE_MODEL | varMax lineage, MILCOM baseline comparison, confidence-based OSR framing | 13 | 14 | 10 |
| 2024_wei_multidomain_milcom | yes | CORE_MODEL; SECTION_MODEL | VENUE_STYLE_MODEL; METHOD_EXPOSITION_MODEL; EXPERIMENT_DESIGN_MODEL; FIGURE_MODEL; TECHNICAL_LINEAGE | RF open-set motivation, multi-domain representation framing, MILCOM page economy | 14 | 15 | 14 |
| 2025_broggi_varmax_uncertainty_novelty | yes | TECHNICAL_REFERENCE; SECTION_MODEL | TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; LAB_CONTINUITY; NEGATIVE_MODEL | varMax uncertainty background, longer method explanation, balanced OSR logic | 12 | 6 | 9 |
| 2026_tiwari_dqn_ids | yes | TECHNICAL_REFERENCE; SECTION_MODEL | TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; LAB_CONTINUITY; NEGATIVE_MODEL | DQN-style confidence-state comparison, learned decision-layer baseline | 11 | 7 | 8 |
| 2026_trott_rf_modulation_varmax | yes | TECHNICAL_REFERENCE; SECTION_MODEL | LAB_CONTINUITY; TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; PROBLEM_FRAMING_MODEL; NEGATIVE_MODEL | RF varMax bridge, multi-domain CNN precedent, target-dependent RF OSR behavior | 15 | 7 | 10 |
| energy_based_open_world_uncertainty_modeling_for_confidence_calibration | should cite | TECHNICAL_REFERENCE; SECTION_MODEL | TECHNICAL_LINEAGE; PROBLEM_FRAMING_MODEL; METHOD_EXPOSITION_MODEL; CLAIM_BOUNDARY_MODEL | closed-world softmax failure framing, energy/open-world uncertainty lineage | 10 | 5 | 17 |
| 2013_scheirer_toward_open_set_recognition | should cite | TECHNICAL_REFERENCE | TECHNICAL_LINEAGE; PROBLEM_FRAMING_MODEL; CLAIM_BOUNDARY_MODEL | canonical open-set recognition definition, open space risk, rejection framing | 10 | 4 | 14 |
| 2016_bendale_open_set_deep_networks | should cite | TECHNICAL_REFERENCE; SECTION_MODEL | TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; PROBLEM_FRAMING_MODEL | deep-network OSR, OpenMax, softmax failure, post-hoc rejection layer | 11 | 5 | 15 |
| 2017_guo_calibration_modern_neural_networks | should cite | TECHNICAL_REFERENCE; SECTION_MODEL | TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; TABLE_MODEL | confidence calibration definition, reliability diagrams, accuracy-vs-confidence distinction | 8 | 4 | 16 |
| 2019_shi_dyspan_unknown_dynamic_rf | candidate cite | SECTION_MODEL; TECHNICAL_REFERENCE | EXPERIMENT_DESIGN_MODEL; RESULTS_NARRATIVE_MODEL; FIGURE_MODEL; TECHNICAL_LINEAGE | RF unknown/dynamic spectrum setting, replay/spoofing, superposition, downstream scheduling use | 15 | 9 | 12 |
| 2020_liu_energy_ood_detection | should cite | TECHNICAL_REFERENCE; SECTION_MODEL | TECHNICAL_LINEAGE; METHOD_EXPOSITION_MODEL; RESULTS_NARRATIVE_MODEL | energy-score definition, softmax-vs-energy distinction, OOD scoring threshold | 10 | 4 | 15 |

## Seed Library Verdict

The seed library is strong for technical lineage but incomplete as a style library.

Current strengths:

- varMax lineage is covered.
- DQN-IDS comparison lineage is covered.
- RF multi-domain representation lineage is covered.
- closed-world softmax and energy/open-world uncertainty framing is covered.

Current gaps:

- Need a stronger polished MILCOM or IEEE short-paper writing exemplar.
- Need a stronger results-narrative exemplar from a compact six-to-eight-page paper.
- Need a stronger claim-boundary or systems/security exemplar.
- Need a stronger table-design exemplar.

Second-batch update:

- Canonical OSR lineage is now covered by Scheirer and Bendale/OpenMax.
- Confidence calibration lineage is now covered by Guo.
- Energy-score OOD lineage is now covered by Liu.
- RF unknown/dynamic spectrum motivation is strengthened by Shi DySPAN.
- The main unresolved gap is still polished short-paper style, not technical background.

## Immediate Use in Revision

For the introduction, synthesize:

1. Energy paper's causal diagnosis of closed-world softmax.
2. Wei paper's RF/EMS unknown-signal motivation.
3. Trott/Baye/Broggi lineage for varMax-style decision evidence.
4. Tiwari lineage only as a comparison point for DQN-style confidence-state heads.

For methodology, synthesize:

1. Wei for multi-domain RF feature explanation.
2. Trott for per-predicted-class evidence bands.
3. Energy for disciplined notation and uncertainty framing.
4. Broggi/Baye for varMax mechanics.

For results and discussion, synthesize:

1. Trott for target/fold dependence.
2. Wei for RF result interpretation.
3. Energy for claim-boundary discipline.
