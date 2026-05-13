import copy
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple, List

import numpy as np
import torch
from sklearn.metrics import f1_score

from osr_core import BaseOSRMethod, BackbonePayload, SplitOutputs, evaluate_osr_predictions


DEFAULT_PAIR_MAP = {
    "PA2": "PA8",
    "PA8": "PA2",
    "PA3": "PA4",
    "PA4": "PA3",
}


def compute_top2_gap(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    scaled_logits = logits / float(temperature)
    probs = torch.softmax(torch.tensor(scaled_logits, dtype=torch.float32), dim=1).numpy()
    sorted_probs = np.sort(probs, axis=1)
    return sorted_probs[:, -1] - sorted_probs[:, -2]


def compute_logit_variance(logits: np.ndarray) -> np.ndarray:
    abs_logits = np.abs(logits)
    return np.var(abs_logits - abs_logits.mean(axis=1, keepdims=True), axis=1)


def compute_energy(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    scaled_logits = logits / float(temperature)
    return (
        float(temperature)
        * torch.logsumexp(torch.tensor(scaled_logits, dtype=torch.float32), dim=1)
    ).numpy()


def compute_varmax_flags(
    top2: np.ndarray,
    var: np.ndarray,
    energy: np.ndarray,
    thresholds: Dict[str, Any],
    pred_labels: np.ndarray,
) -> np.ndarray:
    t2_thr = float(thresholds["top2"])
    is_known = (top2 >= t2_thr)

    ambiguous = ~is_known
    var_bounds = np.array([thresholds["var"][int(c)] for c in pred_labels], dtype=float)
    v_lo, v_hi = var_bounds[:, 0], var_bounds[:, 1]
    is_known[ambiguous] |= ((var >= v_lo) & (var <= v_hi))[ambiguous]

    if "energy" in thresholds and thresholds["energy"]:
        ambiguous = ~is_known
        e_bounds = np.array([thresholds["energy"][int(c)] for c in pred_labels], dtype=float)
        e_lo, e_hi = e_bounds[:, 0], e_bounds[:, 1]
        is_known[ambiguous] |= ((energy >= e_lo) & (energy <= e_hi))[ambiguous]

    return is_known


def _band_distance(x: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    lo = bounds[:, 0]
    hi = bounds[:, 1]
    below = np.clip(lo - x, 0.0, None)
    above = np.clip(x - hi, 0.0, None)
    raw = below + above
    width = np.maximum(hi - lo, 1e-8)
    return raw / width


def _safe_percentile(values: np.ndarray, lo_hi: Tuple[float, float]) -> Tuple[float, float]:
    lo_p, hi_p = lo_hi
    return float(np.percentile(values, lo_p)), float(np.percentile(values, hi_p))

def _write_osr_progress_from_varmax(**payload) -> None:
    path = os.environ.get("PADATASET_OSR_PROGRESS_JSON")
    if not path:
        return
    try:
        p = Path(path)
        existing = {}
        if p.is_file():
            try:
                existing = json.loads(p.read_text())
            except Exception:
                existing = {}
        existing.update(payload)
        existing.setdefault("time", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(existing, indent=2))
        tmp.replace(p)
    except Exception:
        pass



def _subset_split(split: SplitOutputs, mask: np.ndarray, split_name: Optional[str] = None) -> SplitOutputs:
    idx = np.asarray(mask)
    if idx.dtype == bool:
        selected_idx = np.where(idx)[0]
    else:
        selected_idx = idx

    if split.sample_meta is None:
        sample_meta = None
    else:
        sample_meta = [split.sample_meta[int(i)] for i in selected_idx]

    return SplitOutputs(
        split_name=split_name or split.split_name,
        y_true=split.y_true[selected_idx],
        logits=split.logits[selected_idx],
        features=split.features[selected_idx],
        closed_pred=split.closed_pred[selected_idx],
        probs=split.probs[selected_idx],
        sample_meta=sample_meta,
    )


def _stratified_three_way_masks(
    labels: np.ndarray,
    fit_frac: float = 0.50,
    guard_frac: float = 0.25,
    seed: int = 0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    labels = np.asarray(labels)
    rng = np.random.default_rng(seed)

    fit_mask = np.zeros(len(labels), dtype=bool)
    guard_mask = np.zeros(len(labels), dtype=bool)
    score_mask = np.zeros(len(labels), dtype=bool)

    for cls in np.unique(labels):
        idx = np.where(labels == cls)[0]
        rng.shuffle(idx)
        n = len(idx)

        if n < 3:
            raise ValueError(
                f"Need at least 3 samples per class for three-way surrogate split; class={cls} has n={n}"
            )

        n_fit = int(round(fit_frac * n))
        n_guard = int(round(guard_frac * n))

        n_fit = max(1, min(n_fit, n - 2))
        n_guard = max(1, min(n_guard, n - n_fit - 1))
        n_score = n - n_fit - n_guard

        if n_score < 1:
            n_guard = max(1, n_guard - 1)
            n_score = n - n_fit - n_guard
        if n_score < 1:
            n_fit = max(1, n_fit - 1)
            n_score = n - n_fit - n_guard
        if n_score < 1:
            raise RuntimeError(f"Could not form three-way split for class={cls}, n={n}")

        fit_idx = idx[:n_fit]
        guard_idx = idx[n_fit:n_fit + n_guard]
        score_idx = idx[n_fit + n_guard:]

        fit_mask[fit_idx] = True
        guard_mask[guard_idx] = True
        score_mask[score_idx] = True

    return fit_mask, guard_mask, score_mask


def _closed_per_class_recall(split: SplitOutputs) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for cls in np.unique(split.y_true):
        cls = int(cls)
        mask = (split.y_true == cls)
        if mask.sum() == 0:
            continue
        out[cls] = float(np.mean(split.closed_pred[mask] == cls))
    return out


class VarMaxOSR(BaseOSRMethod):
    method_name = "varmax"

    def __init__(
        self,
        temperature: float = 1.0,
        top2_threshold: Optional[float] = None,
        top2_percentile: float = 5.0,
        var_percentiles: Tuple[float, float] = (5.0, 95.0),
        energy_percentiles: Tuple[float, float] = (5.0, 95.0),
        use_energy: bool = True,
        fit_on: str = "predicted_class",
        min_samples_per_class: int = 5,
    ):
        self.temperature = float(temperature)
        self.top2_threshold = top2_threshold
        self.top2_percentile = float(top2_percentile)
        self.var_percentiles = tuple(var_percentiles)
        self.energy_percentiles = tuple(energy_percentiles)
        self.use_energy = bool(use_energy)
        self.fit_on = fit_on
        self.min_samples_per_class = int(min_samples_per_class)

        self.thresholds_: Optional[Dict[str, Any]] = None
        self.num_classes_: Optional[int] = None
        self.class_names_: Optional[list[str]] = None
        self.fitted_ = False

        self.sweep_history_: list[dict] = []
        self.best_sweep_result_: Optional[Dict[str, Any]] = None
        self.top_feasible_results_: list[dict] = []
        self.top_fallback_results_: list[dict] = []
        self.calibration_specs_: list[dict] = []

        self.baseline_known_closed_macro_f1_: Optional[float] = None
        self.baseline_known_closed_acc_: Optional[float] = None
        self.no_feasible_solution_: bool = False
        self.calibration_mode_: Optional[str] = None

    def _compute_scores(self, logits: np.ndarray) -> Dict[str, np.ndarray]:
        top2 = compute_top2_gap(logits, temperature=self.temperature)
        var = compute_logit_variance(logits)
        energy = compute_energy(logits, temperature=self.temperature)
        return {"top2": top2, "var": var, "energy": energy}

    def _select_fit_labels(self, split: SplitOutputs) -> np.ndarray:
        if self.fit_on == "predicted_class":
            return split.closed_pred.astype(int)
        if self.fit_on == "true_class":
            return split.y_true.astype(int)
        raise ValueError(f"Unsupported fit_on: {self.fit_on}")

    def _fit_class_bands(
        self,
        values: np.ndarray,
        labels_for_bands: np.ndarray,
        fallback_labels: np.ndarray,
        percentiles: Tuple[float, float],
        num_classes: int,
    ) -> Dict[int, Tuple[float, float]]:
        out: Dict[int, Tuple[float, float]] = {}

        for cls in range(num_classes):
            mask = (labels_for_bands == cls)
            vals = values[mask]

            if vals.size < self.min_samples_per_class:
                vals = values[fallback_labels == cls]
            if vals.size < self.min_samples_per_class:
                vals = values

            out[cls] = _safe_percentile(vals, percentiles)

        return out

    def _make_thresholds_from_percentiles(
        self,
        known_split: SplitOutputs,
        top2_threshold: float,
        var_percentiles: Tuple[float, float],
        energy_percentiles: Tuple[float, float],
    ) -> Dict[str, Any]:
        logits = known_split.logits
        scores = self._compute_scores(logits)

        true_labels = known_split.y_true.astype(int)
        labels_for_bands = self._select_fit_labels(known_split)

        var_thresholds = self._fit_class_bands(
            values=scores["var"],
            labels_for_bands=labels_for_bands,
            fallback_labels=true_labels,
            percentiles=var_percentiles,
            num_classes=self.num_classes_,
        )

        if self.use_energy:
            energy_thresholds = self._fit_class_bands(
                values=scores["energy"],
                labels_for_bands=labels_for_bands,
                fallback_labels=true_labels,
                percentiles=energy_percentiles,
                num_classes=self.num_classes_,
            )
        else:
            energy_thresholds = {}

        return {
            "top2": float(top2_threshold),
            "var": var_thresholds,
            "energy": energy_thresholds,
        }

    def _unknown_score_from_scores(
        self,
        scores: Dict[str, np.ndarray],
        pred_labels: np.ndarray,
        thresholds: Dict[str, Any],
    ) -> np.ndarray:
        top2 = scores["top2"]
        var = scores["var"]
        energy = scores["energy"]

        t2_thr = float(thresholds["top2"])
        top2_deficit = np.clip(t2_thr - top2, 0.0, None) / max(t2_thr, 1e-8)

        var_bounds = np.array([thresholds["var"][int(c)] for c in pred_labels], dtype=float)
        var_outside = _band_distance(var, var_bounds)

        if self.use_energy and thresholds.get("energy"):
            energy_bounds = np.array([thresholds["energy"][int(c)] for c in pred_labels], dtype=float)
            energy_outside = _band_distance(energy, energy_bounds)
        else:
            energy_outside = np.zeros_like(var_outside)

        ambiguous = top2 < t2_thr
        unknown_score = top2_deficit.copy()
        unknown_score[ambiguous] += var_outside[ambiguous]
        if self.use_energy:
            unknown_score[ambiguous] += energy_outside[ambiguous]

        return unknown_score

    def _predict_with_thresholds(
        self,
        split: SplitOutputs,
        thresholds: Dict[str, Any],
        unknown_label: int,
    ) -> Dict[str, np.ndarray]:
        logits = split.logits
        pred_labels = split.closed_pred.astype(int)
        scores = self._compute_scores(logits)

        is_known = compute_varmax_flags(
            top2=scores["top2"],
            var=scores["var"],
            energy=scores["energy"],
            thresholds=thresholds,
            pred_labels=pred_labels,
        )

        final_pred = pred_labels.copy()
        final_pred[~is_known] = int(unknown_label)

        unknown_score = self._unknown_score_from_scores(scores, pred_labels, thresholds)

        return {
            "unknown_score": unknown_score,
            "is_unknown": (~is_known).astype(bool),
            "closed_pred": pred_labels,
            "final_pred": final_pred,
            "top2": scores["top2"],
            "var": scores["var"],
            "energy": scores["energy"],
        }

    def _evaluate_thresholds(
        self,
        known_split: SplitOutputs,
        open_split: SplitOutputs,
        thresholds: Dict[str, Any],
    ) -> Dict[str, Any]:
        unknown_label = self.num_classes_

        known_pred = self._predict_with_thresholds(known_split, thresholds, unknown_label)
        open_pred = self._predict_with_thresholds(open_split, thresholds, unknown_label)

        return evaluate_osr_predictions(
            known_split=known_split,
            open_split=open_split,
            known_pred=known_pred,
            open_pred=open_pred,
            known_class_names=self.class_names_,
            unknown_label_name="unknown",
        )

    def _build_surrogate_specs(
        self,
        payload: BackbonePayload,
        calibration_known: SplitOutputs,
        calibration_mode: str,
        pair_map: Optional[Dict[str, str]] = None,
        surrogate_fit_frac: float = 0.50,
        surrogate_guard_frac: float = 0.25,
        surrogate_seed: int = 0,
    ) -> List[Dict[str, Any]]:
        class_names = list(payload.meta["class_names"])
        unknown_pas = list(payload.meta.get("unknown_pas", []))
        true_unknown_name = unknown_pas[0] if len(unknown_pas) == 1 else None

        pair_map = pair_map or DEFAULT_PAIR_MAP
        aligned_name = pair_map.get(true_unknown_name, None)
        aligned_idx = class_names.index(aligned_name) if aligned_name in class_names else None

        fit_mask, guard_mask, score_mask = _stratified_three_way_masks(
            calibration_known.y_true,
            fit_frac=surrogate_fit_frac,
            guard_frac=surrogate_guard_frac,
            seed=surrogate_seed,
        )

        fit_known = _subset_split(
            calibration_known, fit_mask, split_name=f"{calibration_known.split_name}_fit_known"
        )
        guard_known = _subset_split(
            calibration_known, guard_mask, split_name=f"{calibration_known.split_name}_guard_known"
        )
        score_pool = _subset_split(
            calibration_known, score_mask, split_name=f"{calibration_known.split_name}_score_pool"
        )

        guard_known_baseline = _closed_per_class_recall(guard_known)

        specs = []

        def make_one(holdout_idx: int, regime: str):
            holdout_name = class_names[holdout_idx]
            open_mask = (score_pool.y_true == holdout_idx)

            if open_mask.sum() == 0:
                return

            spec = {
                "calibration_mode": calibration_mode,
                "regime": regime,
                "spec_name": f"{regime}:{holdout_name}",
                "true_unknown_name": true_unknown_name,
                "heldout_class_idx": int(holdout_idx),
                "heldout_class_name": holdout_name,
                "is_structure_aligned": (
                    aligned_idx is not None and int(holdout_idx) == int(aligned_idx)
                ),
                "fit_known_split": fit_known,
                "guard_known_split": guard_known,
                "guard_known_baseline_per_class_closed_recall": copy.deepcopy(guard_known_baseline),
                "open_split": _subset_split(
                    score_pool,
                    open_mask,
                    split_name=f"{score_pool.split_name}_{regime}_open",
                ),
            }
            specs.append(spec)

        if calibration_mode == "surrogate_aligned":
            if aligned_idx is None:
                raise ValueError(
                    f"No aligned surrogate found for true unknown '{true_unknown_name}' within class_names={class_names}"
                )
            make_one(aligned_idx, "aligned")
        elif calibration_mode == "surrogate_mismatched":
            for idx in range(len(class_names)):
                if aligned_idx is not None and idx == aligned_idx:
                    continue
                make_one(idx, "mismatched")
        elif calibration_mode == "surrogate_all":
            for idx in range(len(class_names)):
                regime = "aligned" if (aligned_idx is not None and idx == aligned_idx) else "mismatched"
                make_one(idx, regime)
        else:
            raise ValueError(f"Unsupported calibration_mode: {calibration_mode}")

        if len(specs) == 0:
            raise RuntimeError(f"No surrogate calibration specs could be built for mode={calibration_mode}")

        return specs

    def _build_calibration_specs(
        self,
        payload: BackbonePayload,
        calibration_known: Optional[SplitOutputs],
        calibration_open: Optional[SplitOutputs],
        calibration_mode: str,
        pair_map: Optional[Dict[str, str]] = None,
        surrogate_fit_frac: float = 0.50,
        surrogate_guard_frac: float = 0.25,
        surrogate_seed: int = 0,
    ) -> List[Dict[str, Any]]:
        calibration_known = calibration_known or payload.val_known

        if calibration_known is None:
            raise ValueError("Calibration requires a known split")

        if calibration_mode == "oracle":
            calibration_open = calibration_open or payload.test_open
            if calibration_open is None:
                raise ValueError("Oracle calibration requires an open split")
            return [{
                "calibration_mode": "oracle",
                "regime": "oracle",
                "spec_name": "oracle",
                "true_unknown_name": (payload.meta.get("unknown_pas") or [None])[0],
                "heldout_class_idx": None,
                "heldout_class_name": None,
                "is_structure_aligned": None,
                "fit_known_split": calibration_known,
                "guard_known_split": calibration_known,
                "guard_known_baseline_per_class_closed_recall": _closed_per_class_recall(calibration_known),
                "open_split": calibration_open,
            }]

        return self._build_surrogate_specs(
            payload=payload,
            calibration_known=calibration_known,
            calibration_mode=calibration_mode,
            pair_map=pair_map,
            surrogate_fit_frac=surrogate_fit_frac,
            surrogate_guard_frac=surrogate_guard_frac,
            surrogate_seed=surrogate_seed,
        )

    def fit(self, payload: BackbonePayload, calibration: Dict[str, Any] | None = None) -> None:
        if payload.val_known is None:
            raise ValueError("VarMaxOSR.fit() requires payload.val_known")

        self.num_classes_ = int(payload.meta["num_classes"])
        self.class_names_ = list(payload.meta["class_names"])

        if calibration is not None and calibration.get("mode") == "sweep":
            self.fit_with_sweep(
                payload=payload,
                calibration_known=calibration.get("calibration_known", payload.val_known),
                calibration_open=calibration.get("calibration_open", payload.test_open),
                calibration_mode=calibration.get("calibration_mode", "oracle"),
                pair_map=calibration.get("pair_map", DEFAULT_PAIR_MAP),
                surrogate_fit_frac=float(calibration.get("surrogate_fit_frac", 0.50)),
                surrogate_guard_frac=float(calibration.get("surrogate_guard_frac", 0.25)),
                surrogate_seed=int(calibration.get("surrogate_seed", 0)),
                top2_grid=calibration.get("top2_grid"),
                var_lo_grid=calibration.get("var_lo_grid"),
                var_hi_grid=calibration.get("var_hi_grid"),
                energy_lo_grid=calibration.get("energy_lo_grid"),
                energy_hi_grid=calibration.get("energy_hi_grid"),
                known_floor_ratio=float(calibration.get("known_floor_ratio", 0.95)),
                unknown_recall_floor=float(calibration.get("unknown_recall_floor", 0.60)),
                per_class_floor_ratio=float(calibration.get("per_class_floor_ratio", 0.95)),
                top_k=int(calibration.get("top_k", 10)),
            )
            return

        if calibration is not None and "thresholds" in calibration:
            self.thresholds_ = copy.deepcopy(calibration["thresholds"])
            self.fitted_ = True
            return

        split = payload.val_known
        logits = split.logits
        true_labels = split.y_true.astype(int)

        scores = self._compute_scores(logits)
        labels_for_bands = self._select_fit_labels(split)

        if self.top2_threshold is None:
            top2_thr = float(np.percentile(scores["top2"], self.top2_percentile))
        else:
            top2_thr = float(self.top2_threshold)

        var_thresholds = self._fit_class_bands(
            values=scores["var"],
            labels_for_bands=labels_for_bands,
            fallback_labels=true_labels,
            percentiles=self.var_percentiles,
            num_classes=self.num_classes_,
        )

        if self.use_energy:
            energy_thresholds = self._fit_class_bands(
                values=scores["energy"],
                labels_for_bands=labels_for_bands,
                fallback_labels=true_labels,
                percentiles=self.energy_percentiles,
                num_classes=self.num_classes_,
            )
        else:
            energy_thresholds = {}

        self.thresholds_ = {
            "top2": top2_thr,
            "var": var_thresholds,
            "energy": energy_thresholds,
        }
        self.fitted_ = True

    def fit_with_sweep(
        self,
        payload: BackbonePayload,
        calibration_known: Optional[SplitOutputs] = None,
        calibration_open: Optional[SplitOutputs] = None,
        calibration_mode: str = "oracle",
        pair_map: Optional[Dict[str, str]] = None,
        surrogate_fit_frac: float = 0.50,
        surrogate_guard_frac: float = 0.25,
        surrogate_seed: int = 0,
        top2_grid: Optional[Sequence[float]] = None,
        var_lo_grid: Optional[Sequence[float]] = None,
        var_hi_grid: Optional[Sequence[float]] = None,
        energy_lo_grid: Optional[Sequence[float]] = None,
        energy_hi_grid: Optional[Sequence[float]] = None,
        known_floor_ratio: float = 0.95,
        unknown_recall_floor: float = 0.60,
        per_class_floor_ratio: float = 0.95,
        top_k: int = 10,
    ) -> None:
        self.num_classes_ = int(payload.meta["num_classes"])
        self.class_names_ = list(payload.meta["class_names"])
        self.calibration_mode_ = calibration_mode

        if top2_grid is None:
            top2_grid = [0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99]
        if var_lo_grid is None:
            var_lo_grid = [1.0, 2.5, 5.0, 7.5, 10.0, 15.0]
        if var_hi_grid is None:
            var_hi_grid = [85.0, 90.0, 92.5, 95.0, 97.5, 99.0]
        if energy_lo_grid is None:
            energy_lo_grid = [1.0, 2.5, 5.0, 7.5, 10.0, 15.0]
        if energy_hi_grid is None:
            energy_hi_grid = [85.0, 90.0, 92.5, 95.0, 97.5, 99.0]

        calibration_specs = self._build_calibration_specs(
            payload=payload,
            calibration_known=calibration_known,
            calibration_open=calibration_open,
            calibration_mode=calibration_mode,
            pair_map=pair_map,
            surrogate_fit_frac=surrogate_fit_frac,
            surrogate_guard_frac=surrogate_guard_frac,
            surrogate_seed=surrogate_seed,
        )
        self.calibration_specs_ = copy.deepcopy(calibration_specs)

        n_top2 = len(list(top2_grid))
        n_var = sum(1 for lo in var_lo_grid for hi in var_hi_grid if float(lo) < float(hi))
        if self.use_energy:
            n_energy = sum(1 for lo in energy_lo_grid for hi in energy_hi_grid if float(lo) < float(hi))
        else:
            n_energy = 1
        total_candidates = max(1, len(calibration_specs) * n_top2 * n_var * n_energy)
        candidate_i = 0
        last_progress_write = 0.0

        _write_osr_progress_from_varmax(
            phase="threshold_sweep",
            pct=20.0,
            sweep_candidate=0,
            sweep_candidates=total_candidates,
            calibration_specs=len(calibration_specs),
            calibration_mode=calibration_mode,
        )

        base_known = calibration_known or payload.val_known
        if base_known is None:
            raise ValueError("Need a known split to compute baseline metrics")

        baseline_known_closed_acc = float(np.mean(base_known.closed_pred == base_known.y_true))
        baseline_known_closed_macro_f1 = float(
            f1_score(
                base_known.y_true,
                base_known.closed_pred,
                average="macro",
                zero_division=0,
            )
        )

        self.baseline_known_closed_acc_ = baseline_known_closed_acc
        self.baseline_known_closed_macro_f1_ = baseline_known_closed_macro_f1

        known_floor_acc = float(known_floor_ratio) * baseline_known_closed_acc
        known_floor_macro_f1 = float(known_floor_ratio) * baseline_known_closed_macro_f1

        sweep_rows = []

        if self.use_energy:
            energy_pairs = [
                (float(lo), float(hi))
                for lo in energy_lo_grid
                for hi in energy_hi_grid
                if float(lo) < float(hi)
            ]
        else:
            energy_pairs = [(None, None)]

        for spec in calibration_specs:
            fit_known = spec["fit_known_split"]
            guard_known = spec["guard_known_split"]
            spec_open = spec["open_split"]

            per_class_baseline = spec["guard_known_baseline_per_class_closed_recall"]
            per_class_floor = {
                int(cls): float(per_class_floor_ratio) * float(base_rec)
                for cls, base_rec in per_class_baseline.items()
            }

            for top2_thr in top2_grid:
                for var_lo in var_lo_grid:
                    for var_hi in var_hi_grid:
                        if float(var_lo) >= float(var_hi):
                            continue

                        for energy_lo, energy_hi in energy_pairs:
                            candidate_i += 1
                            now = time.time()
                            if candidate_i == 1 or candidate_i == total_candidates or (now - last_progress_write) >= 2.0:
                                last_progress_write = now
                                pct = 20.0 + 65.0 * (float(candidate_i) / float(total_candidates))
                                _write_osr_progress_from_varmax(
                                    phase="threshold_sweep",
                                    pct=pct,
                                    sweep_candidate=candidate_i,
                                    sweep_candidates=total_candidates,
                                    calibration_mode=calibration_mode,
                                    spec_name=spec.get("spec_name"),
                                    top2_threshold=float(top2_thr),
                                    var_percentiles=[float(var_lo), float(var_hi)],
                                    energy_percentiles=(
                                        [float(energy_lo), float(energy_hi)]
                                        if self.use_energy else None
                                    ),
                                )

                            thresholds = self._make_thresholds_from_percentiles(
                                known_split=fit_known,
                                top2_threshold=float(top2_thr),
                                var_percentiles=(float(var_lo), float(var_hi)),
                                energy_percentiles=(
                                    (float(energy_lo), float(energy_hi))
                                    if self.use_energy else self.energy_percentiles
                                ),
                            )

                            metrics = self._evaluate_thresholds(
                                known_split=guard_known,
                                open_split=spec_open,
                                thresholds=thresholds,
                            )

                            per_class_recall = metrics["known_osr_per_class_recall"]
                            per_class_feasible = all(
                                per_class_recall.get(int(cls), 0.0) >= floor
                                for cls, floor in per_class_floor.items()
                            )

                            feasible = (
                                metrics["known_osr_macro_f1"] >= known_floor_macro_f1 and
                                metrics["known_osr_acc"] >= known_floor_acc and
                                metrics["unknown_recall"] >= float(unknown_recall_floor) and
                                per_class_feasible
                            )

                            row = {
                                "calibration_mode": calibration_mode,
                                "regime": spec["regime"],
                                "spec_name": spec["spec_name"],
                                "true_unknown_name": spec["true_unknown_name"],
                                "heldout_class_idx": spec["heldout_class_idx"],
                                "heldout_class_name": spec["heldout_class_name"],
                                "is_structure_aligned": spec["is_structure_aligned"],
                                "top2_threshold": float(top2_thr),
                                "var_percentiles": (float(var_lo), float(var_hi)),
                                "energy_percentiles": (
                                    (float(energy_lo), float(energy_hi))
                                    if self.use_energy else None
                                ),
                                "feasible": bool(feasible),
                                "known_floor_ratio": float(known_floor_ratio),
                                "per_class_floor_ratio": float(per_class_floor_ratio),
                                "known_floor_acc": known_floor_acc,
                                "known_floor_macro_f1": known_floor_macro_f1,
                                "per_class_floor_recall": copy.deepcopy(per_class_floor),
                                "baseline_known_closed_acc": baseline_known_closed_acc,
                                "baseline_known_closed_macro_f1": baseline_known_closed_macro_f1,
                                "metrics": metrics,
                                "thresholds": thresholds,
                            }
                            sweep_rows.append(row)

        _write_osr_progress_from_varmax(
            phase="selecting_threshold",
            pct=87.0,
            sweep_candidate=candidate_i,
            sweep_candidates=total_candidates,
            calibration_mode=calibration_mode,
        )

        self.sweep_history_ = sweep_rows

        feasible_rows = [r for r in sweep_rows if r["feasible"]]
        infeasible_rows = [r for r in sweep_rows if not r["feasible"]]

        feasible_rows.sort(
            key=lambda r: (
                float(r["metrics"]["osr_macro_f1"]),
                -abs(float(r["metrics"]["bias_delta"])),
                float(r["metrics"]["unknown_f1"]),
            ),
            reverse=True,
        )

        infeasible_rows.sort(
            key=lambda r: (
                float(r["metrics"]["unknown_recall"]),
                float(r["metrics"]["known_osr_macro_f1"]),
                float(r["metrics"]["osr_macro_f1"]),
            ),
            reverse=True,
        )

        self.top_feasible_results_ = copy.deepcopy(feasible_rows[:top_k])
        self.top_fallback_results_ = copy.deepcopy(infeasible_rows[:top_k])

        if len(feasible_rows) > 0:
            chosen = feasible_rows[0]
            self.no_feasible_solution_ = False
        elif len(infeasible_rows) > 0:
            chosen = infeasible_rows[0]
            self.no_feasible_solution_ = True
        else:
            raise RuntimeError("Threshold sweep produced no candidates")

        self.thresholds_ = copy.deepcopy(chosen["thresholds"])
        self.best_sweep_result_ = copy.deepcopy(chosen)
        self.fitted_ = True

    def score(self, split: SplitOutputs) -> np.ndarray:
        if not self.fitted_ or self.thresholds_ is None:
            raise RuntimeError("VarMaxOSR must be fitted before score()")

        logits = split.logits
        pred_labels = split.closed_pred.astype(int)
        scores = self._compute_scores(logits)
        return self._unknown_score_from_scores(scores, pred_labels, self.thresholds_)

    def predict(self, split: SplitOutputs, unknown_label: int) -> Dict[str, np.ndarray]:
        if not self.fitted_ or self.thresholds_ is None:
            raise RuntimeError("VarMaxOSR must be fitted before predict()")
        return self._predict_with_thresholds(split, self.thresholds_, unknown_label)

    def get_params(self) -> Dict[str, Any]:
        return {
            "method_name": self.method_name,
            "temperature": self.temperature,
            "top2_threshold": self.top2_threshold,
            "top2_percentile": self.top2_percentile,
            "var_percentiles": self.var_percentiles,
            "energy_percentiles": self.energy_percentiles,
            "use_energy": self.use_energy,
            "fit_on": self.fit_on,
            "min_samples_per_class": self.min_samples_per_class,
            "calibration_mode": self.calibration_mode_,
            "baseline_known_closed_acc": self.baseline_known_closed_acc_,
            "baseline_known_closed_macro_f1": self.baseline_known_closed_macro_f1_,
            "no_feasible_solution": self.no_feasible_solution_,
            "calibration_specs": copy.deepcopy(self.calibration_specs_),
            "best_sweep_result": copy.deepcopy(self.best_sweep_result_),
            "top_feasible_results": copy.deepcopy(self.top_feasible_results_),
            "top_fallback_results": copy.deepcopy(self.top_fallback_results_),
            "fitted_thresholds": copy.deepcopy(self.thresholds_),
        }