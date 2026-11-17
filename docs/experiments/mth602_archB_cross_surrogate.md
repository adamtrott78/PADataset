# MTH602 Architecture B — Cross-Surrogate DQNGuard

## Hypothesis

A DQN trained with one known PA serving as pseudo-open evidence is useful only if
its unknownness rule transfers to *other* pseudo-open PAs. Architecture B
therefore selects a single surrogate-specific DQN using off-diagonal transfer,
not performance on the surrogate that produced the candidate.

## Frozen development protocol

For a target-withheld four-known backbone:

1. Partition `val_known` into disjoint roles using the shared deterministic
   multi-surrogate partitioner.
2. For each known class S:
   - train one DQN on `known_fit + pseudo_open[S]`;
   - fit its final unknown-score threshold on `known_threshold` only to the
     declared known-reject budget;
   - evaluate the thresholded candidate on `known_guard` plus every
     `pseudo_open[T]` where T != S.
3. Never score candidate S on `pseudo_open[S]` for candidate selection.
4. Select one candidate by:
   - maximum worst off-diagonal unknown F1;
   - then maximum mean off-diagonal unknown F1;
   - then maximum mean off-diagonal OSR macro-F1;
   - then minimum known-guard rejection.
5. Freeze the winner.
6. Only after the winner is frozen, evaluate the genuine target-open test split.

## Development sequence

- B0: `softmax3 = [Pmax, P1-P2, entropy]`, DQN only.
- B1: matched `expanded5 = [Pmax, P1-P2, entropy, energy, logit variance]`.
- B2: winning state mode plus known-class conditional DQNGuard bands.
- B3: band-rule/weight tuning only if B2 provides evidence that the guard is
  complementary to the DQN state.

B0/B1 use the continuous DQN score `Q_unknown - Q_known` with a known-only
quantile threshold. This makes the declared known-reject budget explicit and
keeps candidate comparison on the same operating constraint.

## Leakage invariants

The true target may not influence:

- backbone gradients;
- backbone checkpoint selection;
- DQN fitting;
- candidate thresholds;
- candidate selection;
- retries or method selection.

The genuine target is first consumed after the Architecture-B winner is frozen.

## Outputs

The evaluator persists:

- off-diagonal cross-surrogate matrix;
- per-candidate transfer summary;
- deterministic partition manifest;
- selected DQN Q-network checkpoint;
- selected threshold;
- final target metrics;
- source/config/checkpoint/result hashes.

## Status

Initial implementation lives in draft PR #23. No merge authorization.
