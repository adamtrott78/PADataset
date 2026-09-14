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

# Slide 3

**TBD — write only after the slide concept is reviewed and locked.**
