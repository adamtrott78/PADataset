#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

from evaluate import _make_setup_from_run_config
from osr_core import load_backbone_run
from prepData import build_data_from_setup
from experiments.l2o_directional_contract import resolve_directional_l2o_contract

SCHEMA = "padataset.mth602-robustness-calibration-cache.v1"

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def collect_logits(handle, loader, split_name: str) -> dict[str, Any]:
    if loader is None:
        raise RuntimeError(f"required calibration loader missing: {split_name}")
    handle.model.eval()
    ys=[]; logits=[]; probs=[]; preds=[]
    with torch.no_grad():
        for batch in loader:
            x,y = batch[:2]
            x=x.to(handle.device, non_blocking=True)
            z=handle.model(x)
            p=torch.softmax(z,dim=1)
            ys.append(y.cpu().numpy())
            logits.append(z.cpu().numpy())
            probs.append(p.cpu().numpy())
            preds.append(z.argmax(dim=1).cpu().numpy())
    if not ys:
        raise RuntimeError(f"empty calibration split: {split_name}")
    return {
        "split_name":split_name,
        "y_true":np.concatenate(ys),
        "logits":np.concatenate(logits),
        "probs":np.concatenate(probs),
        "closed_pred":np.concatenate(preds),
    }

def save_split(path: Path, d: dict[str, Any]) -> dict[str, Any]:
    np.savez_compressed(
        path,
        split_name=np.asarray(d["split_name"]),
        y_true=d["y_true"],
        logits=d["logits"],
        probs=d["probs"],
        closed_pred=d["closed_pred"],
    )
    return {"path":path.name,"sha256":sha256_file(path),"n":int(len(d["y_true"]))}

def build_data(cfg: dict, data_root: str, batch_size: int, num_workers: int):
    setup=_make_setup_from_run_config(cfg,data_root=data_root)
    return build_data_from_setup(
        setup,batch_size=batch_size,num_workers=num_workers,pin_memory=True,
        loader_seed=int(cfg.get("training_seed",cfg.get("seed",0)) or 0),
    )

def close_data(data):
    try:
        ds=data.get("dataset")
        if hasattr(ds,"close"): ds.close()
    except Exception:
        pass

def build_calibration_cache(*,run_dir:Path,checkpoint:str,pair_a:str,pair_b:str,out_dir:Path,data_root:str,device:str,batch_size:int,num_workers:int):
    if device!="cuda":
        raise ValueError("post-training calibration-cache builder must use cuda")
    out_dir.mkdir(parents=True,exist_ok=True)
    handle=load_backbone_run(str(run_dir),checkpoint,device=device)
    ca=resolve_directional_l2o_contract(handle.config,evaluation_target=pair_a,evaluation_surrogate=pair_b,model_class_names=handle.class_names)
    cb=resolve_directional_l2o_contract(handle.config,evaluation_target=pair_b,evaluation_surrogate=pair_a,model_class_names=handle.class_names)

    files={}
    da=build_data(ca.target_config,data_root,batch_size,num_workers)
    try:
        files["known_val"]=save_split(out_dir/"known_val.npz",collect_logits(handle,da["val_loader"],"known_val"))
        files["known_test"]=save_split(out_dir/"known_test.npz",collect_logits(handle,da["test_known_loader"],"known_test"))
        bal=da.get("val_known_balanced_loader")
        if bal is not None:
            files["known_val_balanced"]=save_split(out_dir/"known_val_balanced.npz",collect_logits(handle,bal,"known_val_balanced"))
        files[f"val_open_{pair_a}"]=save_split(out_dir/f"val_open_{pair_a}.npz",collect_logits(handle,da["val_open_loader"],f"val_open_{pair_a}"))
    finally:
        close_data(da)

    db=build_data(cb.target_config,data_root,batch_size,num_workers)
    try:
        files[f"val_open_{pair_b}"]=save_split(out_dir/f"val_open_{pair_b}.npz",collect_logits(handle,db["val_open_loader"],f"val_open_{pair_b}"))
    finally:
        close_data(db)

    manifest={
        "schema":SCHEMA,
        "run_name":handle.run_name,
        "checkpoint":handle.checkpoint_tag,
        "checkpoint_sha256":sha256_file(Path(handle.checkpoint_path)),
        "config_sha256":sha256_file(Path(handle.run_dir)/"config.json"),
        "pair":[pair_a,pair_b],
        "class_names":list(handle.class_names),
        "num_classes":int(handle.num_classes),
        "partition_seed":int(handle.config.get("partition_seed",handle.config.get("seed",0)) or 0),
        "training_seed":int(handle.config.get("training_seed",handle.config.get("seed",0)) or 0),
        "target_test_materialized":False,
        "target_labels_used_for_tuning":False,
        "device":"cuda",
        "files":files,
    }
    (out_dir/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    complete={"schema":"padataset.mth602-robustness-calibration-cache-complete.v1","status":"SUCCESS","manifest_sha256":sha256_file(out_dir/"manifest.json"),"target_test_materialized":False}
    (out_dir/"cache_complete.json").write_text(json.dumps(complete,indent=2,sort_keys=True)+"\n")
    print(f"ROBUST_CACHE_COMPLETE | run_name={handle.run_name} | pair={pair_a}-{pair_b} | target_test_materialized=false",flush=True)
    return {"path":str(out_dir),"manifest_sha256":complete["manifest_sha256"],"target_test_materialized":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-dir",required=True); ap.add_argument("--checkpoint",default="best_model")
    ap.add_argument("--pair-a",required=True); ap.add_argument("--pair-b",required=True)
    ap.add_argument("--out-dir",required=True); ap.add_argument("--data-root",required=True)
    ap.add_argument("--device",default="cuda"); ap.add_argument("--batch-size",type=int,default=128); ap.add_argument("--num-workers",type=int,default=0)
    a=ap.parse_args()
    build_calibration_cache(run_dir=Path(a.run_dir),checkpoint=a.checkpoint,pair_a=a.pair_a,pair_b=a.pair_b,out_dir=Path(a.out_dir),data_root=a.data_root,device=a.device,batch_size=a.batch_size,num_workers=a.num_workers)

if __name__=="__main__": main()
