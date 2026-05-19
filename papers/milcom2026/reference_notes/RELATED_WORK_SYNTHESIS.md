# Related Work and Design Synthesis

This file summarizes converted references for the MILCOM 2026 paper. It bridges reference papers into `sections/2-related.tex` and also tracks design choices worth copying.

## Source inventory

| Key | Source | Used for | Converted? | Notes |
|---|---|---|---:|---|
| 2024_baye_varmax | Baye et al., varMax MILCOM 2024 | original varMax OSR framing | no | TODO |
| 2025_broggi_varmax | Broggi et al., varMax HICSS 2025 | uncertainty/novelty management | no | TODO |
| 2026_trott_rf_varmax | Trott et al., RF varMax | RF OSR, banded variance/energy thresholds | yes | TODO summarize |
| 2026_tiwari_dqn_ids | Tiwari et al., DQN-IDS | DQN confidence-state OSR head | no | TODO |
| attack_chain_prediction | labmate ATT&CK prediction work | downstream QR-CWoS / attack-chain linkage | partial | TODO |

## Design choices worth considering

TODO.

## Related-work paragraph plan

1. Open-set recognition and varMax.
2. RF signal novelty / RF OSR.
3. DQN-IDS and confidence-state decision heads.
4. ATT&CK attack-chain prediction and continual label-making as downstream consumers of RF OSR outputs.
