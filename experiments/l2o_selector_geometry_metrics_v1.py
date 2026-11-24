from __future__ import annotations

import numpy as np


def entropy_from_probs(p):
    p = np.clip(np.asarray(p), 1e-12, 1.0)
    return -np.sum(p * np.log(p), axis=1)


def p1_gap_entropy(split):
    probs = np.asarray(split.probs)
    p1 = probs.max(axis=1)
    sortp = np.sort(probs, axis=1)
    gap = sortp[:, -1] - sortp[:, -2]
    ent = entropy_from_probs(probs)
    return p1, gap, ent


def summarize_confidence(known, surrogate):
    """Frozen historical Rule B definition recovered from the MILCOM analyzer."""
    kp1, kgap, kent = p1_gap_entropy(known)
    sp1, sgap, sent = p1_gap_entropy(surrogate)

    p1_drop = float(np.mean(kp1) - np.mean(sp1))
    gap_drop = float(np.mean(kgap) - np.mean(sgap))
    ent_rise = float(np.mean(sent) - np.mean(kent))

    eps = 1e-9
    z_p1_drop = p1_drop / (float(np.std(kp1)) + eps)
    z_gap_drop = gap_drop / (float(np.std(kgap)) + eps)
    z_ent_rise = ent_rise / (float(np.std(kent)) + eps)

    confidence_geometry_score = float(z_p1_drop + z_gap_drop + z_ent_rise)
    overconfident_surrogate = bool(
        (np.mean(sp1) > np.mean(kp1)) and (np.mean(sent) < np.mean(kent))
    )

    return {
        "known_p1_mean": float(np.mean(kp1)),
        "sur_p1_mean": float(np.mean(sp1)),
        "p1_drop_known_minus_sur": p1_drop,
        "known_gap_mean": float(np.mean(kgap)),
        "sur_gap_mean": float(np.mean(sgap)),
        "gap_drop_known_minus_sur": gap_drop,
        "known_entropy_mean": float(np.mean(kent)),
        "sur_entropy_mean": float(np.mean(sent)),
        "entropy_rise_sur_minus_known": ent_rise,
        "confidence_geometry_score": confidence_geometry_score,
        "overconfident_surrogate": overconfident_surrogate,
    }


def l2_normalize(x):
    x = np.asarray(x, dtype=np.float32)
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return x / np.maximum(n, 1e-9)


def summarize_feature_geometry(known, surrogate):
    """Frozen historical Rule C feature-geometry definition."""
    Xk = l2_normalize(known.features)
    Xs = l2_normalize(surrogate.features)
    yk = np.asarray(known.y_true)

    classes = sorted([int(c) for c in np.unique(yk) if int(c) >= 0])
    centroids = [Xk[yk == c].mean(axis=0) for c in classes]
    C = l2_normalize(np.stack(centroids, axis=0))

    dk = 1.0 - (Xk @ C.T)
    ds = 1.0 - (Xs @ C.T)

    k_near = np.min(dk, axis=1)
    s_near = np.min(ds, axis=1)
    s_sorted = np.sort(ds, axis=1)
    s_margin = (
        s_sorted[:, 1] - s_sorted[:, 0]
        if s_sorted.shape[1] > 1
        else np.zeros(len(Xs))
    )

    known_95 = float(np.percentile(k_near, 95))
    surrogate_median = float(np.median(s_near))
    ratio = surrogate_median / max(known_95, 1e-9)

    return {
        "known_nearest_centroid_dist_median": float(np.median(k_near)),
        "known_nearest_centroid_dist_p95": known_95,
        "sur_nearest_centroid_dist_median": surrogate_median,
        "sur_nearest_centroid_dist_mean": float(np.mean(s_near)),
        "sur_centroid_margin_median": float(np.median(s_margin)),
        "surrogate_known_distance_ratio": float(ratio),
        "feature_distance_score": float(ratio),
        "feature_boundary_score": float(-abs(np.log(max(ratio, 1e-9)))),
    }
