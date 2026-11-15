import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG_ROOT = ROOT / "manifests" / "configs" / "mth602_stage03"


class Stage03DeterministicReplicateTests(unittest.TestCase):
    def test_training_path_binds_config_seed_to_all_rngs(self):
        source = (ROOT / "discriminate.py").read_text()
        for marker in (
            "random.seed(seed)",
            "np.random.seed(seed)",
            "torch.manual_seed(seed)",
            "torch.cuda.manual_seed_all(seed)",
            "torch.use_deterministic_algorithms(True)",
            "torch.backends.cudnn.benchmark = False",
            "torch.backends.cudnn.deterministic = True",
            'os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")',
        ):
            self.assertIn(marker, source)

    def test_stage03_overlap_probe_is_bounded_deterministic_and_quarantined(self):
        path = CFG_ROOT / "perf_strict_tf32_w4_overlap_detv2.json"
        cfg = json.loads(path.read_text())
        self.assertTrue(cfg["throughput_probe"])
        self.assertEqual(cfg["throughput_probe_train_samples"], 32768)
        self.assertEqual(cfg["throughput_probe_val_samples"], 4096)
        self.assertTrue(cfg["deterministic_training"])
        self.assertEqual(cfg["deterministic_profile"], "strict_tf32")
        self.assertEqual(cfg["num_workers"], 4)
        self.assertEqual(cfg["unknown_pas"], ["PA2"])
        self.assertTrue(cfg["quarantine_target_until_test"])
        self.assertEqual(cfg["open_val_frac"], 0)
        self.assertFalse(cfg["build_balanced_val_open"])
        self.assertFalse(cfg["allow_val_open_fallback"])
        self.assertEqual(cfg["cache_len"], 16384)

    def test_stage03_deterministic_replicates_are_exact_and_quarantined(self):
        for seed in (0, 1, 2):
            path = CFG_ROOT / (
                f"archC_backbone_knownonly_unkPA2_c16384_seed{seed}_detv1.json"
            )
            cfg = json.loads(path.read_text())
            self.assertEqual(cfg["seed"], seed)
            self.assertEqual(cfg["manifold_balance_seed"], seed)
            self.assertTrue(cfg["deterministic_training"])
            self.assertEqual(cfg["unknown_pas"], ["PA2"])
            self.assertTrue(cfg["quarantine_target_until_test"])
            self.assertEqual(cfg["early_stopping_mode"], "known_only")
            self.assertEqual(cfg["open_val_frac"], 0)
            self.assertFalse(cfg["build_balanced_val_open"])
            self.assertFalse(cfg["allow_val_open_fallback"])
            self.assertEqual(cfg["cache_len"], 16384)
            self.assertIn(f"seed{seed}_detv1", cfg["run_name"])


if __name__ == "__main__":
    unittest.main()
