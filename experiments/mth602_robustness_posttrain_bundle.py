#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, time
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS","4")
os.environ.setdefault("MKL_NUM_THREADS","4")
os.environ.setdefault("OPENBLAS_NUM_THREADS","4")
os.environ.setdefault("NUMEXPR_NUM_THREADS","4")

import numpy as np
import torch
torch.set_num_threads(min(4,max(1,os.cpu_count() or 1)))
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

from osr_core import BackbonePayload, load_backbone_run
from evaluate import _make_setup_from_run_config
from prepData import build_data_from_setup
from experiments.l2o_directional_contract import resolve_directional_l2o_contract
from experiments.mth602_robustness_calibration_cache import load_backbone_run as _unused, collect_logits, save_split, sha256_file
from experiments.mth602_robustness_cached_all_osr import load_policy, load_split, payload_meta
from experiments.pa_eval_dqn_guard_surrogate_open import cap_split, make_method
from experiments.pa_eval_l2o_controls_v1 import make_dqn_control, make_varmax_control, build_varmax_calibration

FREEZE_SCHEMA="padataset.mth602-robustness-frozen-methods.v1"
TARGET_SCHEMA="padataset.mth602-robustness-target-cache.v1"
BUNDLE_SCHEMA="padataset.mth602-robustness-posttrain-bundle.v1"

def _cpolicy():
    return {"controls":{
      "dqn_ids_style":{
        "method_id":"dqn_ids_style_softmax3_external_surrogate_cap625_v1","state_mode":"softmax3",
        "final_decision":"hard_dqn_argmax","open_calibration_source":"external_surrogate_validation",
        "gamma":0.95,"epsilon":1.0,"epsilon_min":0.05,"epsilon_decay":0.99,"learning_rate":0.001,
        "memory_size":2000,"dqn_batch_size":32,"episodes":30,"anchor_fraction":0.05,
        "train_subsample_size":1250,"centroid_update_threshold":0.75,"seed":42,"device":"cpu",
        "known_cap":625,"open_cap":625
      },
      "varmax":{
        "method_id":"varmax_surrogate_all_smoke_matched_l2o_v1","calibration_mode":"surrogate_all",
        "sweep_grid":"smoke","external_surrogate_consumed":False,"temperature":1.0,"use_energy":True,
        "fit_on":"predicted_class","min_samples_per_class":5
      }
    }}

def _fit_one(handle,known_val,known_bal,known_test,surrogate_val,target,surrogate,policy):
    meta=payload_meta(handle,target); pseed=int(meta["partition_seed"])
    fit_payload=BackbonePayload(meta=meta,val_known=known_val,test_known=known_test,test_open=None)
    dgcfg=policy["methods"]["dqnguard"]
    kc=cap_split(known_val,int(dgcfg["known_cap"]),pseed+101,True,"dqnguard_known")
    oc=cap_split(surrogate_val,int(dgcfg["open_cap"]),pseed+202,False,"dqnguard_surrogate")
    dg=make_method(str(dgcfg["band_accept_mode"]))
    dg.fit(fit_payload,calibration={"calibration_mode":f"surrogate_{surrogate}_var_energy_cap{dgcfg['open_cap']}","calibration_known":kc,"calibration_open":oc})
    u=int(meta["num_classes"])
    ckp=dg.predict(kc,unknown_label=u)
    thr=float(np.percentile(ckp["unknown_score"],100.0*(1.0-float(dgcfg["max_known_reject_cal"]))))

    cp=_cpolicy()
    di=make_dqn_control(cp)
    dik=cap_split(known_val,625,pseed+101,True,"dqnids_known")
    dio=cap_split(surrogate_val,625,pseed+202,False,"dqnids_surrogate")
    di.fit(fit_payload,calibration={"calibration_mode":"external_surrogate_cap625","calibration_known":dik,"calibration_open":dio})
    vm=make_varmax_control(cp)
    extras={"val_known_balanced":known_bal,"val_open":None,"val_open_balanced":None}
    vm.fit(fit_payload,calibration=build_varmax_calibration(fit_payload,extras,cp))
    return {"target":target,"surrogate":surrogate,"meta":meta,"dqnguard":dg,"dqnguard_threshold":thr,"dqnids":di,"varmax":vm}

def freeze_methods(*,run_dir:Path,cache_dir:Path,pair_a:str,pair_b:str,policy_path:Path,out_dir:Path):
    out_dir.mkdir(parents=True,exist_ok=True)
    policy=load_policy(policy_path)
    handle=load_backbone_run(str(run_dir),"best_model",device="cpu")
    known_val=load_split(cache_dir/"known_val.npz")
    known_test=load_split(cache_dir/"known_test.npz")
    kb=cache_dir/"known_val_balanced.npz"; known_bal=load_split(kb) if kb.is_file() else None
    frozen={}
    for target,sur in ((pair_a,pair_b),(pair_b,pair_a)):
        surrogate_val=load_split(cache_dir/f"val_open_{sur}.npz")
        key=f"{target}_from_{sur}"
        frozen[key]=_fit_one(handle,known_val,known_bal,known_test,surrogate_val,target,sur,policy)
    pt=out_dir/"frozen_methods.pt"
    torch.save({"schema":FREEZE_SCHEMA,"run_name":handle.run_name,"pair":[pair_a,pair_b],"directions":frozen},pt)
    rec={
      "schema":FREEZE_SCHEMA,"status":"SUCCESS","run_name":handle.run_name,"pair":[pair_a,pair_b],
      "partition_seed":int(handle.config.get("partition_seed",handle.config.get("seed",0)) or 0),
      "training_seed":int(handle.config.get("training_seed",handle.config.get("seed",0)) or 0),
      "checkpoint_sha256":sha256_file(Path(handle.checkpoint_path)),
      "config_sha256":sha256_file(Path(handle.run_dir)/"config.json"),
      "frozen_methods_sha256":sha256_file(pt),
      "target_test_materialized_before_freeze":False,
      "target_test_consumed_before_method_fit":False,
      "frozen_at":time.strftime("%Y-%m-%dT%H:%M:%S%z")
    }
    (out_dir/"methods_frozen.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(f"ROBUST_METHODS_FROZEN | run_name={handle.run_name} | directions=2 | target_test_consumed_before_method_fit=false",flush=True)
    return rec

def _build_target_data(cfg,data_root,batch_size,num_workers):
    setup=_make_setup_from_run_config(cfg,data_root=data_root)
    return build_data_from_setup(setup,batch_size=batch_size,num_workers=num_workers,pin_memory=True,
      loader_seed=int(cfg.get("training_seed",cfg.get("seed",0)) or 0))

def _close(data):
    try:
        ds=data.get("dataset")
        if hasattr(ds,"close"): ds.close()
    except Exception:
        pass

def build_target_cache(*,run_dir:Path,freeze_dir:Path,pair_a:str,pair_b:str,out_dir:Path,data_root:str,batch_size:int=128,num_workers:int=4):
    frec=json.loads((freeze_dir/"methods_frozen.json").read_text())
    if frec.get("status")!="SUCCESS" or frec.get("target_test_consumed_before_method_fit") is not False:
        raise RuntimeError("methods must be durably frozen before target-test materialization")
    if sha256_file(freeze_dir/"frozen_methods.pt")!=frec["frozen_methods_sha256"]:
        raise RuntimeError("frozen methods provenance mismatch")
    out_dir.mkdir(parents=True,exist_ok=True)
    handle=load_backbone_run(str(run_dir),"best_model",device="cuda")
    files={}
    for target,sur in ((pair_a,pair_b),(pair_b,pair_a)):
        contract=resolve_directional_l2o_contract(handle.config,evaluation_target=target,evaluation_surrogate=sur,model_class_names=handle.class_names)
        data=_build_target_data(contract.target_config,data_root,batch_size,num_workers)
        try:
            files[f"test_open_{target}"]=save_split(out_dir/f"test_open_{target}.npz",collect_logits(handle,data["test_open_loader"],f"test_open_{target}"))
        finally:
            _close(data)
    manifest={
      "schema":TARGET_SCHEMA,"status":"SUCCESS","run_name":handle.run_name,"pair":[pair_a,pair_b],
      "checkpoint_sha256":sha256_file(Path(handle.checkpoint_path)),
      "config_sha256":sha256_file(Path(handle.run_dir)/"config.json"),
      "methods_frozen_sha256":frec["frozen_methods_sha256"],
      "methods_frozen_before_target_test":True,
      "target_labels_used_for_tuning":False,
      "target_test_consumed_before_method_fit":False,
      "files":files
    }
    (out_dir/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    (out_dir/"target_cache_complete.json").write_text(json.dumps({"schema":TARGET_SCHEMA,"status":"SUCCESS","methods_frozen_before_target_test":True},indent=2,sort_keys=True)+"\n")
    print(f"ROBUST_TARGET_CACHE_COMPLETE | run_name={handle.run_name} | targets=2 | methods_frozen_before_target_test=true",flush=True)
    return manifest

def build_posttrain_osr_bundle(*,run_dir:Path,calibration_cache_dir:Path,pair_a:str,pair_b:str,policy_path:Path,data_root:str,batch_size:int=128,num_workers:int=4):
    bundle=run_dir/"osr_posttrain_bundle"; freeze_dir=bundle/"frozen"; target_dir=bundle/"target_cache"
    frec=freeze_methods(run_dir=run_dir,cache_dir=calibration_cache_dir,pair_a=pair_a,pair_b=pair_b,policy_path=policy_path,out_dir=freeze_dir)
    tman=build_target_cache(run_dir=run_dir,freeze_dir=freeze_dir,pair_a=pair_a,pair_b=pair_b,out_dir=target_dir,data_root=data_root,batch_size=batch_size,num_workers=num_workers)
    done={"schema":BUNDLE_SCHEMA,"status":"SUCCESS","run_name":frec["run_name"],"pair":[pair_a,pair_b],"methods_frozen_sha256":frec["frozen_methods_sha256"],"methods_frozen_before_target_test":True,"target_test_consumed_before_method_fit":False}
    (bundle/"bundle_complete.json").write_text(json.dumps(done,indent=2,sort_keys=True)+"\n")
    return done
