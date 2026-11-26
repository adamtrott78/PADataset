#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0,str(REPO_ROOT))

os.environ.setdefault("OMP_NUM_THREADS","4")
os.environ.setdefault("MKL_NUM_THREADS","4")
os.environ.setdefault("OPENBLAS_NUM_THREADS","4")
os.environ.setdefault("NUMEXPR_NUM_THREADS","4")
os.environ.setdefault("CUDA_VISIBLE_DEVICES","")

import numpy as np
import torch
torch.set_num_threads(min(4,max(1,os.cpu_count() or 1)))
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

from osr_core import BackbonePayload, evaluate_osr_predictions
from experiments.mth602_robustness_cached_all_osr import (
    apply_threshold, load_policy, load_split, payload_meta_from_manifests
)
from experiments.pa_eval_dqn_guard_surrogate_open import cap_split, make_method
from experiments.pa_eval_l2o_controls_v1 import (
    build_varmax_calibration, make_dqn_control, make_varmax_control
)

METHODS=("DQNGuard","DQN-IDS-style","VarMax")
METRICS=("known_reject_rate","unknown_precision","unknown_recall","unknown_f1","osr_acc","osr_macro_f1","unknown_auroc")


def readj(p:Path):
    return json.loads(p.read_text())


def metrics(method,payload):
    u=int(payload.meta["num_classes"])
    kp=method.predict(payload.test_known,unknown_label=u)
    op=method.predict(payload.test_open,unknown_label=u)
    m=evaluate_osr_predictions(
        known_split=payload.test_known,open_split=payload.test_open,
        known_pred=kp,open_pred=op,known_class_names=payload.meta["class_names"],
        unknown_label_name="unknown",
    )
    return {k:float(m[k]) for k in METRICS},kp,op


def dqn_guard_metrics(method,thr,payload):
    u=int(payload.meta["num_classes"])
    kb=method.predict(payload.test_known,unknown_label=u)
    ob=method.predict(payload.test_open,unknown_label=u)
    kp=apply_threshold(kb,thr,u)
    op=apply_threshold(ob,thr,u)
    m=evaluate_osr_predictions(
        known_split=payload.test_known,open_split=payload.test_open,
        known_pred=kp,open_pred=op,known_class_names=payload.meta["class_names"],
        unknown_label_name="unknown",
    )
    return {k:float(m[k]) for k in METRICS},kp,op


def final_pred(x):
    return np.asarray(x["final_pred"],dtype=np.int64)


def compare(name,ref_tuple,frozen_tuple,tol):
    rm,rk,ro=ref_tuple
    fm,fk,fo=frozen_tuple
    deltas={k:abs(rm[k]-fm[k]) for k in METRICS}
    kp_mismatch=int(np.count_nonzero(final_pred(rk)!=final_pred(fk)))
    op_mismatch=int(np.count_nonzero(final_pred(ro)!=final_pred(fo)))
    mx=max(deltas.values()) if deltas else 0.0
    return {
        "method":name,
        "metric_abs_delta":deltas,
        "max_metric_abs_delta":mx,
        "known_final_pred_mismatch":kp_mismatch,
        "open_final_pred_mismatch":op_mismatch,
        "pass":bool(mx<=tol and kp_mismatch==0 and op_mismatch==0),
    }


def fit_reference(cache_dir:Path,target:str,surrogate:str,policy):
    cal=readj(cache_dir/"manifest.json")
    known_val=load_split(cache_dir/"known_val.npz")
    known_test=load_split(cache_dir/"known_test.npz")
    kb=cache_dir/"known_val_balanced.npz"
    known_bal=load_split(kb) if kb.is_file() else None
    surrogate_val=load_split(cache_dir/f"val_open_{surrogate}.npz")
    meta=payload_meta_from_manifests(cal,target)
    pseed=int(meta["partition_seed"])
    fit_payload=BackbonePayload(meta=meta,val_known=known_val,test_known=known_test,test_open=None)

    dgcfg=policy["methods"]["dqnguard"]
    kc=cap_split(known_val,int(dgcfg["known_cap"]),pseed+101,True,"parity_dqnguard_known")
    oc=cap_split(surrogate_val,int(dgcfg["open_cap"]),pseed+202,False,"parity_dqnguard_surrogate")
    dg=make_method(str(dgcfg["band_accept_mode"]))
    dg.fit(fit_payload,calibration={
        "calibration_mode":f"surrogate_{surrogate}_var_energy_cap{dgcfg['open_cap']}",
        "calibration_known":kc,"calibration_open":oc,
    })
    u=int(meta["num_classes"])
    ckp=dg.predict(kc,unknown_label=u)
    thr=float(np.percentile(ckp["unknown_score"],100.0*(1.0-float(dgcfg["max_known_reject_cal"]))))

    cp=readj(REPO_ROOT/"manifests/l2o_control_eval_policy_v1.json")
    di=make_dqn_control(cp)
    dik=cap_split(known_val,625,pseed+101,True,"parity_dqnids_known")
    dio=cap_split(surrogate_val,625,pseed+202,False,"parity_dqnids_surrogate")
    di.fit(fit_payload,calibration={
        "calibration_mode":"external_surrogate_cap625",
        "calibration_known":dik,"calibration_open":dio,
    })

    vm=make_varmax_control(cp)
    extras={"val_known_balanced":known_bal,"val_open":None,"val_open_balanced":None}
    vm.fit(fit_payload,calibration=build_varmax_calibration(fit_payload,extras,cp))
    return dg,thr,di,vm


def run_cell(cell,pipeline_root:Path,policy,tol):
    rn=cell["run_name"]; pair=list(cell["canonical_pair"])
    run_dir=pipeline_root/"backbones"/rn
    cache_dir=run_dir/"osr_calibration_cache"
    bundle=run_dir/"osr_posttrain_bundle"
    frozen=torch.load(bundle/"frozen/frozen_methods.pt",map_location="cpu",weights_only=False)
    cal=readj(cache_dir/"manifest.json")
    known_test=load_split(cache_dir/"known_test.npz")
    rows=[]
    for target,surrogate in ((pair[0],pair[1]),(pair[1],pair[0])):
        ref_dg,ref_thr,ref_di,ref_vm=fit_reference(cache_dir,target,surrogate,policy)
        fr=frozen["directions"][f"{target}_from_{surrogate}"]
        target_test=load_split(bundle/f"target_cache/test_open_{target}.npz")
        meta=payload_meta_from_manifests(cal,target)
        payload=BackbonePayload(meta=meta,val_known=None,test_known=known_test,test_open=target_test)

        comps=[
            compare("DQNGuard",dqn_guard_metrics(ref_dg,ref_thr,payload),dqn_guard_metrics(fr["dqnguard"],fr["dqnguard_threshold"],payload),tol),
            compare("DQN-IDS-style",metrics(ref_di,payload),metrics(fr["dqnids"],payload),tol),
            compare("VarMax",metrics(ref_vm,payload),metrics(fr["varmax"],payload),tol),
        ]
        for c in comps:
            c.update({"run_name":rn,"target":target,"surrogate":surrogate,"direction":f"{target}<-{surrogate}"})
            rows.append(c)
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",default=str(REPO_ROOT/"manifests/mth602_robustness_parity_smoke_v1.json"))
    ap.add_argument("--pipeline-root",default=str(Path.home()/".cache/workspace-control/mth602-robustness-pipeline"))
    ap.add_argument("--tolerance",type=float,default=1e-12)
    a=ap.parse_args()

    manifest=readj(Path(a.manifest))
    policy=load_policy(REPO_ROOT/"manifests/mth602_robustness_cached_osr_policy_v1.json")
    cells=[c for lane in manifest["lanes"] for c in lane["cells"]]
    root=Path(a.pipeline_root).expanduser().resolve()
    started=time.time()
    all_rows=[]; errors=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futs={pool.submit(run_cell,c,root,policy,a.tolerance):c["run_name"] for c in cells}
        for fut in as_completed(futs):
            rn=futs[fut]
            try:
                rows=fut.result(); all_rows.extend(rows)
                p=sum(1 for r in rows if r["pass"])
                print(f"SAME_EVIDENCE_CELL | run={rn} | pass={p}/{len(rows)}",flush=True)
            except Exception as e:
                errors.append(f"{rn}: {type(e).__name__}: {e}")
                print(f"SAME_EVIDENCE_ERROR | run={rn} | {type(e).__name__}: {e}",flush=True)

    all_rows.sort(key=lambda r:(r["run_name"],r["direction"],r["method"]))
    failed=[r for r in all_rows if not r["pass"]]
    status="PASS" if not errors and len(all_rows)==24 and not failed else "FAIL"
    report={
        "schema":"padataset.mth602-robustness-same-evidence-parity.v1",
        "status":status,
        "rows":len(all_rows),
        "expected_rows":24,
        "tolerance":a.tolerance,
        "failed_rows":len(failed),
        "errors":errors,
        "max_metric_abs_delta":max((r["max_metric_abs_delta"] for r in all_rows),default=None),
        "known_final_pred_mismatch_total":sum(r["known_final_pred_mismatch"] for r in all_rows),
        "open_final_pred_mismatch_total":sum(r["open_final_pred_mismatch"] for r in all_rows),
        "target_labels_used_for_tuning":False,
        "elapsed_sec":time.time()-started,
        "results":all_rows,
    }
    out=root/"parity"/"same_evidence_parity.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(
        f"SAME_EVIDENCE_PARITY={status} | rows={len(all_rows)}/24 | "
        f"failed={len(failed)} | max_metric_abs_delta={report['max_metric_abs_delta']} | "
        f"known_pred_mismatch={report['known_final_pred_mismatch_total']} | "
        f"open_pred_mismatch={report['open_final_pred_mismatch_total']} | errors={len(errors)}",
        flush=True,
    )
    print(f"REPORT={out}",flush=True)
    return 0 if status=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
