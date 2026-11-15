import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
A = (ROOT / ".github/workflows/lambda-ci-scientific.yml").read_text()
B = (ROOT / ".github/workflows/lambda-ci-scientific-2.yml").read_text()

GPU0 = "GPU-a333e68b-d1dc-6d25-1678-97b527bf55ea"
GPU1 = "GPU-cfed3394-a935-63aa-9325-c4cae7b568b6"


class ScientificDualLaneWorkflowTests(unittest.TestCase):
    def test_lane_b_is_separate_single_gpu_route(self):
        self.assertIn("startsWith(github.event.comment.body, '/lambda-scientific-2 ')", B)
        self.assertIn("runs-on: lambda-padataset-scientific-single-gpu-2", B)
        self.assertIn(GPU1, B)
        self.assertNotIn(GPU0, B)
        self.assertIn("workload=scientific-single-gpu-2", B)

    def test_lane_b_preserves_scientific_bounds(self):
        for marker in (
            "github.event.issue.pull_request",
            "github.actor == 'adamtrott78'",
            "github.event.comment.author_association == 'OWNER'",
            "expected_sha",
            "actual_sha",
            "head_repo",
            "skip_cache_build",
            "force_rebuild_cache",
            "cache_len",
            'cfg.get("unknown_pas") != ["PA2"]',
            'cfg.get("early_stopping_mode") != "known_only"',
            'cfg.get("quarantine_target_until_test") is not True',
            'float(cfg.get("open_val_frac", -1)) != 0.0',
            'd["threshold"]["source"] == "known_only"',
            'd["provenance"]["target_labels_used_for_tuning"] is False',
            'if not payload["cuda_available"] or payload["cuda_device_count"] != 1',
        ):
            self.assertIn(marker, A)
            self.assertIn(marker, B)

    def test_lane_b_artifacts_are_namespaced(self):
        self.assertIn("name: padataset-scientific-2-${{ github.run_id }}", B)


if __name__ == "__main__":
    unittest.main()
