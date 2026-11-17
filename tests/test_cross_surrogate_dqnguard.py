from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest


def _install_lightweight_dependency_stubs():
    """Isolate pure Architecture-B logic from unavailable GPU dependencies.

    Workspace Shell candidate-pytest intentionally does not carry PyTorch.
    These tests exercise selection/summarization/threshold application only,
    so replace heavy runtime modules with the minimum import surface required
    by cross_surrogate_dqnguard.
    """
    dqn_osr = ModuleType("dqn_osr")
    dqn_osr.DQNOSR = type("DQNOSR", (), {})
    sys.modules.setdefault("dqn_osr", dqn_osr)

    multisurrogate = ModuleType("multisurrogate_dqnguard")
    multisurrogate.CalibrationPartitions = type("CalibrationPartitions", (), {})
    multisurrogate.EmpiricalCDFNormalizer = type("EmpiricalCDFNormalizer", (), {})
    multisurrogate.PredictedClassBands = type("PredictedClassBands", (), {})
    multisurrogate.SurrogateGuard = type("SurrogateGuard", (), {})

    def _unexpected_runtime_call(*_args, **_kwargs):
        raise AssertionError("heavy runtime dependency unexpectedly exercised")

    multisurrogate.assert_target_quarantined = _unexpected_runtime_call
    multisurrogate.fit_surrogate_guard = _unexpected_runtime_call
    multisurrogate.known_only_threshold = _unexpected_runtime_call
    sys.modules.setdefault("multisurrogate_dqnguard", multisurrogate)

    osr_core = ModuleType("osr_core")
    osr_core.BackbonePayload = type("BackbonePayload", (), {})
    osr_core.SplitOutputs = type("SplitOutputs", (), {})
    osr_core.evaluate_osr_predictions = _unexpected_runtime_call
    sys.modules.setdefault("osr_core", osr_core)


_install_lightweight_dependency_stubs()

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



def test_evaluator_materializes_target_only_after_winner_freeze():
    import ast
    from pathlib import Path

    source = Path("experiments/pa_eval_cross_surrogate_dqnguard.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)

    fit_line = None
    target_extract_line = None
    prefit_payload_includes = None

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "fit":
                fit_line = node.lineno if fit_line is None else min(fit_line, node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "build_backbone_payload":
                for kw in node.keywords:
                    if kw.arg == "include" and isinstance(kw.value, ast.Tuple):
                        prefit_payload_includes = [
                            elt.value for elt in kw.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
            if node.func.id == "extract_backbone_outputs":
                if (
                    len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value == "test_open"
                ):
                    target_extract_line = node.lineno

    assert prefit_payload_includes == ["val_known", "test_known"]
    assert fit_line is not None
    assert target_extract_line is not None
    assert target_extract_line > fit_line




def test_evaluator_allows_empty_precreated_output_dir_and_rejects_nonempty():
    import ast
    from pathlib import Path

    source = Path("experiments/pa_eval_cross_surrogate_dqnguard.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)

    # Structural regression: the evaluator must distinguish an empty
    # workflow-created directory from a non-empty prior result directory.
    text = source
    assert "if any(out.iterdir()):" in text
    assert "Refusing to overwrite non-empty output directory" in text
    assert "Refusing to overwrite existing output directory" not in text
    assert "if not out.is_dir():" in text



def test_b2_band_path_uses_only_candidate_own_pseudo_surrogate():
    from pathlib import Path

    text = Path("cross_surrogate_dqnguard.py").read_text(encoding="utf-8")
    assert "use_class_conditional_bands" in text
    assert "PredictedClassBands(" in text
    assert "bands.transform(partitions.pseudo_open[surrogate])" in text
    assert "fit_surrogate_guard(" in text
    assert '"candidate_guard_training": "own_pseudo_surrogate_only"' in text
    assert '"composite_score": "dqn_margin_plus_guard_cdf"' in text


def test_b2_evaluator_keeps_target_materialization_after_candidate_freeze():
    from pathlib import Path

    text = Path("experiments/pa_eval_cross_surrogate_dqnguard.py").read_text(
        encoding="utf-8"
    )
    assert "--class-conditional-bands" in text
    assert "use_class_conditional_bands=args.class_conditional_bands" in text
    fit_pos = text.index("method.fit(payload, partitions)")
    target_pos = text.index('"test_open"', fit_pos)
    assert target_pos > fit_pos


def test_b3_search_is_bounded_and_does_not_change_dqn_state():
    from pathlib import Path

    text = Path("cross_surrogate_dqnguard.py").read_text(encoding="utf-8")
    assert 'B3_BAND_WEIGHT_RULES = (' in text
    for rule in (
        "uniform",
        "gap_only",
        "variance_only",
        "energy_only",
        "gap_variance_equal",
        "gap_energy_equal",
        "variance_energy_equal",
        "absolute_median_separation",
    ):
        assert f'"{rule}"' in text
    assert "B3_GUARD_SCALES = (0.5, 1.0, 2.0)" in text
    assert "tune_band_weights" in text
    assert '"selection_evidence": "off_diagonal_pseudo_open_only"' in text
    assert '"dqn_retrained_per_weight": False' in text


def test_b3_search_does_not_materialize_target_before_fit():
    from pathlib import Path

    text = Path("experiments/pa_eval_cross_surrogate_dqnguard.py").read_text(
        encoding="utf-8"
    )
    assert "--tune-band-weights" in text
    fit_pos = text.index("method.fit(payload, partitions)")
    target_pos = text.index('"test_open"', fit_pos)
    assert target_pos > fit_pos
