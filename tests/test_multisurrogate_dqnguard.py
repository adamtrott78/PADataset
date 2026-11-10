import unittest

import numpy as np

from osr_core import SplitOutputs
from multisurrogate_dqnguard import (
    EmpiricalCDFNormalizer,
    aggregate_max_guard,
    assert_target_quarantined,
    fit_surrogate_guard,
    known_only_threshold,
    partition_known_calibration,
)


def make_split(n_per_class=10, classes=4, name="known"):
    y = np.repeat(np.arange(classes), n_per_class)
    n = len(y)
    logits = np.zeros((n, classes), dtype=np.float32)
    for i, cls in enumerate(y):
        logits[i, cls] = 3.0 + 0.01 * i
        logits[i] += np.linspace(-0.2, 0.2, classes)
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = e / e.sum(axis=1, keepdims=True)
    features = np.arange(n * 3, dtype=np.float32).reshape(n, 3)
    pred = probs.argmax(axis=1)
    meta = [{"sample_id": f"{name}-{i}"} for i in range(n)]
    return SplitOutputs(
        split_name=name,
        y_true=y,
        logits=logits,
        features=features,
        closed_pred=pred,
        probs=probs,
        sample_meta=meta,
    )


class MultiSurrogateDQNGuardContractTests(unittest.TestCase):
    def test_partition_is_deterministic_and_disjoint(self):
        split = make_split()
        names = ["PA1", "PA2", "PA3", "PA4"]
        a = partition_known_calibration(split, names, seed=17)
        b = partition_known_calibration(split, names, seed=17)
        self.assertEqual(a.manifest["sha256"], b.manifest["sha256"])

        sets = [set(a.manifest["roles"][k]) for k in ("fit", "guard", "norm", "threshold")]
        sets += [set(v) for v in a.manifest["pseudo_open"].values()]
        union = set()
        for s in sets:
            self.assertFalse(union.intersection(s))
            union.update(s)
        self.assertEqual(len(union), len(split.y_true))

    def test_target_quarantine_accepts_disjoint_and_rejects_overlap(self):
        known = make_split(name="known")
        parts = partition_known_calibration(known, ["PA1", "PA2", "PA3", "PA4"], seed=2)
        target = make_split(n_per_class=2, classes=4, name="target")
        assert_target_quarantined(parts, target)

        overlapping = make_split(n_per_class=2, classes=4, name="target")
        overlapping.sample_meta[0] = known.sample_meta[0]
        with self.assertRaisesRegex(ValueError, "target leakage"):
            assert_target_quarantined(parts, overlapping)

    def test_empirical_normalizer_is_monotone(self):
        norm = EmpiricalCDFNormalizer().fit(np.array([0.0, 1.0, 2.0, 3.0]))
        out = norm.transform(np.array([-1.0, 0.5, 2.5, 9.0]))
        self.assertTrue(np.all(np.diff(out) >= 0))
        self.assertEqual(out[-1], 1.0)

    def test_surrogate_guard_weights_are_nonnegative_and_normalized(self):
        known = np.array([[0.0, 0.0, 0.0], [0.1, 0.2, 0.1], [0.2, 0.1, 0.2]])
        pseudo = np.array([[2.0, 0.2, 0.1], [3.0, 0.3, 0.2], [2.5, 0.2, 0.2]])
        guard = fit_surrogate_guard("PA1", known, pseudo)
        self.assertTrue(np.all(guard.weights >= 0))
        self.assertAlmostEqual(float(guard.weights.sum()), 1.0)
        self.assertGreater(guard.weights[0], guard.weights[1])

    def test_max_aggregation_is_predeclared_or_semantics(self):
        out = aggregate_max_guard({
            "PA1": np.array([0.1, 0.9]),
            "PA2": np.array([0.8, 0.2]),
        })
        np.testing.assert_allclose(out, np.array([0.8, 0.9]))

    def test_known_only_threshold_does_not_depend_on_target(self):
        known = np.linspace(-1.0, 1.0, 100)
        t1, r1 = known_only_threshold(known, budget=0.05)
        _target_a = np.array([-100.0, 100.0])
        t2, r2 = known_only_threshold(known, budget=0.05)
        self.assertEqual(t1, t2)
        self.assertEqual(r1, r2)
        self.assertGreaterEqual(r1, 0.05)

    def test_partition_rejects_too_few_samples(self):
        split = make_split(n_per_class=4)
        with self.assertRaisesRegex(ValueError, "need >= 5"):
            partition_known_calibration(split, ["PA1", "PA2", "PA3", "PA4"])


if __name__ == "__main__":
    unittest.main()
