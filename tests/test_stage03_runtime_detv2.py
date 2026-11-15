import unittest

import torch
from torch.utils.data import TensorDataset

from discriminate import configure_training_reproducibility
from prepData import make_seeded_dataloader


class Stage03RuntimeDetV2Tests(unittest.TestCase):
    def test_seeded_loader_repeats_shuffle_order(self):
        ds = TensorDataset(torch.arange(128))

        def order():
            loader = make_seeded_dataloader(
                ds, batch_size=8, shuffle=True, num_workers=0,
                pin_memory=False, seed=17, stream_id=11,
            )
            return torch.cat([x[0] for x in loader]).tolist()

        self.assertEqual(order(), order())

    def test_seeded_loader_changes_with_seed(self):
        ds = TensorDataset(torch.arange(128))

        def order(seed):
            loader = make_seeded_dataloader(
                ds, batch_size=8, shuffle=True, num_workers=0,
                pin_memory=False, seed=seed, stream_id=11,
            )
            return torch.cat([x[0] for x in loader]).tolist()

        self.assertNotEqual(order(17), order(18))

    def test_invalid_deterministic_profile_fails_closed(self):
        with self.assertRaises(ValueError):
            configure_training_reproducibility({
                "seed": 0,
                "deterministic_training": True,
                "deterministic_profile": "bogus",
            })


if __name__ == "__main__":
    unittest.main()
