from __future__ import annotations

import copy
from typing import Any, Dict, Mapping

import numpy as np

from dqn_osr import DQNOSR
from multisurrogate_dqnguard import (
    CalibrationPartitions,
    EmpiricalCDFNormalizer,
    PredictedClassBands,
    SurrogateGuard,
    assert_target_quarantined,
    fit_surrogate_guard,
    known_only_threshold,
)
from osr_core import BackbonePayload, SplitOutputs, evaluate_osr_predictions


B3_BAND_WEIGHT_RULES = (
    "uniform",
    "gap_only",
    "variance_only",
    "energy_only",
    "gap_variance_equal",
    "gap_energy_equal",
    "variance_energy_equal",
    "absolute_median_separation",
)
B3_GUARD_SCALES = (0.5, 1.0, 2.0)


def _normalized_nonnegative(weights: np.ndarray) -> np.ndarray:
    values = np.asarray(weights, dtype=float).reshape(-1)
    if values.shape != (3,) or not np.isfinite(values).all():
        raise ValueError("band guard weights must be three finite values")
    values = np.maximum(values, 0.0)
    total = float(values.sum())
    if total <= 0.0:
        return np.full(3, 1.0 / 3.0, dtype=float)
    return values / total


def fit_b3_band_guard(
    surrogate: str,
    known_distance_features: np.ndarray,
    pseudo_distance_features: np.ndarray,
    weight_rule: str,
) -> SurrogateGuard:
    known = np.asarray(known_distance_features, dtype=float)
    pseudo = np.asarray(pseudo_distance_features, dtype=float)
    if known.ndim != 2 or pseudo.ndim != 2 or known.shape[1] != 3 or pseudo.shape[1] != 3:
        raise ValueError("B3 band distance feature shapes must be Nx3")

    fixed = {
        "uniform": [1.0, 1.0, 1.0],
        "gap_only": [1.0, 0.0, 0.0],
        "variance_only": [0.0, 1.0, 0.0],
        "energy_only": [0.0, 0.0, 1.0],
        "gap_variance_equal": [1.0, 1.0, 0.0],
        "gap_energy_equal": [1.0, 0.0, 1.0],
        "variance_energy_equal": [0.0, 1.0, 1.0],
    }
    if weight_rule in fixed:
        weights = _normalized_nonnegative(np.asarray(fixed[weight_rule], dtype=float))
    elif weight_rule == "absolute_median_separation":
        separation = np.abs(
            np.median(pseudo, axis=0) - np.median(known, axis=0)
        )
        weights = _normalized_nonnegative(separation)
    else:
        raise ValueError(f"Unsupported B3 band weight rule: {weight_rule}")

    raw_known = known @ weights
    normalizer = EmpiricalCDFNormalizer().fit(raw_known)
    return SurrogateGuard(
        surrogate=str(surrogate),
        weights=weights,
        normalizer=normalizer,
    )


def apply_unknown_score_threshold(
    score: np.ndarray,
    split: SplitOutputs,
    threshold: float,
    unknown_label: int,
) -> Dict[str, np.ndarray]:
    """Apply a known-only calibrated threshold to a frozen unknown score."""
    score = np.asarray(score, dtype=np.float32)
    is_unknown = score >= float(threshold)
    closed_pred = np.asarray(split.closed_pred, dtype=int).copy()
    final_pred = closed_pred.copy()
    final_pred[is_unknown] = int(unknown_label)
    return {
        "unknown_score": score,
        "is_unknown": is_unknown.astype(bool),
        "closed_pred": closed_pred,
        "final_pred": final_pred,
    }


def apply_dqn_score_threshold(
    dqn: DQNOSR,
    split: SplitOutputs,
    threshold: float,
    unknown_label: int,
) -> Dict[str, np.ndarray]:
    """Backward-compatible DQN-only threshold helper used by B0/B1 tests."""
    return apply_unknown_score_threshold(
        dqn.score(split),
        split,
        threshold,
        unknown_label,
    )


def summarize_cross_surrogate_candidate(
    train_surrogate: str,
    rows: Mapping[str, Mapping[str, Any]],
    known_guard_reject_rate: float,
) -> Dict[str, Any]:
    """
    Summarize only OFF-DIAGONAL pseudo-open evaluations.

    The candidate's own training surrogate must never appear in rows.
    """
    if train_surrogate in rows:
        raise ValueError(
            f"Own-surrogate diagonal leaked into selection rows: {train_surrogate}"
        )
    if not rows:
        raise ValueError(f"No off-diagonal rows for candidate {train_surrogate}")

    unknown_f1 = np.asarray(
        [float(v["unknown_f1"]) for v in rows.values()], dtype=float
    )
    unknown_recall = np.asarray(
        [float(v["unknown_recall"]) for v in rows.values()], dtype=float
    )
    osr_macro = np.asarray(
        [float(v["osr_macro_f1"]) for v in rows.values()], dtype=float
    )
    aurocs = [
        float(v["unknown_auroc"])
        for v in rows.values()
        if v.get("unknown_auroc") is not None
    ]

    return {
        "train_surrogate": str(train_surrogate),
        "n_cross_surrogates": int(len(rows)),
        "eval_surrogates": sorted(str(k) for k in rows),
        "worst_cross_unknown_f1": float(np.min(unknown_f1)),
        "mean_cross_unknown_f1": float(np.mean(unknown_f1)),
        "worst_cross_unknown_recall": float(np.min(unknown_recall)),
        "mean_cross_unknown_recall": float(np.mean(unknown_recall)),
        "mean_cross_osr_macro_f1": float(np.mean(osr_macro)),
        "mean_cross_unknown_auroc": (
            float(np.mean(aurocs)) if aurocs else None
        ),
        "known_guard_reject_rate": float(known_guard_reject_rate),
    }


def select_cross_surrogate_candidate(
    summaries: Mapping[str, Mapping[str, Any]],
) -> str:
    """
    Select for TRANSFERABILITY, not home-surrogate performance.

    Priority:
      1. maximize worst off-diagonal unknown F1
      2. maximize mean off-diagonal unknown F1
      3. maximize mean off-diagonal OSR macro-F1
      4. minimize known-guard rejection
      5. deterministic lexical surrogate name tie-break
    """
    if not summaries:
        raise ValueError("No cross-surrogate candidate summaries")

    def key(item):
        name, row = item
        return (
            float(row["worst_cross_unknown_f1"]),
            float(row["mean_cross_unknown_f1"]),
            float(row["mean_cross_osr_macro_f1"]),
            -float(row["known_guard_reject_rate"]),
            str(name),
        )

    return max(summaries.items(), key=key)[0]


class CrossSurrogateDQNGuardB:
    """
    Architecture B: one DQN candidate per pseudo-open surrogate, with
    leave-own-surrogate-out cross-surrogate selection.

    True target-open evidence is never used for fitting, thresholding or
    candidate selection. Each candidate is trained on:
      - known_fit
      - its OWN pseudo-open class

    Each candidate threshold is fitted on known_threshold only.

    Candidate S is selected using ONLY:
      - known_guard
      - pseudo-open classes T != S

    The own-surrogate diagonal is deliberately excluded.
    """

    method_name = "cross_surrogate_dqnguard_b"

    def __init__(
        self,
        *,
        state_mode: str = "softmax3",
        budget: float = 0.05,
        seed: int = 42,
        dqn_kwargs: Dict[str, Any] | None = None,
        use_class_conditional_bands: bool = False,
        tune_band_weights: bool = False,
    ):
        self.state_mode = str(state_mode)
        if self.state_mode not in {"softmax3", "expanded5"}:
            raise ValueError(
                f"Unsupported state_mode={self.state_mode!r}; "
                "expected softmax3 or expanded5"
            )
        self.budget = float(budget)
        self.seed = int(seed)
        self.dqn_kwargs = dict(dqn_kwargs or {})
        self.use_class_conditional_bands = bool(use_class_conditional_bands)
        self.tune_band_weights = bool(tune_band_weights)
        if self.tune_band_weights and not self.use_class_conditional_bands:
            raise ValueError("B3 band tuning requires class-conditional bands")

        self.candidates_: Dict[str, DQNOSR] = {}
        self.thresholds_: Dict[str, float] = {}
        self.threshold_known_reject_cal_: Dict[str, float] = {}
        self.cross_metrics_: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.candidate_summaries_: Dict[str, Dict[str, Any]] = {}
        self.bands_: PredictedClassBands | None = None
        self.candidate_guards_: Dict[str, SurrogateGuard] = {}
        self.candidate_guard_scales_: Dict[str, float] = {}

        self.selected_candidate_id_: str | None = None
        self.selected_surrogate_: str | None = None
        self.selected_dqn_: DQNOSR | None = None
        self.selected_threshold_: float | None = None
        self.partition_manifest_: Dict[str, Any] | None = None
        self.fitted_ = False

    def _make_dqn(self) -> DQNOSR:
        kwargs = dict(self.dqn_kwargs)
        kwargs.pop("state_mode", None)
        kwargs.setdefault("seed", self.seed)
        kwargs.setdefault("device", "cpu")
        return DQNOSR(state_mode=self.state_mode, **kwargs)

    def _candidate_score(
        self,
        dqn: DQNOSR,
        split: SplitOutputs,
        *,
        guard: SurrogateGuard | None,
        bands: PredictedClassBands | None,
        guard_scale: float = 1.0,
    ) -> np.ndarray:
        score = np.asarray(dqn.score(split), dtype=np.float64)
        if not self.use_class_conditional_bands:
            return score
        if guard is None or bands is None:
            raise RuntimeError("B2 class-conditional guard is not fitted")
        distance = bands.transform(split)
        return (score + float(guard_scale) * guard.score(distance)).astype(np.float64)

    def fit(
        self,
        payload: BackbonePayload,
        partitions: CalibrationPartitions,
    ) -> None:
        if payload.val_known is None:
            raise ValueError("Architecture B requires val_known")
        if payload.test_open is not None:
            # Identity-only leakage assertion. The target values are not used.
            assert_target_quarantined(partitions, payload.test_open)

        class_names = list(payload.meta["class_names"])
        pseudo_names = sorted(partitions.pseudo_open)
        if sorted(class_names) != pseudo_names:
            raise ValueError(
                "Architecture B requires exactly one pseudo-open partition per "
                f"known class; class_names={class_names}, pseudo={pseudo_names}"
            )
        if len(pseudo_names) < 3:
            raise ValueError("Architecture B requires at least three known classes")

        unknown_label = int(payload.meta["num_classes"])

        candidates: Dict[str, DQNOSR] = {}
        thresholds: Dict[str, float] = {}
        threshold_reject: Dict[str, float] = {}
        cross_metrics: Dict[str, Dict[str, Dict[str, Any]]] = {}
        summaries: Dict[str, Dict[str, Any]] = {}
        candidate_guards: Dict[str, SurrogateGuard] = {}
        candidate_guard_scales: Dict[str, float] = {}

        bands: PredictedClassBands | None = None
        known_norm_distance: np.ndarray | None = None
        if self.use_class_conditional_bands:
            bands = PredictedClassBands(
                percentiles=(5.0, 95.0),
                min_samples_per_class=5,
                temperature=1.0,
            ).fit(partitions.known_guard)
            known_norm_distance = bands.transform(partitions.known_norm)

        for surrogate in pseudo_names:
            dqn = self._make_dqn()
            dqn.fit(
                payload,
                calibration={
                    "calibration_mode": f"archB_train_{surrogate}",
                    "calibration_known": partitions.known_fit,
                    "calibration_open": partitions.pseudo_open[surrogate],
                },
            )
            candidates[surrogate] = dqn

            if not self.use_class_conditional_bands:
                specs = [(surrogate, None, 1.0, "none")]
            elif self.tune_band_weights:
                if bands is None or known_norm_distance is None:
                    raise RuntimeError("B3 band state missing")
                pseudo_distance = bands.transform(partitions.pseudo_open[surrogate])
                specs = []
                for weight_rule in B3_BAND_WEIGHT_RULES:
                    guard = fit_b3_band_guard(
                        surrogate,
                        known_norm_distance,
                        pseudo_distance,
                        weight_rule,
                    )
                    for guard_scale in B3_GUARD_SCALES:
                        candidate_id = (
                            f"{surrogate}|{weight_rule}|scale={guard_scale:g}"
                        )
                        specs.append(
                            (candidate_id, guard, float(guard_scale), weight_rule)
                        )
            else:
                if bands is None or known_norm_distance is None:
                    raise RuntimeError("B2 band state missing")
                guard = fit_surrogate_guard(
                    surrogate,
                    known_norm_distance,
                    bands.transform(partitions.pseudo_open[surrogate]),
                )
                specs = [(surrogate, guard, 1.0, "positive_median_separation_else_uniform")]

            for candidate_id, guard, guard_scale, weight_rule in specs:
                if guard is not None:
                    candidate_guards[candidate_id] = guard
                    candidate_guard_scales[candidate_id] = float(guard_scale)

                threshold_scores = self._candidate_score(
                    dqn,
                    partitions.known_threshold,
                    guard=guard,
                    bands=bands,
                    guard_scale=guard_scale,
                )
                threshold, realized = known_only_threshold(
                    threshold_scores,
                    budget=self.budget,
                )

                known_pred = apply_unknown_score_threshold(
                    self._candidate_score(
                        dqn,
                        partitions.known_guard,
                        guard=guard,
                        bands=bands,
                        guard_scale=guard_scale,
                    ),
                    partitions.known_guard,
                    threshold,
                    unknown_label,
                )
                known_guard_reject = float(np.mean(known_pred["is_unknown"]))

                rows: Dict[str, Dict[str, Any]] = {}
                for eval_surrogate in pseudo_names:
                    if eval_surrogate == surrogate:
                        continue
                    open_split = partitions.pseudo_open[eval_surrogate]
                    open_pred = apply_unknown_score_threshold(
                        self._candidate_score(
                            dqn,
                            open_split,
                            guard=guard,
                            bands=bands,
                            guard_scale=guard_scale,
                        ),
                        open_split,
                        threshold,
                        unknown_label,
                    )
                    rows[eval_surrogate] = evaluate_osr_predictions(
                        known_split=partitions.known_guard,
                        open_split=open_split,
                        known_pred=known_pred,
                        open_pred=open_pred,
                        known_class_names=class_names,
                        unknown_label_name="unknown",
                    )

                thresholds[candidate_id] = float(threshold)
                threshold_reject[candidate_id] = float(realized)
                cross_metrics[candidate_id] = rows
                summary = summarize_cross_surrogate_candidate(
                    surrogate,
                    rows,
                    known_guard_reject_rate=known_guard_reject,
                )
                summary["candidate_id"] = candidate_id
                summary["band_weight_rule"] = weight_rule
                summary["guard_scale"] = float(guard_scale)
                summary["threshold"] = float(threshold)
                summary["threshold_known_reject_cal"] = float(realized)
                summaries[candidate_id] = summary

        selected = select_cross_surrogate_candidate(summaries)
        selected_summary = summaries[selected]
        selected_surrogate = str(selected_summary["train_surrogate"])

        self.candidates_ = candidates
        self.thresholds_ = thresholds
        self.threshold_known_reject_cal_ = threshold_reject
        self.cross_metrics_ = cross_metrics
        self.candidate_summaries_ = summaries
        self.bands_ = bands
        self.candidate_guards_ = candidate_guards
        self.candidate_guard_scales_ = candidate_guard_scales
        self.selected_candidate_id_ = selected
        self.selected_surrogate_ = selected_surrogate
        self.selected_dqn_ = candidates[selected_surrogate]
        self.selected_threshold_ = thresholds[selected]
        self.partition_manifest_ = copy.deepcopy(partitions.manifest)
        self.fitted_ = True

    def score(self, split: SplitOutputs) -> np.ndarray:
        if not self.fitted_ or self.selected_dqn_ is None:
            raise RuntimeError("Architecture B must be fitted first")
        candidate_id = self.selected_candidate_id_ or self.selected_surrogate_
        guard = self.candidate_guards_.get(candidate_id)
        guard_scale = self.candidate_guard_scales_.get(candidate_id, 1.0)
        return self._candidate_score(
            self.selected_dqn_,
            split,
            guard=guard,
            bands=self.bands_,
            guard_scale=guard_scale,
        )

    def predict(
        self,
        split: SplitOutputs,
        unknown_label: int,
    ) -> Dict[str, np.ndarray]:
        if (
            not self.fitted_
            or self.selected_dqn_ is None
            or self.selected_threshold_ is None
        ):
            raise RuntimeError("Architecture B must be fitted first")
        return apply_unknown_score_threshold(
            self.score(split),
            split,
            self.selected_threshold_,
            unknown_label,
        )

    def get_params(self) -> Dict[str, Any]:
        selected_params = None
        if self.selected_dqn_ is not None:
            selected_params = self.selected_dqn_.get_params()
            # Keep result metadata compact; full training history is not needed
            # in the JSON record because the evaluator persists the selected
            # Q-network checkpoint separately.
            selected_params = copy.deepcopy(selected_params)
            selected_params.pop("train_history", None)

        band_params = None
        if self.use_class_conditional_bands:
            band_params = {
                "enabled": True,
                "features": ["top2_gap", "logit_variance", "energy"],
                "fit_role": "known_guard",
                "percentiles": [5.0, 95.0],
                "normalization_fit_role": "known_norm",
                "guard_weight_rule": (
                    "bounded_b3_search"
                    if self.tune_band_weights
                    else "positive_median_separation_else_uniform"
                ),
                "candidate_guard_training": "own_pseudo_surrogate_only",
                "guard_normalization": "empirical_known_cdf",
                "composite_score": "dqn_margin_plus_guard_cdf",
                "candidate_guard_weights": {
                    name: guard.weights.tolist()
                    for name, guard in sorted(self.candidate_guards_.items())
                },
                "candidate_guard_scales": copy.deepcopy(
                    self.candidate_guard_scales_
                ),
                "b3_search": (
                    {
                        "weight_rules": list(B3_BAND_WEIGHT_RULES),
                        "guard_scales": list(B3_GUARD_SCALES),
                        "selection_evidence": "off_diagonal_pseudo_open_only",
                        "dqn_retrained_per_weight": False,
                    }
                    if self.tune_band_weights
                    else None
                ),
            }

        return {
            "method_name": self.method_name,
            "architecture": "B",
            "state_mode": self.state_mode,
            "use_class_conditional_bands": self.use_class_conditional_bands,
            "tune_band_weights": self.tune_band_weights,
            "selected_candidate_id": self.selected_candidate_id_,
            "band_params": band_params,
            "budget": self.budget,
            "seed": self.seed,
            "selected_surrogate": self.selected_surrogate_,
            "selected_threshold": self.selected_threshold_,
            "thresholds": copy.deepcopy(self.thresholds_),
            "threshold_known_reject_cal": copy.deepcopy(
                self.threshold_known_reject_cal_
            ),
            "candidate_summaries": copy.deepcopy(self.candidate_summaries_),
            "cross_metrics": copy.deepcopy(self.cross_metrics_),
            "partition_manifest": copy.deepcopy(self.partition_manifest_),
            "selected_dqn_params": selected_params,
        }
