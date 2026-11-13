import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
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
    return SimpleNamespace(
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

    def test_real_default_collation_preserves_sample_identities_and_quarantine(self):
        import torch
        from torch.utils.data._utils.collate import default_collate
        from osr_core import _collect_split_outputs, _decollate_sample_metadata
        from multisurrogate_dqnguard import split_sample_ids

        class DummyBackbone(torch.nn.Module):
            def forward(self, x, return_features=False):
                logits = torch.stack((x[:, 0], x[:, 1], x[:, 2], x[:, 3]), dim=1)
                return (logits, x) if return_features else logits

        samples = [
            (torch.tensor([float(i % 4 == cls) for cls in range(4)]),
             torch.tensor(i % 4),
             {"dataset_index": i, "local_idx": i, "path": f"/cache/known-{i}.h5",
              "pa_name": ("PA1", "PA3", "PA4", "PA8")[i % 4]})
            for i in range(40)
        ]
        batches = [default_collate(samples[:17]), default_collate(samples[17:])]
        self.assertIsInstance(batches[0][2], dict)
        self.assertIsInstance(batches[0][2]["dataset_index"], torch.Tensor)
        split = _collect_split_outputs(DummyBackbone(), batches, "cpu", "known")
        self.assertEqual(len(split.sample_meta), len(split.y_true))
        self.assertEqual([m["dataset_index"] for m in split.sample_meta], list(range(40)))
        self.assertEqual([m["path"] for m in split.sample_meta],
                         [f"/cache/known-{i}.h5" for i in range(40)])
        self.assertEqual(len(set(split_sample_ids(split))), 40)

        classes = ["PA1", "PA3", "PA4", "PA8"]
        first = partition_known_calibration(split, classes, seed=17)
        second = partition_known_calibration(split, classes, seed=17)
        self.assertEqual(first.manifest["sha256"], second.manifest["sha256"])
        groups = [set(v) for v in first.manifest["roles"].values()]
        groups += [set(v) for v in first.manifest["pseudo_open"].values()]
        union = set()
        for group in groups:
            self.assertFalse(union & group)
            union.update(group)
        self.assertEqual(union, set(split_sample_ids(split)))

        target = make_split(n_per_class=2, classes=4, name="target")
        assert_target_quarantined(first, target)
        target.sample_meta[0] = split.sample_meta[0]
        with self.assertRaisesRegex(ValueError, "target leakage"):
            assert_target_quarantined(first, target)

        with self.assertRaisesRegex(ValueError, "batch length mismatch"):
            _decollate_sample_metadata({"dataset_index": torch.tensor([1, 2])}, 3)

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

    def test_stage03_pa2_backbone_config_is_target_quarantined_four_class_ota(self):
        repo_root = Path(__file__).resolve().parents[1]
        cfg_path = (
            repo_root
            / "manifests"
            / "configs"
            / "mth602_stage03"
            / "archC_backbone_knownonly_unkPA2_c16384_seed0.json"
        )
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg["unknown_pas"], ["PA2"])
        self.assertEqual(set(cfg["pas"]), {"PA1", "PA2", "PA3", "PA4", "PA8"})
        self.assertEqual(len(set(cfg["pas"]) - set(cfg["unknown_pas"])), 4)
        self.assertEqual(cfg["cache_len"], 16384)
        self.assertEqual(cfg["source_type"], "ota")
        self.assertEqual(cfg["source_name"], "ota_core_high_run01")
        self.assertEqual(cfg["dataset_tag"], "ota_core_high_run01")
        self.assertEqual(cfg["noise_tag"], "high_run01")
        self.assertEqual(cfg["early_stopping_mode"], "known_only")
        self.assertEqual(cfg["model_selection_metric"], "val_macro_f1")
        self.assertEqual(cfg["open_val_frac"], 0.0)
        self.assertFalse(cfg["build_balanced_val_open"])
        self.assertFalse(cfg["require_true_val_open"])
        self.assertFalse(cfg["allow_val_open_fallback"])
        self.assertTrue(cfg["quarantine_target_until_test"])
        self.assertTrue(cfg["skip_cache_build"])
        self.assertFalse(cfg["force_rebuild_cache"])


if __name__ == "__main__":
    unittest.main()
