#!/usr/bin/env python3
import argparse, os, shutil, time
from pathlib import Path

import h5py

def is_valid_bank_mat(path: Path, expected_rows: int) -> tuple[bool, str]:
    """Check v7.3 .mat (HDF5) has dataset X with correct first dimension."""
    try:
        with h5py.File(path, "r") as f:
            if "X" not in f:
                return False, "missing X"
            X = f["X"]
            if len(X.shape) != 3:
                return False, f"X rank={len(X.shape)}"
            if X.shape[0] != expected_rows:
                return False, f"X.shape[0]={X.shape[0]} expected={expected_rows}"
            # optional sanity: second dim should be 2
            if X.shape[1] != 2:
                return False, f"X.shape[1]={X.shape[1]} expected=2"
            return True, "ok"
    except Exception as e:
        return False, f"open/read failed: {e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Repo root, e.g. ~/adamArchives/Adam/varMax/PADataset")
    ap.add_argument("--protocol", default=None, choices=["wifi","bluetooth","zigbee"], help="If set, only this protocol")
    ap.add_argument("--bank-name", required=True, help="e.g. ota_core_high_run01 or ota_pa1_run01")
    ap.add_argument("--expected-rows", type=int, required=True, help="e.g. 500 for core banks, 2000 for pa1 banks")
    ap.add_argument("--quarantine-dir", default=None, help="Default: <repo>/results/bank_quarantine_<timestamp>")
    ap.add_argument("--delete", action="store_true", help="Delete bad files instead of moving to quarantine")
    args = ap.parse_args()

    repo = Path(os.path.expanduser(args.repo)).resolve()
    bank_name = args.bank_name
    expected_rows = args.expected_rows

    if args.quarantine_dir:
        qdir = Path(os.path.expanduser(args.quarantine_dir)).resolve()
    else:
        qdir = repo / "results" / f"bank_quarantine_{time.strftime('%Y%m%d_%H%M%S')}"
    if not args.delete:
        qdir.mkdir(parents=True, exist_ok=True)

    protos = [args.protocol] if args.protocol else ["wifi","bluetooth","zigbee"]

    bad = []
    good = 0
    scanned = 0

    for proto in protos:
        bdir = repo / "data" / proto / "ota" / bank_name
        if not bdir.is_dir():
            continue
        for p in bdir.glob(f"{bank_name}__shard_*__PA*.mat"):
            scanned += 1
            ok, why = is_valid_bank_mat(p, expected_rows)
            if ok:
                good += 1
                continue
            bad.append((p, why))

    print(f"SCAN: scanned={scanned} good={good} bad={len(bad)}")
    for p, why in bad:
        print(f"BAD: {p} | {why}")
        if args.delete:
            p.unlink(missing_ok=True)
        else:
            shutil.move(str(p), str(qdir / p.name))

    if not args.delete:
        print(f"Quarantine dir: {qdir}")

if __name__ == "__main__":
    main()