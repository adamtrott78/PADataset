import argparse
import os
import glob

from prepData import DataSetup, build_feature_cache

def main():
    ap = argparse.ArgumentParser(description="Build (or reuse) prepData feature caches.")
    ap.add_argument("--data-root", required=True, help="PADataset/data (absolute or ~)")
    ap.add_argument("--cache-root", required=True, help="Where .h5 caches live (NVMe path recommended)")
    ap.add_argument("--cache-len", type=int, default=8192, help="Feature length (e.g., 8192, 16384)")
    ap.add_argument("--normalize", action="store_true", help="Use normalize=True")
    ap.add_argument("--no-normalize", dest="normalize", action="store_false", help="Use normalize=False")
    ap.set_defaults(normalize=True)

    ap.add_argument("--source-type", required=True, help="e.g., ota")
    ap.add_argument("--source-name", required=True, help="e.g., ota_core_high_run01")
    ap.add_argument("--dataset-tag", default=None)
    ap.add_argument("--noise-tag", default=None)

    ap.add_argument("--manifest-path", default=None, help="Manifest JSON (preferred). If set, source_glob is ignored.")
    ap.add_argument("--source-glob", default=None, help="Relative glob under data-root if you insist (single pattern).")

    ap.add_argument("--force", action="store_true", help="Force rebuild cache even if .h5 exists")
    args = ap.parse_args()

    data_root = os.path.expanduser(args.data_root)
    cache_root = os.path.expanduser(args.cache_root)
    manifest_path = os.path.expanduser(args.manifest_path) if args.manifest_path else None

    setup = DataSetup(
        root=data_root,
        task="pa",
        split_mode="closed",

        normalize=bool(args.normalize),
        cache_len=int(args.cache_len),
        cache_root=cache_root,
        force_rebuild_cache=bool(args.force),

        source_type=str(args.source_type),
        source_name=str(args.source_name),
        source_glob=str(args.source_glob) if args.source_glob else None,
        manifest_path=manifest_path,

        dataset_tag=args.dataset_tag,
        noise_tag=args.noise_tag,
        cache_namespace=None,
    )

    print("Building caches with setup:")
    print(f"  data_root     = {setup.root}")
    print(f"  cache_root    = {setup.cache_root}")
    print(f"  cache_len     = {setup.cache_len}")
    print(f"  normalize     = {setup.normalize}")
    print(f"  source_type   = {setup.source_type}")
    print(f"  source_name   = {setup.source_name}")
    print(f"  manifest_path = {setup.manifest_path}")
    print(f"  source_glob   = {setup.source_glob}")
    print(f"  force_rebuild = {setup.force_rebuild_cache}")

    out_root = build_feature_cache(setup)

    h5s = sorted(glob.glob(os.path.join(out_root, "*.h5")))
    print(f"Cache build complete: {out_root}")
    print(f"Cache files present : {len(h5s)}")

if __name__ == "__main__":
    main()