from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from experiments.l2o_eval_request_contract import resolve_directional_eval_request
from experiments.l2o_eval_result_record import build_result_record
from experiments.l2o_selector_geometry_metrics_v1 import (
    summarize_confidence,
    summarize_feature_geometry,
)


def _split(probs, features, y):
    return SimpleNamespace(
        probs=np.asarray(probs, dtype=float),
        features=np.asarray(features, dtype=float),
        y_true=np.asarray(y, dtype=int),
    )


def test_rule_b_matches_frozen_historical_definition():
    known = _split(
        [[0.8,0.1,0.1],[0.6,0.3,0.1],[0.7,0.2,0.1]],
        [[1,0],[0,1],[1,1]],
        [0,1,0],
    )
    sur = _split(
        [[0.5,0.3,0.2],[0.45,0.35,0.2],[0.4,0.35,0.25]],
        [[1,0],[0,1],[1,-1]],
        [-1,-1,-1],
    )
    got=summarize_confidence(known,sur)

    def stats(p):
        p=np.asarray(p,float)
        p1=p.max(axis=1)
        s=np.sort(p,axis=1)
        gap=s[:,-1]-s[:,-2]
        ent=-np.sum(np.clip(p,1e-12,1.0)*np.log(np.clip(p,1e-12,1.0)),axis=1)
        return p1,gap,ent
    kp1,kg,ke=stats(known.probs)
    sp1,sg,se=stats(sur.probs)
    expected=(
        (kp1.mean()-sp1.mean())/(kp1.std()+1e-9)
        +(kg.mean()-sg.mean())/(kg.std()+1e-9)
        +(se.mean()-ke.mean())/(ke.std()+1e-9)
    )
    assert np.isclose(got["confidence_geometry_score"],expected)


def test_rule_c_matches_frozen_historical_centroid_margin():
    known=_split(
        [[.8,.2],[.2,.8],[.7,.3],[.3,.7]],
        [[1,0],[0,1],[1,.1],[.1,1]],
        [0,1,0,1],
    )
    sur=_split(
        [[.5,.5],[.55,.45]],
        [[1,1],[1,-1]],
        [-1,-1],
    )
    got=summarize_feature_geometry(known,sur)
    def norm(x):
        x=np.asarray(x,np.float32)
        return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-9)
    Xk=norm(known.features); Xs=norm(sur.features)
    C=norm(np.stack([Xk[known.y_true==c].mean(axis=0) for c in [0,1]]))
    ds=1-(Xs@C.T)
    margin=np.sort(ds,axis=1)[:,1]-np.sort(ds,axis=1)[:,0]
    assert np.isclose(got["sur_centroid_margin_median"],np.median(margin))


def _write_contract(tmp_path: Path, analysis_mode="selector_geometry_pair_v1"):
    matrix={
        "schema":"padataset.l2o-canonical-backbone-matrix.v1",
        "backbones":[{
            "canonical_key":"PA1-PA2","canonical_pair":["PA1","PA2"],
            "known_pas":["PA3","PA4","PA8"],"status":"COMPLETE",
            "artifact_id":123,"artifact_digest":"sha256:abc",
            "workflow_run_id":1,"workflow_job_id":2,"candidate_sha":"a"*40,
            "best_model_sha256":"b"*64,"config_sha256":"c"*64,
            "directed_cells":[
                {"evaluation_target":"PA1","evaluation_surrogate":"PA2"},
                {"evaluation_target":"PA2","evaluation_surrogate":"PA1"},
            ],
        }]
    }
    policy={
        "schema":"padataset.l2o-directional-eval-policy.v1",
        "policy_id":"l2o_dqnguard_track_a_frozen_v1","checkpoint":"best_model",
        "band_accept_mode":"var_energy","decision_mode":"score_threshold",
        "max_known_reject_cal":0.05,"known_cap":625,"open_cap":625,
        "mix_true_open":False,"dqn_state_mode":"softmax3","evaluator_device":"cuda",
        "batch_size":128,"num_workers":0,"target_labels_used_for_tuning":False,
    }
    req={
        "schema":"padataset.l2o-directional-eval-request.v1",
        "policy_id":"l2o_dqnguard_track_a_frozen_v1",
        "canonical_matrix":"manifests/l2o_canonical_backbone_matrix_v1.json",
        "evaluation_policy":"manifests/l2o_directional_eval_policy_v1.json",
        "canonical_key":"PA1-PA2","artifact_id":123,"artifact_digest":"sha256:abc",
        "evaluation_target":"PA1","evaluation_surrogate":"PA2","checkpoint":"best_model",
        "target_labels_used_for_tuning":False,"status":"READY_FOR_BOUNDED_EVALUATOR",
        "analysis_mode":analysis_mode,
    }
    out={}
    for n,v in [("matrix",matrix),("policy",policy),("request",req)]:
        p=tmp_path/f"{n}.json"; p.write_text(json.dumps(v)); out[n]=p
    return out


def test_selector_request_adds_geometry_only_flag(tmp_path):
    p=_write_contract(tmp_path)
    r=resolve_directional_eval_request(
        request_path=p["request"],matrix_path=p["matrix"],policy_path=p["policy"],
        run_dir=tmp_path/"run",out_dir=tmp_path/"out",
    )
    assert r.analysis_mode=="selector_geometry_pair_v1"
    assert "--selector-geometry-pair-only" in r.evaluator_args
    assert "--mix-true-open" not in r.evaluator_args


def test_selector_result_requires_and_records_both_directions(tmp_path):
    p=_write_contract(tmp_path)
    fields={
        "analysis_mode":"selector_geometry_pair_v1",
        "target_labels_used_for_tuning":False,
        "known_p1_mean":.8,"sur_p1_mean":.5,"p1_drop_known_minus_sur":.3,
        "known_gap_mean":.6,"sur_gap_mean":.2,"gap_drop_known_minus_sur":.4,
        "known_entropy_mean":.4,"sur_entropy_mean":.9,"entropy_rise_sur_minus_known":.5,
        "confidence_geometry_score":2.1,"sur_centroid_margin_median":.15,
        "surrogate_known_distance_ratio":1.2,"feature_distance_score":1.2,
        "feature_boundary_score":-.18,
    }
    rows=[]
    for target,surrogate in [("PA1","PA2"),("PA2","PA1")]:
        rows.append({"target":target,"surrogate":surrogate,**fields})
    csv=tmp_path/"summary.csv"; pd.DataFrame(rows).to_csv(csv,index=False)
    out=tmp_path/"result.json"
    rec=build_result_record(
        request_path=p["request"],matrix_path=p["matrix"],policy_path=p["policy"],
        summary_csv=csv,output_path=out,
    )
    assert rec["schema"]=="padataset.l2o-selector-geometry-result.v1"
    assert rec["provenance"]["target_test_consumed"] is False
    assert len(rec["rows"])==2
