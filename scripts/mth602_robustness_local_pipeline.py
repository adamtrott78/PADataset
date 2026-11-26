#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, pwd, shutil, signal, subprocess, sys, time
from pathlib import Path

PATTERNS=[
"/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/backbone/mth602_robust_*",
"/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results/backbone/mth602_robust_*",
]

def operator_home():
    if os.geteuid()==0 and os.environ.get("SUDO_USER"):
        return Path(pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir)
    return Path.home()

def read_json(p):
    try:return json.loads(Path(p).read_text())
    except Exception:return None

def atomic_json(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n"); tmp.replace(path)

def discover():
    import glob
    out={}
    for pat in PATTERNS:
        for s in glob.glob(pat):
            p=Path(s); c=read_json(p/"config.json")
            if not c or not c.get("post_train_osr_calibration_cache"): continue
            if not (p/"train_complete.json").is_file() or not (p/"osr_calibration_cache/cache_complete.json").is_file() or not (p/"osr_posttrain_bundle/bundle_complete.json").is_file(): continue
            out[p.name]=p
    return out

def copy_ready(src,dst):
    dst.mkdir(parents=True,exist_ok=True)
    for name in ("config.json","summary.json","train_complete.json","best_model.pt"):
        sp=src/name; dp=dst/name
        if sp.is_file() and not dp.is_file(): shutil.copy2(sp,dp)
    for sub, marker in (("osr_calibration_cache","cache_complete.json"),("osr_posttrain_bundle","bundle_complete.json")):
        sc=src/sub; dc=dst/sub
        if sc.is_dir() and not (dc/marker).is_file():
            tmp=dst/(sub+".tmp")
            if tmp.exists(): shutil.rmtree(tmp)
            shutil.copytree(sc,tmp); tmp.replace(dc)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--repo",default=str(Path(__file__).resolve().parents[1])); ap.add_argument("--runtime-python",default=sys.executable)
    ap.add_argument("--data-root",default="/srv/workspace-ci/padataset/trusted-cache/scientific-data/ota_core_high_run01_len16384_v1")
    ap.add_argument("--max-workers",type=int,default=2); ap.add_argument("--refresh",type=float,default=2.0); ap.add_argument("--once",action="store_true")
    a=ap.parse_args()
    root=operator_home()/".cache/workspace-control/mth602-robustness-pipeline"; backbones=root/"backbones"; results=root/"osr"; logs=root/"logs"; root.mkdir(parents=True,exist_ok=True)
    workers={}
    stop=False
    def sig(*_):
        nonlocal stop; stop=True
    signal.signal(signal.SIGINT,sig); signal.signal(signal.SIGTERM,sig)
    while not stop:
        for rn,src in discover().items():
            dst=backbones/rn; copy_ready(src,dst)
        for rn,p in list(workers.items()):
            rc=p.poll()
            if rc is not None: workers.pop(rn,None)
        candidates=[]
        for d in sorted(backbones.glob("mth602_robust_*")):
            cfg=read_json(d/"config.json") or {}; pair=str((cfg.get("robustness_replication") or {}).get("canonical_pair") or "")
            if len(pair.split("-"))!=2: continue
            od=results/d.name
            if (od/"osr_complete.json").is_file() or d.name in workers: continue
            candidates.append((d,pair,od))
        while candidates and len(workers)<a.max_workers:
            d,pair,od=candidates.pop(0); pa,pb=pair.split("-"); od.mkdir(parents=True,exist_ok=True); logs.mkdir(parents=True,exist_ok=True)
            log=(logs/f"{d.name}.log").open("ab",buffering=0)
            env=os.environ.copy(); env["CUDA_VISIBLE_DEVICES"]=""; env["PYTHONUNBUFFERED"]="1"
            env["OMP_NUM_THREADS"]="4"; env["MKL_NUM_THREADS"]="4"; env["OPENBLAS_NUM_THREADS"]="4"; env["NUMEXPR_NUM_THREADS"]="4"
            cmd=[a.runtime_python,str(Path(a.repo)/"experiments/mth602_robustness_cached_all_osr.py"),"--cache-dir",str(d/"osr_calibration_cache"),"--bundle-dir",str(d/"osr_posttrain_bundle"),"--pair-a",pa,"--pair-b",pb,"--out-dir",str(od),"--policy",str(Path(a.repo)/"manifests/mth602_robustness_cached_osr_policy_v1.json"),"--device","cpu"]
            p=subprocess.Popen(cmd,cwd=a.repo,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            workers[d.name]=p
        state={"schema":"padataset.mth602-robustness-local-pipeline-state.v2","time":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"epoch":time.time(),"pid":os.getpid(),"max_workers":a.max_workers,"active_workers":{k:v.pid for k,v in workers.items()},"backbones_spooled":len(list(backbones.glob("mth602_robust_*"))),"osr_complete":len(list(results.glob("*/osr_complete.json"))),"provider_calls_per_refresh":0}
        atomic_json(root/"pipeline_state.json",state)
        if a.once: break
        time.sleep(a.refresh)
    for p in workers.values():
        if p.poll() is None: p.terminate()

if __name__=="__main__": main()
