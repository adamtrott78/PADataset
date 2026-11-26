#!/usr/bin/env python3
from __future__ import annotations
import glob, json, os, subprocess, time
from pathlib import Path

def cmd(args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT, timeout=10)
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"

def read_text(p, n=12000):
    try:
        return Path(p).read_text(errors="replace")[-n:]
    except Exception as e:
        return f"ERROR: {e}"

def main():
    out={"time":time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    out["loadavg"]=read_text("/proc/loadavg",1000)
    out["meminfo"]="\n".join(read_text("/proc/meminfo",12000).splitlines()[:25])
    out["nvidia_smi"]=cmd(["nvidia-smi",
        "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,utilization.memory,temperature.gpu,pstate",
        "--format=csv,noheader,nounits"])
    out["nvidia_compute"]=cmd(["nvidia-smi",
        "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
        "--format=csv,noheader,nounits"])
    ps=cmd(["ps","-eo","pid,ppid,etimes,%cpu,%mem,rss,vsz,stat,args","--sort=-%cpu"])
    keep=[]
    needles=("pa_eval","l2o","dqnguard","dqn_guard","controls_v1","varmax","python","Runner.Worker","Runner.Listener")
    for line in ps.splitlines():
        if line.startswith("  PID") or any(n.lower() in line.lower() for n in needles):
            keep.append(line)
    out["processes"]="\n".join(keep[:250])
    roots=[
        "/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results",
        "/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results",
    ]
    result_dirs=[]
    for pat in roots:
        result_dirs.extend(glob.glob(pat))
    out["scientific_result_roots"]=sorted(set(result_dirs))
    interesting=[]
    for root in sorted(set(result_dirs)):
        rp=Path(root)
        for p in rp.rglob("*"):
            try:
                if not p.is_file(): continue
                nm=p.name.lower()
                if any(k in nm for k in ("progress","result","summary","receipt","error","complete")):
                    st=p.stat()
                    interesting.append({
                        "path":str(p),
                        "mtime":st.st_mtime,
                        "age_sec":time.time()-st.st_mtime,
                        "size":st.st_size,
                        "tail":read_text(p,4000) if st.st_size <= 200000 else "<large>"
                    })
            except Exception:
                pass
    interesting.sort(key=lambda x:x["mtime"], reverse=True)
    out["recent_result_files"]=interesting[:80]
    # Look for runner diagnostics/workflow temp files mentioning the live evaluator scripts.
    hits=[]
    pats=[
        "/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/*",
        "/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/*",
    ]
    for pat in pats:
        for s in glob.glob(pat):
            p=Path(s)
            try:
                if p.is_file() and p.stat().st_size < 200000:
                    txt=p.read_text(errors="replace")
                    low=txt.lower()
                    if "l2o_control_eval" in low or "l2o_directional_eval" in low or "pa_eval_l2o" in low:
                        hits.append({"path":str(p),"age_sec":time.time()-p.stat().st_mtime,"tail":txt[-6000:]})
            except Exception:
                pass
    hits.sort(key=lambda x:x["age_sec"])
    out["runner_temp_hits"]=hits[:40]
    print(json.dumps(out, indent=2, sort_keys=True))

if __name__=="__main__":
    main()
