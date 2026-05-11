import argparse
import json
import os
import glob
from collections import Counter

VALID_PROTOS = {"wifi", "bluetooth", "zigbee"}

def main():
    ap = argparse.ArgumentParser(description="Build a prepData manifest JSON for a subset of protocols.")
    ap.add_argument("--data-root", required=True, help="PADataset/data (absolute or ~)")
    ap.add_argument("--source-type", required=True, help="e.g., ota or digital")
    ap.add_argument("--source-name", required=True, help="e.g., ota_core_high_run01 or ota_pa1_run01")
    ap.add_argument("--protocols", nargs="+", required=True, help="Protocols to include (wifi bluetooth zigbee)")
    ap.add_argument("--out", required=True, help="Output manifest JSON path")
    ap.add_argument("--dataset-tag", default=None, help="Optional dataset_tag stored in manifest rows")
    ap.add_argument("--noise-tag", default=None, help="Optional noise_tag stored in manifest rows")
    ap.add_argument("--require-nonempty", action="store_true", help="Error if any selected protocol has 0 files")
    args = ap.parse_args()

    data_root = os.path.expanduser(args.data_root)
    source_type = str(args.source_type)
    source_name = str(args.source_name)
    out_path = os.path.expanduser(args.out)

    protos = [str(p) for p in args.protocols]
    bad = [p for p in protos if p not in VALID_PROTOS]
    if bad:
        raise ValueError(f"Invalid protocols: {bad}. Valid: {sorted(VALID_PROTOS)}")

    records = []
    counts = Counter()

    for proto in protos:
        pat = os.path.join(data_root, proto, source_type, source_name, "*.mat")
        files = sorted(glob.glob(pat))
        counts[proto] = len(files)

        if args.require_nonempty and len(files) == 0:
            raise FileNotFoundError(f"No files found for {proto} with pattern: {pat}")

        for fp in files:
            records.append({
                "path": fp,  # absolute path is safest
                "protocol_name": proto,
                "source_type": source_type,
                "source_name": source_name,
                "dataset_tag": args.dataset_tag,
                "noise_tag": args.noise_tag,
            })

    records = sorted(records, key=lambda r: r["path"])
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"Manifest written: {out_path}")
    for proto in protos:
        print(f"  {proto:10s}: {counts[proto]} files")
    print(f"  total     : {len(records)} files")

if __name__ == "__main__":
    main()