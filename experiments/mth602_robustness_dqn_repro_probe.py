#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path

REPO_ROOT=Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0,str(REPO_ROOT))

os.environ["OMP_NUM_THREADS"]="1"
os.environ["MKL_NUM_THREADS"]="1"
os.environ["OPENBLAS_NUM_THREADS"]="1"
os.environ["NUMEXPR_NUM_THREADS"]="1"
os.environ["CUDA_VISIBLE_DEVICES"]=""

import numpy as np
import torch
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)

from osr_core import BackbonePayload, load_backbone_run
from experiments.mth602_robustness_cached_all_osr import load_policy, load_split, payload_meta
from experiments.mth602_robustness_posttrain_bundle import _fit_one


def tensor_sha(module)->str:
    h=hashlib.sha256()
    for k,v in sorted(module.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def pred_sig(method,split,u:int):
    p=method.predict(split,unknown_label=u)
    return {
        "final_pred":np.asarray(p["final_pred"],dtype=np.int64),
        "unknown_score":np.asarray(p["unknown_score"],dtype=np.float32),
    }


def fit_once(run_dir,cache_dir,target,surrogate,policy):
    handle=load_backbone_run(str(run_dir),"best_model",device="cpu")
    known_val=load_split(cache_dir/"known_val.npz")
    known_test=load_split(cache_dir/"known_test.npz")
    kb=cache_dir/"known_val_balanced.npz"
    known_bal=load_split(kb) if kb.is_file() else None
    surrogate_val=load_split(cache_dir/f"val_open_{surrogate}.npz")
    fr=_fit_one(handle,known_val,known_bal,known_test,surrogate_val,target,surrogate,policy)
    return handle,known_test,fr


def compare(run_dir,cache_dir,target,surrogate,policy):
    h1,known_test,a=fit_once(run_dir,cache_dir,target,surrogate,policy)
    h2,known_test2,b=fit_once(run_dir,cache_dir,target,surrogate,policy)
    u=int(h1.num_classes)

    adg=a["dqnguard"].dqn.agent.model
    bdg=b["dqnguard"].dqn.agent.model
    adi=a["dqnids"].agent.model
    bdi=b["dqnids"].agent.model

    ap=pred_sig(a["dqnguard"],known_test,u); bp=pred_sig(b["dqnguard"],known_test2,u)
    ai=pred_sig(a["dqnids"],known_test,u); bi=pred_sig(b["dqnids"],known_test2,u)

    out={
      "schema":"padataset.mth602-robustness-dqn-repro-probe.v1",
      "run_name":h1.run_name,
      "direction":f"{target}<-{surrogate}",
      "torch_num_threads":torch.get_num_threads(),
      "deterministic_algorithms":torch.are_deterministic_algorithms_enabled(),
      "dqnguard":{
        "weight_sha_a":tensor_sha(adg),"weight_sha_b":tensor_sha(bdg),
        "weight_identity":tensor_sha(adg)==tensor_sha(bdg),
        "threshold_a":float(a["dqnguard_threshold"]),"threshold_b":float(b["dqnguard_threshold"]),
        "threshold_delta":abs(float(a["dqnguard_threshold"])-float(b["dqnguard_threshold"])),
        "known_pred_mismatch":int(np.count_nonzero(ap["final_pred"]!=bp["final_pred"])),
        "known_score_max_abs_delta":float(np.max(np.abs(ap["unknown_score"]-bp["unknown_score"]))),
      },
      "dqnids":{
        "weight_sha_a":tensor_sha(adi),"weight_sha_b":tensor_sha(bdi),
        "weight_identity":tensor_sha(adi)==tensor_sha(bdi),
        "known_pred_mismatch":int(np.count_nonzero(ai["final_pred"]!=bi["final_pred"])),
        "known_score_max_abs_delta":float(np.max(np.abs(ai["unknown_score"]-bi["unknown_score"]))),
      },
    }
    out["status"]="PASS" if (
      out["dqnguard"]["weight_identity"] and
      out["dqnids"]["weight_identity"] and
      out["dqnguard"]["threshold_delta"]==0.0 and
      out["dqnguard"]["known_pred_mismatch"]==0 and
      out["dqnids"]["known_pred_mismatch"]==0 and
      out["dqnguard"]["known_score_max_abs_delta"]==0.0 and
      out["dqnids"]["known_score_max_abs_delta"]==0.0
    ) else "FAIL"
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--pipeline-root",default=str(Path.home()/".cache/workspace-control/mth602-robustness-pipeline"))
    ap.add_argument("--run-name",default="mth602_robust_smoke_A_PA1_PA2_p01_t00")
    ap.add_argument("--target",default="PA1")
    ap.add_argument("--surrogate",default="PA2")
    a=ap.parse_args()
    root=Path(a.pipeline_root).expanduser().resolve()
    run_dir=root/"backbones"/a.run_name
    cache_dir=run_dir/"osr_calibration_cache"
    policy=load_policy(REPO_ROOT/"manifests/mth602_robustness_cached_osr_policy_v1.json")
    out=compare(run_dir,cache_dir,a.target,a.surrogate,policy)
    dest=root/"parity"/"dqn_repro_probe.json"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(
      f"DQN_REPRO={out['status']} | run={out['run_name']} | direction={out['direction']} | "
      f"threads={out['torch_num_threads']} | deterministic={out['deterministic_algorithms']} | "
      f"DQNG_weight_identity={out['dqnguard']['weight_identity']} | "
      f"DQNG_pred_mismatch={out['dqnguard']['known_pred_mismatch']} | "
      f"IDS_weight_identity={out['dqnids']['weight_identity']} | "
      f"IDS_pred_mismatch={out['dqnids']['known_pred_mismatch']}",
      flush=True,
    )
    print(f"REPORT={dest}",flush=True)
    return 0 if out["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
