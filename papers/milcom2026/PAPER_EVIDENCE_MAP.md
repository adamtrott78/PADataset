
---

# OTA physical capture setup

The OTA recordings used two Ettus USRP N210 radios. One radio used an SBX daughterboard and the other used a CBX daughterboard. Each radio used a VERT2450 omnidirectional antenna. The radios were separated by approximately one sheet of US letter paper along the long edge, i.e., about 11 inches. TX gain was 30 dB and RX gain was 10 dB. Both radios were connected through a Netgear 1 GbE switch, which was connected to the Lambda Vector Pro workstation used for control/capture.

Paper-facing setup sentence:

The OTA capture setup used two Ettus USRP N210 radios, equipped with SBX/CBX daughterboards and VERT2450 omnidirectional antennas, connected through a Netgear 1 GbE switch to a Lambda Vector Pro workstation. The radios were separated by approximately 11 inches, with TX/RX gains fixed at 30/10 dB.

---

# OTA network hardware correction

The Ethernet switch used for the OTA capture setup was a NETGEAR ProSAFE GS108 Gigabit switch.

Updated paper-facing setup sentence:

The OTA capture setup used two Ettus USRP N210 radios, equipped with SBX/CBX daughterboards and VERT2450 omnidirectional antennas, connected through a NETGEAR ProSAFE GS108 Gigabit switch to a Lambda Vector Pro workstation. The radios were separated by approximately 11 inches, with TX/RX gains fixed at 30/10 dB.

---

# Target--Surrogate surrogate-selection analysis

The L2O terminology is deprecated for paper-facing writing. The paper should use **Target--Surrogate Matrix** or **TS matrix**.

We tested three candidate surrogate-selection rule families:

1. Guard-score calibration rule:
   - choose the surrogate with highest calibration-open recall at the known-only threshold.

2. Confidence-geometry rule:
   - choose the surrogate with stronger softmax uncertainty separation from known calibration samples, using P1, P1-P2 gap, and entropy.

3. Feature-geometry rule:
   - choose the surrogate based on nearest known-centroid distances and centroid-margin statistics in backbone feature space.

Result:
- Guard-score calibration recall did not predict target unknown F1.
- Confidence-geometry scores were negatively correlated with target unknown F1.
- Simple feature-geometry metrics gave only weak signal; the best positive metric was surrogate centroid-margin median, but it selected the true best surrogate for only 1/5 targets.

Conclusion:
The TS matrix shows that surrogate choice matters strongly, but simple calibration-recall, confidence-geometry, and centroid-distance rules do not yet provide a reliable automatic surrogate-selection policy. This supports treating surrogate selection as a nontrivial learned-geometry problem rather than a simple confidence-thresholding problem.
