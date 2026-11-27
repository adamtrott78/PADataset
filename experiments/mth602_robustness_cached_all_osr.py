#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, time
from pathlib import Path
import sys

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0,str(REPO_ROOT))

os.environ.setdefault("OMP_NUM_THREADS","4")
os.environ.setdefault("MKL_NUM_THREADS","4")
os.environ.setdefault("OPENBLAS_NUM_THREADS","4")
os.environ.setdefault("NUMEXPR_NUM_THREADS","4")

import numpy as np
import pandas as pd
import torch
torch.set_num_threads(min(4,max(1,os.cpu_count() or 1)))
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

from osr_core import BackbonePayload, SplitOutputs, evaluate_osr_predictions

POLICY_SCHEMA="padataset.mth602-robustness-cached-osr-policy.v1"

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""): h.update(b)
    return h.hexdigest()

def load_policy(path:Path):
    p=json.loads(path.read_text())
    if p.get("schema")!=POLICY_SCHEMA: raise ValueError("robustness cached OSR policy schema mismatch")
    if p.get("status")!="CANDIDATE_REQUIRES_PILOT_PARITY_BEFORE_FINAL_SCIENCE": raise ValueError("unexpected robustness policy status")
    if p["firewall"]["target_test_consumed_before_method_fit"] is not False: raise ValueError("policy permits target-test prefit consumption")
    return p

def load_split(path:Path)->SplitOutputs:
    with np.load(path,allow_pickle=False) as z:
        y=np.asarray(z["y_true"]); logits=np.asarray(z["logits"]); probs=np.asarray(z["probs"]); pred=np.asarray(z["closed_pred"])
        return SplitOutputs(str(z["split_name"].item()),y,logits,np.empty((len(y),0),dtype=np.float32),pred,probs,None)

def payload_meta_from_manifests(cal_manifest,target):
    return {
      "run_name":cal_manifest["run_name"],"unknown_pas":[target],"class_names":list(cal_manifest["class_names"]),
      "num_classes":int(cal_manifest["num_classes"]),"seed":int(cal_manifest["training_seed"]),
      "partition_seed":int(cal_manifest["partition_seed"]),"training_seed":int(cal_manifest["training_seed"])
    }

def apply_threshold(base,thr,unknown_label):
    out=dict(base); is_unknown=np.asarray(base["unknown_score"])>=float(thr)
    final=np.asarray(base["closed_pred"]).astype(int).copy(); final[is_unknown]=int(unknown_label)
    out["is_unknown"]=is_unknown.astype(bool); out["final_pred"]=final
    return out

def scalar_metrics(method,payload):
    u=int(payload.meta["num_classes"])
    kp=method.predict(payload.test_known,unknown_label=u); op=method.predict(payload.test_open,unknown_label=u)
    m=evaluate_osr_predictions(known_split=payload.test_known,open_split=payload.test_open,known_pred=kp,open_pred=op,known_class_names=payload.meta["class_names"],unknown_label_name="unknown")
    return {k:float(m[k]) for k in ("known_reject_rate","unknown_precision","unknown_recall","unknown_f1","osr_acc","osr_macro_f1","unknown_auroc")}

def run_cached(*,cache_dir:Path,bundle_dir:Path,pair_a:str,pair_b:str,out_dir:Path,policy_path:Path):
    load_policy(policy_path)
    cal=json.loads((cache_dir/"manifest.json").read_text())
    freeze=json.loads((bundle_dir/"frozen/methods_frozen.json").read_text())
    target=json.loads((bundle_dir/"target_cache/manifest.json").read_text())
    if target.get("methods_frozen_before_target_test") is not True: raise RuntimeError("target cache was not produced after method freeze")
    if target.get("target_test_consumed_before_method_fit") is not False: raise RuntimeError("target-test firewall violated")
    if sha256_file(bundle_dir/"frozen/frozen_methods.pt")!=freeze["frozen_methods_sha256"]: raise RuntimeError("frozen method hash mismatch")
    if target["methods_frozen_sha256"]!=freeze["frozen_methods_sha256"]: raise RuntimeError("target cache/frozen method binding mismatch")
    frozen=torch.load(bundle_dir/"frozen/frozen_methods.pt",map_location="cpu",weights_only=False)
    known_test=load_split(cache_dir/"known_test.npz")
    rows=[]
    out_dir.mkdir(parents=True,exist_ok=True)
    for target_pa,sur in ((pair_a,pair_b),(pair_b,pair_a)):
        key=f"{target_pa}_from_{sur}"; fr=frozen["directions"][key]
        meta=payload_meta_from_manifests(cal,target_pa)
        target_test=load_split(bundle_dir/f"target_cache/test_open_{target_pa}.npz")
        payload=BackbonePayload(meta=meta,val_known=None,test_known=known_test,test_open=target_test)
        u=int(meta["num_classes"])
        dg=fr["dqnguard"]; kb=dg.predict(known_test,unknown_label=u); ob=dg.predict(target_test,unknown_label=u)
        dm=evaluate_osr_predictions(known_split=known_test,open_split=target_test,known_pred=apply_threshold(kb,fr["dqnguard_threshold"],u),open_pred=apply_threshold(ob,fr["dqnguard_threshold"],u),known_class_names=meta["class_names"],unknown_label_name="unknown")
        dr={"method":"DQNGuard","method_id":"l2o_dqnguard_track_a_frozen_v1","score_threshold":float(fr["dqnguard_threshold"]),**{k:float(dm[k]) for k in ("known_reject_rate","unknown_precision","unknown_recall","unknown_f1","osr_acc","osr_macro_f1","unknown_auroc")}}
        ir={"method":"DQN-IDS-style","method_id":"dqn_ids_style_softmax3_external_surrogate_cap625_v1",**scalar_metrics(fr["dqnids"],payload)}
        vr={"method":"VarMax","method_id":"varmax_surrogate_all_smoke_matched_l2o_v1",**scalar_metrics(fr["varmax"],payload)}
        for row in (dr,ir,vr):
            rows.append({"run_name":cal["run_name"],"target":target_pa,"surrogate":sur,"partition_seed":cal["partition_seed"],"training_seed":cal["training_seed"],"dqn_seed":42,"target_labels_used_for_tuning":False,"target_test_consumed_before_method_fit":False,**row})
        p=out_dir/f"progress_{target_pa}_from_{sur}.json"
        p.write_text(json.dumps({"schema":"padataset.mth602-robustness-osr-progress.v2","run_name":cal["run_name"],"direction":f"{target_pa}<-{sur}","phase":"direction_complete","time":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"results":rows[-3:]},indent=2)+"\n")
    pd.DataFrame(rows).to_csv(out_dir/"all_methods.csv",index=False)
    (out_dir/"result.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    done={"schema":"padataset.mth602-robustness-cached-osr-complete.v2","status":"SUCCESS","run_name":cal["run_name"],"pair":[pair_a,pair_b],"partition_seed":cal["partition_seed"],"training_seed":cal["training_seed"],"method_direction_rows":len(rows),"raw_hdf5_reads":0,"backbone_forward_passes":0,"target_test_consumed_before_method_fit":False}
    (out_dir/"osr_complete.json").write_text(json.dumps(done,indent=2,sort_keys=True)+"\n")
    print(f"ROBUST_OSR_COMPLETE | run_name={cal['run_name']} | rows={len(rows)} | raw_hdf5_reads=0 | backbone_forward_passes=0",flush=True)
    return rows

def payload_meta(handle,target):
    legacy=int(handle.config.get("seed",0) or 0)
    return {"run_name":handle.run_name,"run_dir":handle.run_dir,"checkpoint_tag":handle.checkpoint_tag,"unknown_pas":[target],"class_names":list(handle.class_names),"num_classes":int(handle.num_classes),"cache_len":handle.config.get("cache_len"),"seed":int(handle.config.get("training_seed",legacy) or 0),"partition_seed":int(handle.config.get("partition_seed",legacy) or 0),"training_seed":int(handle.config.get("training_seed",legacy) or 0),"epochs":handle.config.get("epochs"),"source_type":handle.config.get("source_type","digital"),"source_name":handle.config.get("source_name","pilot_noisy_torch"),"dataset_tag":handle.config.get("dataset_tag"),"noise_tag":handle.config.get("noise_tag")}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--cache-dir",required=True); ap.add_argument("--bundle-dir",required=True); ap.add_argument("--pair-a",required=True); ap.add_argument("--pair-b",required=True); ap.add_argument("--out-dir",required=True); ap.add_argument("--policy",default="manifests/mth602_robustness_cached_osr_policy_v1.json"); ap.add_argument("--device",default="cpu")
    a=ap.parse_args()
    if a.device!="cpu": raise ValueError("cached robustness OSR consumer is CPU-only")
    if os.environ.get("CUDA_VISIBLE_DEVICES") not in ("","-1"): raise RuntimeError("CPU OSR consumer requires CUDA_VISIBLE_DEVICES hidden")
    run_cached(cache_dir=Path(a.cache_dir),bundle_dir=Path(a.bundle_dir),pair_a=a.pair_a,pair_b=a.pair_b,out_dir=Path(a.out_dir),policy_path=Path(a.policy))

if __name__=="__main__": main()
