# MILCOM 2026 Presentation Script

This file contains the spoken script for slides whose concepts are stable enough to narrate.

The script should remain conversational and clear. It is not intended to be read as a paper paragraph. Preserve the scientific claim boundaries in the slide plan.

---

# Slide 2 — Closed-set RF classifiers cannot say "I don't know"

## Target speaking time

Approximately **45-55 seconds**.

## Script

On the left is the conventional closed-set problem. If the receiver observes a behavior the classifier already knows, everything works as expected. A Burst is classified as Burst.

The problem is the second case. If genuinely unfamiliar RF behavior appears, the classifier still has to choose one of its existing labels. "Unknown" simply is not in its output space. And that prediction can still be made with high confidence.

What we want is the behavior on the right. Known observations should remain useful known classifications, while observations that do not fit the trained taxonomy should be routed as unknown.

That distinction matters because these classifications are intended to become evidence for downstream decision-making. A confidently mislabeled novel behavior can be more damaging than admitting that the system does not recognize what it is seeing.

So what exactly are the RF behaviors we're trying to recognize?

## Delivery notes

- Do not rush the two examples. Let the audience visually compare left and right.
- Stress **"Unknown simply is not in its output space."**
- The phrase **"Known observations should remain useful known classifications"** is important because it sets up the later known-rejection budget.
- Do not introduce DQNGuard yet.
- The final sentence is the direct transition to Slide 3.

---

# Slide 3 — Preliminary Actions capture RF behavior, not final attack labels

## Target speaking time

Approximately **55-65 seconds**.

## Script

The behaviors we're classifying are what we call Preliminary Actions, or PAs.

A Preliminary Action is not a final attack-technique label. It is observable RF behavior that may precede, enable, or contextualize a later cyber or Electronic Warfare attack technique. That makes it useful as precursor evidence for downstream reasoning, including MITRE ATT&CK-style reasoning.

In this work we evaluate five behaviors. Scan represents discovery-like RF activity. Burst is repeated short transmissions separated by quiet gaps. Sustain is persistent channel occupancy. Hop captures frequency-agile dwell and revisit behavior. And Replay captures repeated waveform or template structure.

The important distinction is the level of the claim. At this stage we're asking, "What behavior can I observe in the RF signal?" We're not yet claiming, "I know exactly what attack technique is occurring."

That makes these detections useful as precursor evidence for downstream reasoning while still preserving uncertainty where appropriate.

We evaluated this same behavioral taxonomy across WiFi, Bluetooth, and Zigbee.

To test that in the real RF environment, we built an over-the-air dataset spanning all three protocol families.

## Delivery notes

- Define **Preliminary Action** before using the acronym PA repeatedly.
- Stress that the labels describe **observable RF behavior**, not final ATT&CK/EW attribution.
- Use **cyber or Electronic Warfare attack technique** rather than the vaguer term `effect`.
- Do not imply that every PA literally occurs before an attack; preserve the broader "precede, enable, or contextualize" framing.
- Give each of the five behavior cards enough time for the audience to connect the label to its RF pattern.
- The final sentence is the direct transition to Slide 4.

---

# Slide 4

**TBD — write only after the slide concept is reviewed and locked.**
