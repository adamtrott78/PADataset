#!/usr/bin/env python3
from __future__ import annotations
import argparse, glob, json, os, pwd, re, shlex, shutil, signal, statistics, subprocess, sys, time
from datetime import datetime, timedelta
from pathlib import Path

RESET="\033[0m"; B="\033[1m"; DIM="\033[2m"; GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"; RED="\033[31m"; MAG="\033[35m"
ANSI_RE=re.compile(r"\x1b\[[0-9;]*m")

def clip_ansi(line: str, width: int) -> str:
    width=max(20,int(width))
    out=[]; visible=0; i=0
    while i < len(line) and visible < width:
        if line[i]=="\x1b":
            m=ANSI_RE.match(line,i)
            if m:
                out.append(m.group(0)); i=m.end(); continue
        out.append(line[i]); visible+=1; i+=1
    return "".join(out)+RESET
PAIRS=["PA1-PA2","PA1-PA3","PA1-PA4","PA1-PA8","PA2-PA3","PA2-PA4","PA2-PA8","PA3-PA4","PA3-PA8","PA4-PA8"]
CONDS=[(0,0),(1,0),(2,0),(3,0),(4,0),(0,1)]

def home():
    if os.geteuid()==0 and os.environ.get("SUDO_USER"): return Path(pwd.getpwnam(os.environ["SUDO_USER"]).pw_dir)
    return Path.home()
ROOT=home()/".cache/workspace-control/mth602-robustness-pipeline"

def readj(p):
    try:return json.loads(Path(p).read_text())
    except Exception:return None

def fmt(sec):
    if sec is None:return "-"
    sec=max(0,int(float(sec))); h,r=divmod(sec,3600); m,s=divmod(r,60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

def metric(x):
    try:return f"{float(x):.4f}"
    except:return "-"

def finish_text(eta):
    if eta is None:return "-"
    return (datetime.now()+timedelta(seconds=max(0,float(eta)))).strftime("%H:%M")

def gpu():
    try:
        raw=subprocess.check_output(["nvidia-smi","--query-gpu=index,memory.used,memory.total,utilization.gpu","--format=csv,noheader,nounits"],text=True,stderr=subprocess.DEVNULL)
        return [tuple(x.strip() for x in line.split(",")) for line in raw.splitlines()]
    except:return []

CONTROLLER_UNITS=[
    ("G0","workspace-ci-v3-controller@padataset-scientific-single-gpu-v1.service"),
    ("G1","workspace-ci-v3-controller@padataset-scientific-single-gpu-2-v1.service"),
]

def controller_liveness():
    rows=[]
    for lane,unit in CONTROLLER_UNITS:
        try:
            raw=subprocess.check_output(
                ["systemctl","show",unit,"--property=ActiveState","--property=SubState","--property=MainPID","--property=NRestarts","--no-pager"],
                text=True,stderr=subprocess.DEVNULL,timeout=3,
            )
            props={}
            for line in raw.splitlines():
                if "=" in line:
                    k,v=line.split("=",1); props[k]=v
            active=props.get("ActiveState","?"); sub=props.get("SubState","?")
            state="ACTIVE" if active=="active" and sub=="running" else ("DOWN" if active in {"failed","inactive"} else active.upper())
            rows.append({"lane":lane,"unit":unit,"state":state,"pid":props.get("MainPID","?"),"restarts":props.get("NRestarts","?")})
        except Exception:
            rows.append({"lane":lane,"unit":unit,"state":"UNKNOWN","pid":"?","restarts":"?"})
    return rows

def proc_rows():
    out={}
    try: raw=subprocess.check_output(["ps","-eo","pid=,etimes=,args="],text=True,stderr=subprocess.DEVNULL)
    except:return out
    for line in raw.splitlines():
        if "pa_train_one.py" not in line or "--cfg" not in line:continue
        p=line.strip().split(None,2)
        if len(p)<3:continue
        try:
            argv=shlex.split(p[2]); cfgp=Path(argv[argv.index("--cfg")+1]); cfg=readj(cfgp)
            if not cfg:continue
            rn=str(cfg.get("run_name",""))
            if not rn.startswith("mth602_robust_"):continue
            out[rn]={"pid":int(p[0]),"elapsed":int(p[1]),"cfg":cfg,"run_dir":Path(str(cfg.get("save_root","")))/rn}
        except:continue
    return out

def scan_dirs():
    d={}
    pats=["/srv/workspace-ci/padataset/jobs/*/runner/_work/_temp/scientific-results/backbone/mth602_robust_*","/srv/workspace-ci/padataset/jobs/*/runner*/_work/_temp/scientific-results/backbone/mth602_robust_*"]
    for pat in pats:
        for s in glob.glob(pat): d.setdefault(Path(s).name,[]).append(Path(s))
    for p in (ROOT/"backbones").glob("mth602_robust_*") if (ROOT/"backbones").is_dir() else []: d.setdefault(p.name,[]).append(p)
    return d

def record(rn,dirs,proc):
    best=None
    for rd in dirs.get(rn,[]):
        c=readj(rd/"train_complete.json"); e=readj(rd/"train_error.json"); pr=readj(rd/"train_progress.json"); sm=readj(rd/"summary.json")
        mt=max([x.stat().st_mtime for x in [rd/"train_complete.json",rd/"train_error.json",rd/"train_progress.json",rd/"summary.json"] if x.exists()] or [0])
        item={"rd":rd,"complete":c,"error":e,"progress":pr,"summary":sm,"mtime":mt}
        if best is None or mt>best["mtime"]:best=item
    p=proc.get(rn)
    if p and best is None:best={"rd":p["run_dir"],"complete":None,"error":None,"progress":None,"summary":None,"mtime":0}
    return best,p

def identity_from_cfg(cfg):
    rr=(cfg or {}).get("robustness_replication") or {}
    return rr.get("canonical_pair"),int(rr.get("partition_seed",0)),int(rr.get("training_seed",0))

def glyph(status):
    return {"SUCCESS":GREEN+"✓"+RESET,"RUNNING":YELLOW+"▶"+RESET,"ERROR":RED+"×"+RESET,"OSR":CYAN+"O"+RESET}.get(status,DIM+"·"+RESET)

def detach_current_client(_signum=None, _frame=None):
    if not os.environ.get("TMUX"):
        return
    subprocess.run(["tmux","detach-client"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)

def render():
    sys.stdout.write("\033[?1049h\033[?25l\033[H");sys.stdout.flush()
    try:
        while True:
            proc=proc_rows(); dirs=scan_dirs(); rows=[]; bycell={}; completed_durations=[]
            names=set(proc)|set(dirs)
            for rn in names:
                rec,p=record(rn,dirs,proc); cfg=(p or {}).get("cfg") if p else readj((rec or {}).get("rd",Path())/"config.json")
                pair,ps,ts=identity_from_cfg(cfg)
                if not pair:continue
                st="WAITING"; epoch=epochs=None; macro=minf=None; elapsed=(p or {}).get("elapsed"); eta=None; best_macro=None; best_min=None
                if rec:
                    if rec["complete"]:
                        st="SUCCESS"; elapsed=rec["complete"].get("elapsed_sec"); sm=rec["summary"] or {}; best_macro=sm.get("best_val_macro_f1"); best_min=sm.get("best_val_min_class_f1"); completed_durations.append(float(elapsed or 0))
                    elif rec["error"]:st="ERROR"
                    elif p:st="RUNNING"
                    pr=rec["progress"] or {}
                    epoch=pr.get("epoch"); epochs=pr.get("epochs"); macro=pr.get("val_macro_f1"); minf=pr.get("val_min_class_f1")
                    if p and epoch and epochs:
                        step=float(pr.get("step",0) or 0); steps=float(pr.get("steps",0) or 0); frac=((float(epoch)-1)+(step/steps if steps else 0))/float(epochs)
                        if frac>0: eta=float(elapsed)*(1-frac)/frac
                od=ROOT/"osr"/rn; osrdone=readj(od/"osr_complete.json")
                osrstate="SUCCESS" if osrdone else ("RUNNING" if any((od/f).exists() for f in ["progress_PA1_from_PA2.json"]) else "-")
                rows.append({"rn":rn,"pair":pair,"p":ps,"t":ts,"status":st,"epoch":epoch,"epochs":epochs,"macro":macro if macro is not None else best_macro,"minf":minf if minf is not None else best_min,"elapsed":elapsed,"eta":eta,"osr":osrstate})
                bycell[(pair,ps,ts)]=st
            g=gpu(); frame=[B+"MTH602 FINAL ROBUSTNESS — LOCAL PIPELINE"+RESET,DIM+"Source: HOST LOCAL ONLY | GitHub/REST/GraphQL calls per refresh: 0 | Ctrl+C detaches"+RESET]
            if g:
                frame.append("   ".join(f"GPU{x[0]} {x[1]}/{x[2]} MiB {x[3]}%" for x in g))
            ctl=controller_liveness()
            if ctl:
                frame.append("   ".join(f"{x['lane']} CTRL {x['state']} pid={x['pid']} restarts={x['restarts']}" for x in ctl))
            frame.append("")
            frame.append(B+"SEED GRID  (✓ success, ▶ running, · not observed)"+RESET)
            frame.append(f"{'PAIR':<9} "+" ".join(f"p{p}t{t}" for p,t in CONDS))
            for pair in PAIRS:frame.append(f"{pair:<9} "+"   ".join(glyph(bycell.get((pair,p,t),"WAITING")) for p,t in CONDS))
            frame.append("")
            frame.append(B+f"{'CELL':<22} {'STATE':<8} {'EPOCH':>7} {'MAC-F1':>8} {'MIN-F1':>8} {'ELAPSED':>9} {'ETA':>9} {'FINISH':>7} {'OSR':>8}"+RESET)
            frame.append("-"*98)
            active=[r for r in rows if r["status"]=="RUNNING"]; terminal=sorted([r for r in rows if r["status"]!="RUNNING"],key=lambda x:x["rn"])[-12:]
            for r in active+terminal:
                ep="-" if not r["epoch"] else f"{int(r['epoch'])}/{int(r['epochs'] or 0)}"
                frame.append(f"{r['pair']} p{r['p']}t{r['t']:<11} {r['status']:<8} {ep:>7} {metric(r['macro']):>8} {metric(r['minf']):>8} {fmt(r['elapsed']):>9} {fmt(r['eta']):>9} {finish_text(r['eta']):>7} {r['osr']:>8}")
            total=50
            done=sum(1 for r in rows if r["status"]=="SUCCESS" and r["t"] in (0,1))
            med=statistics.median([x for x in completed_durations if x>0]) if any(x>0 for x in completed_durations) else None
            active_frac=0.0
            for r in active:
                if r["elapsed"] and r["eta"] is not None and (r["elapsed"]+r["eta"])>0: active_frac+=float(r["elapsed"])/(float(r["elapsed"])+float(r["eta"]))
            progress=min(1.0,(done+active_frac)/total)
            overall_eta=None
            if med is not None: overall_eta=max(0.0,(total-done-active_frac)*med/2.0)
            frame.append("-"*98)
            frame.append(f"TRAINING {done}/{total} + active={active_frac:.2f}  completion≈{progress*100:5.1f}%  median completed={fmt(med)}  campaign ETA={fmt(overall_eta)}  projected finish={finish_text(overall_eta)}")
            ps=readj(ROOT/"pipeline_state.json") or {}
            p_age=None
            try: p_age=max(0.0,time.time()-float(ps.get("epoch")))
            except Exception: pass
            p_state="ALIVE" if p_age is not None and p_age <= 5.0 else "STALE"
            frame.append(f"PIPELINE {p_state} age={fmt(p_age)} pid={ps.get('pid','-')} | CPU OSR workers {len(ps.get('active_workers',{}))}/{ps.get('max_workers','-')} | spooled {ps.get('backbones_spooled','-')} | OSR complete {ps.get('osr_complete','-')} | provider calls/refresh 0")
            width=max(40,shutil.get_terminal_size((100,40)).columns-1)
            rendered="\n".join(clip_ansi(line,width) for line in frame)
            sys.stdout.write("\033[2J\033[H"+rendered)
            sys.stdout.flush()
            time.sleep(2)
    finally:
        sys.stdout.write("\033[?25h\033[?1049l");sys.stdout.flush()

if __name__=="__main__":
    signal.signal(signal.SIGINT,detach_current_client)
    render()
