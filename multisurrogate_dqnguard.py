from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Sequence

import numpy as np

from dqn_osr import (
    DQNOSR,
    compute_energy_from_logits,
    compute_logit_variance,
    compute_top2_gap_from_probs,
)
from osr_core import BackbonePayload, SplitOutputs


ROLE_NAMES = ("fit", "guard", "norm", "threshold", "pseudo")


def _stable_json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    except Exception:
        return repr(value)


def sample_identity(meta: Any, fallback_index: int) -> str:
    if meta is None:
        return f"index:{int(fallback_index)}"
    return hashlib.sha256(_stable_json(meta).encode("utf-8")).hexdigest()


def split_sample_ids(split: SplitOutputs) -> list[str]:
    meta = getattr(split, "sample_meta", None)
    if meta is None:
        return [sample_identity(None, i) for i in range(len(split.y_true))]
    if len(meta) != len(split.y_true):
        raise ValueError("sample_meta length does not match split length")
    return [sample_identity(item, i) for i, item in enumerate(meta)]


def take_split(split: SplitOutputs, indices: Sequence[int], suffix: str) -> SplitOutputs:
    idx = np.asarray(indices, dtype=int)
    meta = None
    if getattr(split, "sample_meta", None) is not None:
        meta = [split.sample_meta[int(i)] for i in idx]
    return SplitOutputs(
        split_name=f"{split.split_name}_{suffix}",
        y_true=np.asarray(split.y_true)[idx],
        logits=np.asarray(split.logits)[idx],
        features=np.asarray(split.features)[idx],
        closed_pred=np.asarray(split.closed_pred)[idx],
        probs=np.asarray(split.probs)[idx],
        sample_meta=meta,
    )


def concat_splits(splits: Iterable[SplitOutputs], name: str) -> SplitOutputs:
    items = list(splits)
    if not items:
        raise ValueError("concat_splits requires at least one split")
    metas = [getattr(s, "sample_meta", None) for s in items]
    meta = None
    if any(m is not None for m in metas):
        meta = []
        for split, m in zip(items, metas):
            meta.extend(list(m) if m is not None else [None] * len(split.y_true))
    return SplitOutputs(
        split_name=name,
        y_true=np.concatenate([np.asarray(s.y_true) for s in items], axis=0),
        logits=np.concatenate([np.asarray(s.logits) for s in items], axis=0),
        features=np.concatenate([np.asarray(s.features) for s in items], axis=0),
        closed_pred=np.concatenate([np.asarray(s.closed_pred) for s in items], axis=0),
        probs=np.concatenate([np.asarray(s.probs) for s in items], axis=0),
        sample_meta=meta,
    )


@dataclass(frozen=True)
class CalibrationPartitions:
    known_fit: SplitOutputs
    known_guard: SplitOutputs
    known_norm: SplitOutputs
    known_threshold: SplitOutputs
    pseudo_open: Dict[str, SplitOutputs]
    manifest: Dict[str, Any]


def partition_known_calibration(
    split: SplitOutputs,
    class_names: Sequence[str],
    seed: int = 0,
) -> CalibrationPartitions:
    """
    Deterministically split each known validation class into five disjoint roles.

    Four roles remain known-only (fit/guard/norm/threshold). The fifth role is
    the class-specific internal pseudo-open evidence P_s. No sample is reused.
    """
    y = np.asarray(split.y_true, dtype=int)
    names = list(class_names)
    if len(names) < 2:
        raise ValueError("at least two known classes are required")
    if np.any(y < 0):
        raise ValueError("known calibration split contains unknown labels")

    by_role: Dict[str, list[int]] = {r: [] for r in ROLE_NAMES[:-1]}
    pseudo_indices: Dict[str, list[int]] = {}
    per_class: Dict[str, Dict[str, list[int]]] = {}

    for cls, name in enumerate(names):
        cls_idx = np.flatnonzero(y == cls)
        if len(cls_idx) < len(ROLE_NAMES):
            raise ValueError(
                f"class {name} has {len(cls_idx)} samples; need >= {len(ROLE_NAMES)}"
            )
        rng = np.random.default_rng(int(seed) + 1009 * (cls + 1))
        perm = rng.permutation(cls_idx)
        chunks = np.array_split(perm, len(ROLE_NAMES))
        class_roles: Dict[str, list[int]] = {}
        for role, chunk in zip(ROLE_NAMES, chunks):
            vals = [int(i) for i in chunk]
            class_roles[role] = vals
            if role == "pseudo":
                pseudo_indices[name] = vals
            else:
                by_role[role].extend(vals)
        per_class[name] = class_roles

    ids = split_sample_ids(split)
    role_ids: Dict[str, list[str]] = {}
    for role in ROLE_NAMES[:-1]:
        role_ids[role] = [ids[i] for i in by_role[role]]
    pseudo_ids = {name: [ids[i] for i in idxs] for name, idxs in pseudo_indices.items()}

    all_sets = [set(v) for v in role_ids.values()] + [set(v) for v in pseudo_ids.values()]
    for i, a in enumerate(all_sets):
        for b in all_sets[i + 1 :]:
            if a.intersection(b):
                raise RuntimeError("calibration partition overlap detected")

    manifest = {
        "schema": "multisurrogate-calibration-partition.v1",
        "seed": int(seed),
        "roles": {k: sorted(v) for k, v in role_ids.items()},
        "pseudo_open": {k: sorted(v) for k, v in pseudo_ids.items()},
        "per_class_counts": {
            name: {role: len(indices) for role, indices in roles.items()}
            for name, roles in per_class.items()
        },
    }
    manifest["sha256"] = hashlib.sha256(
        _stable_json(manifest).encode("utf-8")
    ).hexdigest()

    return CalibrationPartitions(
        known_fit=take_split(split, sorted(by_role["fit"]), "known_fit"),
        known_guard=take_split(split, sorted(by_role["guard"]), "known_guard"),
        known_norm=take_split(split, sorted(by_role["norm"]), "known_norm"),
        known_threshold=take_split(split, sorted(by_role["threshold"]), "known_threshold"),
        pseudo_open={
            name: take_split(split, sorted(idxs), f"pseudo_{name}")
            for name, idxs in pseudo_indices.items()
        },
        manifest=manifest,
    )


def assert_target_quarantined(
    partitions: CalibrationPartitions,
    target_split: SplitOutputs,
) -> None:
    target_ids = set(split_sample_ids(target_split))
    used = set()
    for key in ("fit", "guard", "norm", "threshold"):
        used.update(partitions.manifest["roles"][key])
    for values in partitions.manifest["pseudo_open"].values():
        used.update(values)
    overlap = target_ids.intersection(used)
    if overlap:
        raise ValueError(f"target leakage detected for {len(overlap)} sample identities")


def guard_features(split: SplitOutputs, temperature: float = 1.0) -> np.ndarray:
    gap = compute_top2_gap_from_probs(np.asarray(split.probs))
    var = compute_logit_variance(np.asarray(split.logits))
    energy = compute_energy_from_logits(np.asarray(split.logits), temperature=temperature)
    return np.stack([gap, var, energy], axis=1).astype(np.float64)


class PredictedClassBands:
    def __init__(
        self,
        percentiles: tuple[float, float] = (5.0, 95.0),
        min_samples_per_class: int = 5,
        temperature: float = 1.0,
    ):
        self.percentiles = tuple(float(x) for x in percentiles)
        self.min_samples_per_class = int(min_samples_per_class)
        self.temperature = float(temperature)
        self.bands_: Dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self.global_band_: tuple[np.ndarray, np.ndarray] | None = None

    def fit(self, split: SplitOutputs) -> "PredictedClassBands":
        feats = guard_features(split, temperature=self.temperature)
        pred = np.asarray(split.closed_pred, dtype=int)
        lo_q, hi_q = self.percentiles
        global_lo = np.percentile(feats, lo_q, axis=0)
        global_hi = np.percentile(feats, hi_q, axis=0)
        self.global_band_ = (global_lo, global_hi)
        self.bands_ = {}
        for cls in sorted(np.unique(pred)):
            idx = np.flatnonzero(pred == cls)
            if len(idx) >= self.min_samples_per_class:
                lo = np.percentile(feats[idx], lo_q, axis=0)
                hi = np.percentile(feats[idx], hi_q, axis=0)
                self.bands_[int(cls)] = (lo, hi)
        return self

    @staticmethod
    def _distance(values: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> np.ndarray:
        width = np.maximum(hi - lo, 1e-8)
        below = np.maximum(lo - values, 0.0) / width
        above = np.maximum(values - hi, 0.0) / width
        return below + above

    def transform(self, split: SplitOutputs) -> np.ndarray:
        if self.global_band_ is None:
            raise RuntimeError("bands must be fitted first")
        feats = guard_features(split, temperature=self.temperature)
        pred = np.asarray(split.closed_pred, dtype=int)
        out = np.zeros_like(feats, dtype=np.float64)
        for cls in np.unique(pred):
            idx = np.flatnonzero(pred == cls)
            lo, hi = self.bands_.get(int(cls), self.global_band_)
            out[idx] = self._distance(feats[idx], lo, hi)
        return out


class EmpiricalCDFNormalizer:
    def __init__(self):
        self.sorted_known_: np.ndarray | None = None

    def fit(self, known_scores: np.ndarray) -> "EmpiricalCDFNormalizer":
        values = np.asarray(known_scores, dtype=float).reshape(-1)
        if values.size == 0 or not np.isfinite(values).all():
            raise ValueError("known normalization scores must be finite and nonempty")
        self.sorted_known_ = np.sort(values)
        return self

    def transform(self, scores: np.ndarray) -> np.ndarray:
        if self.sorted_known_ is None:
            raise RuntimeError("normalizer must be fitted first")
        values = np.asarray(scores, dtype=float)
        ranks = np.searchsorted(self.sorted_known_, values, side="right")
        return ranks.astype(np.float64) / float(len(self.sorted_known_))


@dataclass
class SurrogateGuard:
    surrogate: str
    weights: np.ndarray
    normalizer: EmpiricalCDFNormalizer

    def raw(self, distance_features: np.ndarray) -> np.ndarray:
        return np.asarray(distance_features, dtype=float) @ self.weights

    def score(self, distance_features: np.ndarray) -> np.ndarray:
        return self.normalizer.transform(self.raw(distance_features))


def fit_surrogate_guard(
    surrogate: str,
    known_distance_features: np.ndarray,
    pseudo_distance_features: np.ndarray,
) -> SurrogateGuard:
    known = np.asarray(known_distance_features, dtype=float)
    pseudo = np.asarray(pseudo_distance_features, dtype=float)
    if known.ndim != 2 or pseudo.ndim != 2 or known.shape[1] != pseudo.shape[1]:
        raise ValueError("guard distance feature shapes are incompatible")
    separation = np.maximum(
        np.median(pseudo, axis=0) - np.median(known, axis=0),
        0.0,
    )
    if float(separation.sum()) <= 0.0:
        weights = np.full(known.shape[1], 1.0 / known.shape[1], dtype=float)
    else:
        weights = separation / separation.sum()
    raw_known = known @ weights
    normalizer = EmpiricalCDFNormalizer().fit(raw_known)
    return SurrogateGuard(surrogate=surrogate, weights=weights, normalizer=normalizer)


def aggregate_max_guard(guard_scores: Mapping[str, np.ndarray]) -> np.ndarray:
    if not guard_scores:
        raise ValueError("at least one surrogate guard score is required")
    arrays = [np.asarray(guard_scores[k], dtype=float) for k in sorted(guard_scores)]
    shape = arrays[0].shape
    if any(a.shape != shape for a in arrays):
        raise ValueError("surrogate guard score shapes do not match")
    return np.max(np.stack(arrays, axis=0), axis=0)


def known_only_threshold(scores: np.ndarray, budget: float = 0.05) -> tuple[float, float]:
    values = np.asarray(scores, dtype=float).reshape(-1)
    if values.size == 0 or not np.isfinite(values).all():
        raise ValueError("known threshold scores must be finite and nonempty")
    if not (0.0 <= float(budget) <= 1.0):
        raise ValueError("budget must be in [0,1]")
    threshold = float(np.percentile(values, 100.0 * (1.0 - float(budget))))
    realized = float(np.mean(values >= threshold))
    return threshold, realized


class MultiSurrogateHybridDQNGuard:
    """
    Architecture C: one DQN score plus max-aggregated surrogate-specific
    deterministic guards, with one known-only final threshold.
    """

    method_name = "multisurrogate_hybrid_dqnguard_c"

    def __init__(
        self,
        *,
        budget: float = 0.05,
        seed: int = 42,
        dqn_kwargs: Dict[str, Any] | None = None,
    ):
        self.budget = float(budget)
        self.seed = int(seed)
        kwargs = dict(dqn_kwargs or {})
        kwargs.setdefault("state_mode", "softmax3")
        kwargs.setdefault("seed", self.seed)
        kwargs.setdefault("device", "cpu")
        self.dqn = DQNOSR(**kwargs)
        self.bands = PredictedClassBands()
        self.guards_: Dict[str, SurrogateGuard] = {}
        self.threshold_: float | None = None
        self.threshold_known_reject_cal_: float | None = None
        self.partition_manifest_: Dict[str, Any] | None = None
        self.fitted_ = False

    def fit(
        self,
        payload: BackbonePayload,
        partitions: CalibrationPartitions,
    ) -> None:
        if payload.test_open is not None:
            assert_target_quarantined(partitions, payload.test_open)

        pseudo_pool = concat_splits(
            [partitions.pseudo_open[k] for k in sorted(partitions.pseudo_open)],
            "pseudo_open_pool",
        )
        self.dqn.fit(
            payload,
            calibration={
                "calibration_known": partitions.known_fit,
                "calibration_open": pseudo_pool,
                "calibration_mode": "internal_multisurrogate_pool",
            },
        )

        self.bands.fit(partitions.known_guard)
        norm_dist = self.bands.transform(partitions.known_norm)

        self.guards_ = {}
        for surrogate, split in sorted(partitions.pseudo_open.items()):
            pseudo_dist = self.bands.transform(split)
            self.guards_[surrogate] = fit_surrogate_guard(
                surrogate,
                norm_dist,
                pseudo_dist,
            )

        threshold_scores = self.score_unthresholded(partitions.known_threshold)
        threshold, realized = known_only_threshold(threshold_scores, budget=self.budget)
        self.threshold_ = threshold
        self.threshold_known_reject_cal_ = realized
        self.partition_manifest_ = copy.deepcopy(partitions.manifest)
        self.fitted_ = True

    def guard_score(self, split: SplitOutputs) -> np.ndarray:
        if not self.guards_:
            raise RuntimeError("surrogate guards are not fitted")
        distances = self.bands.transform(split)
        scores = {name: guard.score(distances) for name, guard in self.guards_.items()}
        return aggregate_max_guard(scores)

    def score_unthresholded(self, split: SplitOutputs) -> np.ndarray:
        dqn_margin = self.dqn.score(split).astype(np.float64)
        return (dqn_margin + self.guard_score(split)).astype(np.float64)

    def score(self, split: SplitOutputs) -> np.ndarray:
        if self.threshold_ is None:
            raise RuntimeError("method must be fitted first")
        return self.score_unthresholded(split)

    def predict(self, split: SplitOutputs, unknown_label: int) -> Dict[str, np.ndarray]:
        if self.threshold_ is None:
            raise RuntimeError("method must be fitted first")
        score = self.score_unthresholded(split)
        is_unknown = score >= self.threshold_
        closed_pred = np.asarray(split.closed_pred, dtype=int).copy()
        final_pred = closed_pred.copy()
        final_pred[is_unknown] = int(unknown_label)
        return {
            "unknown_score": score.astype(np.float32),
            "is_unknown": is_unknown.astype(bool),
            "closed_pred": closed_pred,
            "final_pred": final_pred,
            "dqn_margin": self.dqn.score(split).astype(np.float32),
            "guard_multi": self.guard_score(split).astype(np.float32),
        }

    def get_params(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "budget": self.budget,
            "seed": self.seed,
            "threshold": self.threshold_,
            "threshold_known_reject_cal": self.threshold_known_reject_cal_,
            "partition_manifest": copy.deepcopy(self.partition_manifest_),
            "guard_aggregation": "max",
            "guard_weights": {
                name: guard.weights.tolist() for name, guard in sorted(self.guards_.items())
            },
            "dqn_params": self.dqn.get_params(),
        }
