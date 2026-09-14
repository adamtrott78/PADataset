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

# Slide 4 — We evaluate the same five behaviors over-the-air across three protocol families

## Target speaking time

Approximately **50-60 seconds**.

## Script

We evaluate these behaviors using over-the-air captures rather than treating this as a purely synthetic classification problem.

The dataset spans three protocol families: WiFi, Bluetooth, and Zigbee. For each protocol, we generate and capture the same five Preliminary Action behaviors—Scan, Burst, Sustain, Hop, and Replay.

That distinction is important. The label we're trying to recognize is the behavior, not the protocol itself. A Burst expressed through WiFi and a Burst expressed through Zigbee are different RF signals, but they represent the same behavioral class.

On the capture side, we transmit and receive using two USRP N210 software-defined radios at 2.437 gigahertz. Each classifier input is a 32-millisecond over-the-air RF window containing 400,000 complex IQ samples at 12.5 mega-samples per second.

So the open-set problem we're about to evaluate is grounded in captured RF across multiple protocol families rather than in a single waveform family.

With that dataset in place, the next question is how to decide when the classifier's prediction should actually be trusted.

## Delivery notes

- Stress **behavior, not protocol**.
- Keep hardware narration short; the point is OTA credibility, not acquisition-system detail.
- Use **USRP N210 software-defined radios**. Do not say "Ettus N210."
- Pause briefly on the 3 × 5 matrix so the audience registers that every protocol spans the same five behaviors.
- The final sentence transitions directly into the OSR decision-layer motivation.

---

# Slide 5 — Unknown detection is only useful if known behavior stays usable

## Target speaking time

Approximately **55-65 seconds**.

## Script

Once we have a closed-set PA classifier, the next problem is deciding when its prediction should be rejected.

We explored two useful directions that informed DQNGuard.

The first is VarMax. VarMax uses structure in the classifier outputs—including confidence, variance, and energy-style evidence—to assign an unknownness score and threshold that score. That gives us useful evidence for novelty, but the operating point still depends heavily on where that threshold is placed.

The second direction is a DQN-style confidence head. Here, features such as maximum softmax probability, the gap between the top two predictions, and entropy are treated as a confidence state, and a learned decision head chooses between known and unknown.

Both approaches are useful, but for our application there is one requirement we want to make explicit: detecting more unknowns cannot come at the cost of arbitrarily rejecting known Preliminary Actions.

So instead of asking only, "How well can I separate known from unknown?" we ask, "How well can I detect unknown behavior while staying inside a fixed known-rejection budget?"

That operating constraint is the central idea behind DQNGuard.

## Delivery notes

- Present VarMax and the DQN-style head as useful predecessors, not strawmen.
- Keep the DQN-style confidence state simple: `P1`, `P1-P2`, and entropy.
- Do not imply that the DQN-style diagram connects to the known-rejection-budget panel; they are separate conceptual panels.
- Stress the phrase **fixed known-rejection budget** at the end.
- Do not reveal Table I results yet.
- The final sentence transitions directly into Slide 6.

---

# Slide 6

**TBD — write only after the slide concept is reviewed and locked.**
