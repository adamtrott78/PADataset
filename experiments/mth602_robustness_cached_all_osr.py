#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import torch

from evaluate import _make_setup_from_run_config
from osr_core import BackbonePayload, SplitOutputs, evaluate_osr_predictions, load_backbone_run
from prepData import build_data_from_setup
from experiments.l2o_directional_contract import resolve_directional_l2o_contract
from experiments.pa_eval_dqn_guard_surrogate_open import cap_split, make_method
from experiments.pa_eval_l2o_controls_v1 import make_dqn_control, make_varmax_control, build_varmax_calibration

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

def collect_target_test_once(handle,cfg,data_root,batch_size,num_workers,split_name):
    setup=_make_setup_from_run_config(cfg,data_root=data_root)
    data=build_data_from_setup(setup,batch_size=batch_size,num_workers=num_workers,pin_memory=False,loader_seed=int(cfg.get("training_seed",cfg.get("seed",0)) or 0))
    try:
        loader=data["test_open_loader"]
        ys=[]; logits=[]; probs=[]; preds=[]
        handle.model.eval()
        with torch.no_grad():
            for batch in loader:
                x,y=batch[:2]
                x=x.to(handle.device)
                z=handle.model(x)
                p=torch.softmax(z,dim=1)
                ys.append(y.cpu().numpy()); logits.append(z.cpu().numpy()); probs.append(p.cpu().numpy()); preds.append(z.argmax(dim=1).cpu().numpy())
        y=np.concatenate(ys); zz=np.concatenate(logits); pp=np.concatenate(probs); pr=np.concatenate(preds)
        return SplitOutputs(split_name,y,zz,np.empty((len(y),0),dtype=np.float32),pr,pp,None)
    finally:
        ds=data.get("dataset")
        if hasattr(ds,"close"): ds.close()

def payload_meta(handle,target):
    legacy=int(handle.config.get("seed",0) or 0)
    return {
        "run_name":handle.run_name,"run_dir":handle.run_dir,"checkpoint_tag":handle.checkpoint_tag,
        "unknown_pas":[target],"class_names":list(handle.class_names),"num_classes":int(handle.num_classes),
        "cache_len":handle.config.get("cache_len"),
        "seed":int(handle.config.get("training_seed",legacy) or 0),
        "partition_seed":int(handle.config.get("partition_seed",legacy) or 0),
        "training_seed":int(handle.config.get("training_seed",legacy) or 0),
        "epochs":handle.config.get("epochs"),"source_type":handle.config.get("source_type","digital"),
        "source_name":handle.config.get("source_name","pilot_noisy_torch"),"dataset_tag":handle.config.get("dataset_tag"),"noise_tag":handle.config.get("noise_tag"),
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

def run_direction(*,handle,known_val,known_val_balanced,known_test,surrogate_val,target,surrogate,policy,data_root,batch_size,num_workers,out_dir,progress_path):
    meta=payload_meta(handle,target); pseed=int(meta["partition_seed"])
    fit_payload=BackbonePayload(meta=meta,val_known=known_val,test_known=known_test,test_open=None)

    def progress(phase,**extra):
        d={"schema":"padataset.mth602-robustness-osr-progress.v1","run_name":handle.run_name,"direction":f"{target}<-{surrogate}","phase":phase,"time":time.strftime("%Y-%m-%dT%H:%M:%S%z"),**extra}
        tmp=progress_path.with_suffix(".tmp"); tmp.write_text(json.dumps(d,indent=2)+"\n"); tmp.replace(progress_path)

    progress("fit_methods_start")
    dgcfg=policy["methods"]["dqnguard"]; known_cap=cap_split(known_val,int(dgcfg["known_cap"]),pseed+101,True,"dqnguard_known"); open_cap=cap_split(surrogate_val,int(dgcfg["open_cap"]),pseed+202,False,"dqnguard_surrogate")
    dg=make_method(str(dgcfg["band_accept_mode"])); dg.fit(fit_payload,calibration={"calibration_mode":f"surrogate_{surrogate}_var_energy_cap{dgcfg['open_cap']}","calibration_known":known_cap,"calibration_open":open_cap})
    u=int(meta["num_classes"]); cal_known=dg.predict(known_cap,unknown_label=u); threshold=float(np.percentile(cal_known["unknown_score"],100.0*(1.0-float(dgcfg["max_known_reject_cal"]))))

    cpolicy={"controls":{"dqn_ids_style":{
        "method_id":"dqn_ids_style_softmax3_external_surrogate_cap625_v1","state_mode":"softmax3","final_decision":"hard_dqn_argmax","open_calibration_source":"external_surrogate_validation",
        "gamma":0.95,"epsilon":1.0,"epsilon_min":0.05,"epsilon_decay":0.99,"learning_rate":0.001,"memory_size":2000,"dqn_batch_size":32,"episodes":30,"anchor_fraction":0.05,"train_subsample_size":1250,"centroid_update_threshold":0.75,"seed":42,"device":"cpu","known_cap":625,"open_cap":625
    },"varmax":{"method_id":"varmax_surrogate_all_smoke_matched_l2o_v1","calibration_mode":"surrogate_all","sweep_grid":"smoke","external_surrogate_consumed":False,"temperature":1.0,"use_energy":True,"fit_on":"predicted_class","min_samples_per_class":5}}}
    di=make_dqn_control(cpolicy); di_known=cap_split(known_val,625,pseed+101,True,"dqnids_known"); di_open=cap_split(surrogate_val,625,pseed+202,False,"dqnids_surrogate")
    di.fit(fit_payload,calibration={"calibration_mode":"external_surrogate_cap625","calibration_known":di_known,"calibration_open":di_open})
    vm=make_varmax_control(cpolicy); extras={"val_known_balanced":known_val_balanced,"val_open":None,"val_open_balanced":None}; vmcal=build_varmax_calibration(fit_payload,extras,cpolicy); vm.fit(fit_payload,calibration=vmcal)
    progress("methods_frozen_before_target_test")

    contract=resolve_directional_l2o_contract(handle.config,evaluation_target=target,evaluation_surrogate=surrogate,model_class_names=handle.class_names)
    target_test=collect_target_test_once(handle,contract.target_config,data_root,batch_size,num_workers,f"test_open_{target}")
    eval_payload=BackbonePayload(meta=meta,val_known=known_val,test_known=known_test,test_open=target_test)
    progress("target_test_materialized_once",target_test_n=int(len(target_test.y_true)))

    known_base=dg.predict(known_test,unknown_label=u); open_base=dg.predict(target_test,unknown_label=u)
    dg_metrics=evaluate_osr_predictions(known_split=known_test,open_split=target_test,known_pred=apply_threshold(known_base,threshold,u),open_pred=apply_threshold(open_base,threshold,u),known_class_names=meta["class_names"],unknown_label_name="unknown")
    dg_row={"method":"DQNGuard","method_id":"l2o_dqnguard_track_a_frozen_v1","score_threshold":threshold,**{k:float(dg_metrics[k]) for k in ("known_reject_rate","unknown_precision","unknown_recall","unknown_f1","osr_acc","osr_macro_f1","unknown_auroc")}}
    di_row={"method":"DQN-IDS-style","method_id":"dqn_ids_style_softmax3_external_surrogate_cap625_v1",**scalar_metrics(di,eval_payload)}
    vm_row={"method":"VarMax","method_id":"varmax_surrogate_all_smoke_matched_l2o_v1",**scalar_metrics(vm,eval_payload)}
    rows=[]
    for row in (dg_row,di_row,vm_row):
        rows.append({"run_name":handle.run_name,"target":target,"surrogate":surrogate,"partition_seed":meta["partition_seed"],"training_seed":meta["training_seed"],"dqn_seed":42,"target_labels_used_for_tuning":False,"target_test_consumed_before_method_fit":False,**row})
    out_dir.mkdir(parents=True,exist_ok=True); (out_dir/"result.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    progress("direction_complete",results=rows)
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-dir",required=True); ap.add_argument("--cache-dir",required=True); ap.add_argument("--pair-a",required=True); ap.add_argument("--pair-b",required=True)
    ap.add_argument("--out-dir",required=True); ap.add_argument("--data-root",required=True); ap.add_argument("--policy",default="manifests/mth602_robustness_cached_osr_policy_v1.json")
    ap.add_argument("--batch-size",type=int,default=128); ap.add_argument("--num-workers",type=int,default=0); ap.add_argument("--device",default="cpu")
    a=ap.parse_args()
    if a.device!="cpu": raise ValueError("cached robustness OSR consumer is CPU-only")
    if os.environ.get("CUDA_VISIBLE_DEVICES") not in ("","-1"): raise RuntimeError("CPU OSR consumer requires CUDA_VISIBLE_DEVICES hidden")
    policy=load_policy(Path(a.policy)); run_dir=Path(a.run_dir); cache=Path(a.cache_dir); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((cache/"manifest.json").read_text())
    if manifest.get("target_test_materialized") is not False: raise ValueError("calibration cache contains target-test evidence")
    if sha256_file(run_dir/"best_model.pt")!=manifest["checkpoint_sha256"]: raise ValueError("checkpoint/cache provenance mismatch")
    if sha256_file(run_dir/"config.json")!=manifest["config_sha256"]: raise ValueError("config/cache provenance mismatch")
    handle=load_backbone_run(str(run_dir),"best_model",device="cpu")
    known_val=load_split(cache/"known_val.npz"); known_test=load_split(cache/"known_test.npz")
    kb=cache/"known_val_balanced.npz"; known_bal=load_split(kb) if kb.is_file() else None
    all_rows=[]
    for target,sur in ((a.pair_a,a.pair_b),(a.pair_b,a.pair_a)):
        s=load_split(cache/f"val_open_{sur}.npz")
        progress_path=out/f"progress_{target}_from_{sur}.json"
        all_rows.extend(run_direction(handle=handle,known_val=known_val,known_val_balanced=known_bal,known_test=known_test,surrogate_val=s,target=target,surrogate=sur,policy=policy,data_root=a.data_root,batch_size=a.batch_size,num_workers=a.num_workers,out_dir=out/f"target{target}_sur{sur}",progress_path=progress_path))
    pd.DataFrame(all_rows).to_csv(out/"all_methods.csv",index=False)
    done={"schema":"padataset.mth602-robustness-cached-osr-complete.v1","status":"SUCCESS","run_name":handle.run_name,"pair":[a.pair_a,a.pair_b],"partition_seed":manifest["partition_seed"],"training_seed":manifest["training_seed"],"method_direction_rows":len(all_rows),"target_test_passes":2,"target_test_consumed_before_method_fit":False}
    (out/"osr_complete.json").write_text(json.dumps(done,indent=2,sort_keys=True)+"\n")
    print(f"ROBUST_OSR_COMPLETE | run_name={handle.run_name} | rows={len(all_rows)}",flush=True)

if __name__=="__main__": main()
