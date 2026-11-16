from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from cross_surrogate_dqnguard import (
    apply_dqn_score_threshold,
    select_cross_surrogate_candidate,
    summarize_cross_surrogate_candidate,
)


class DummyDQN:
    def __init__(self, scores):
        self._scores = np.asarray(scores, dtype=np.float32)

    def score(self, split):
        assert len(split.closed_pred) == len(self._scores)
        return self._scores


def _metric(unknown_f1, unknown_recall, osr_macro_f1, auroc=0.8):
    return {
        "unknown_f1": float(unknown_f1),
        "unknown_recall": float(unknown_recall),
        "osr_macro_f1": float(osr_macro_f1),
        "unknown_auroc": float(auroc),
    }


def test_candidate_summary_rejects_own_surrogate_diagonal():
    rows = {
        "PA1": _metric(0.99, 0.99, 0.99),
        "PA3": _metric(0.80, 0.81, 0.82),
    }
    with pytest.raises(ValueError, match="diagonal"):
        summarize_cross_surrogate_candidate(
            "PA1",
            rows,
            known_guard_reject_rate=0.05,
        )


def test_selection_prioritizes_worst_case_cross_surrogate_transfer():
    # PA1 has the better mean, but one catastrophic off-diagonal failure.
    summaries = {
        "PA1": {
            "worst_cross_unknown_f1": 0.20,
            "mean_cross_unknown_f1": 0.83,
            "mean_cross_osr_macro_f1": 0.88,
            "known_guard_reject_rate": 0.04,
        },
        "PA3": {
            "worst_cross_unknown_f1": 0.72,
            "mean_cross_unknown_f1": 0.76,
            "mean_cross_osr_macro_f1": 0.81,
            "known_guard_reject_rate": 0.05,
        },
    }
    assert select_cross_surrogate_candidate(summaries) == "PA3"


def test_candidate_summary_uses_only_supplied_off_diagonal_rows():
    rows = {
        "PA3": _metric(0.70, 0.75, 0.80, 0.81),
        "PA4": _metric(0.85, 0.90, 0.84, 0.88),
        "PA8": _metric(0.76, 0.78, 0.82, 0.83),
    }
    out = summarize_cross_surrogate_candidate(
        "PA1",
        rows,
        known_guard_reject_rate=0.051,
    )
    assert out["eval_surrogates"] == ["PA3", "PA4", "PA8"]
    assert out["n_cross_surrogates"] == 3
    assert np.isclose(out["worst_cross_unknown_f1"], 0.70)
    assert np.isclose(out["mean_cross_unknown_f1"], (0.70 + 0.85 + 0.76) / 3)
    assert np.isclose(out["known_guard_reject_rate"], 0.051)


def test_known_only_score_threshold_application():
    split = SimpleNamespace(
        closed_pred=np.asarray([0, 1, 2, 3], dtype=int)
    )
    dqn = DummyDQN([-0.2, 0.1, 0.5, 1.2])
    pred = apply_dqn_score_threshold(
        dqn,
        split,
        threshold=0.5,
        unknown_label=4,
    )
    assert pred["is_unknown"].tolist() == [False, False, True, True]
    assert pred["final_pred"].tolist() == [0, 1, 4, 4]
    assert np.allclose(pred["unknown_score"], [-0.2, 0.1, 0.5, 1.2])
