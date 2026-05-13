#!/usr/bin/env python3
from pathlib import Path
import argparse
import h5py
import numpy as np

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--cache-root",
        default="_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01",
    )
    ap.add_argument("--max-files", type=int, default=None)
    args = ap.parse_args()

    root = Path(args.cache_root).expanduser()
    files = sorted(root.glob("*.h5"))
    if args.max_files is not None:
        files = files[:args.max_files]

    print("CACHE_ROOT:", root)
    print("FILES:", len(files))

    bad = []
    ok = 0

    for i, path in enumerate(files, 1):
        try:
            with h5py.File(path, "r") as f:
                keys = list(f.keys())

                if "Xfeat" in f:
                    x = f["Xfeat"]
                elif "X" in f:
                    x = f["X"]
                else:
                    raise KeyError(f"No Xfeat or X key. keys={keys}")

                shape = x.shape
                if len(shape) < 2:
                    raise ValueError(f"Unexpected feature shape: {shape}")

                # Read first and last sample-ish slices lightly.
                first = np.array(x[0])
                last = np.array(x[-1])

                if not np.isfinite(first).all():
                    raise ValueError("Non-finite values in first item")
                if not np.isfinite(last).all():
                    raise ValueError("Non-finite values in last item")

                ok += 1
                if i % 25 == 0 or i == len(files):
                    print(f"OK {i}/{len(files)}")

        except Exception as e:
            bad.append((str(path), repr(e)))
            print(f"BAD {path}: {e!r}")

    print()
    print("SUMMARY")
    print("OK:", ok)
    print("BAD:", len(bad))

    if bad:
        print()
        print("BAD FILES:")
        for p, e in bad:
            print(p)
            print("  ", e)
        raise SystemExit(2)

if __name__ == "__main__":
    main()
