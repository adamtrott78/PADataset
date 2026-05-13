import os
import glob
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import h5py
import numpy as np
import torch
import torch.nn.functional as F
from scipy.fft import fft
from scipy.fftpack import dct
from torch.utils.data import Dataset, Subset, DataLoader


PA_NAMES = ["PA1", "PA2", "PA3", "PA4", "PA8"]
PROTO_NAMES = ["wifi", "bluetooth", "zigbee"]

PA_NAME_TO_IDX = {name: i for i, name in enumerate(PA_NAMES)}
PROTO_NAME_TO_IDX = {name: i for i, name in enumerate(PROTO_NAMES)}

OPTIONAL_SAMPLE_META_KEYS = [
    "window_id",
    "pair_id",
    "segment_id",
    "record_id",
    "shard_id",
    "session_id",
    "tape_id",
    "snr_level",
    "noise_level",
    "source_id",
]


# -----------------------------
# setup object
# -----------------------------
@dataclass
class DataSetup:
    root: str
    task: str = "pa"                 # "pa" or "joint"
    split_mode: str = "closed"       # "closed" or "open_pa"
    unknown_pas: Tuple[Union[str, int], ...] = field(default_factory=tuple)

    normalize: bool = True
    cache_len: Optional[int] = 8192
    cache_root: Optional[str] = None
    force_rebuild_cache: bool = False
    skip_cache_build: bool = False

    train_frac: float = 0.70
    val_frac: float = 0.15
    seed: int = 0

    protocols: Optional[Tuple[Union[str, int], ...]] = None
    pas: Optional[Tuple[Union[str, int], ...]] = None

    return_metadata: bool = False

    # new source-layer controls
    source_type: str = "digital"             # "digital", "ota", "any", or custom
    source_name: Optional[str] = "pilot_noisy_torch"
    source_glob: Optional[str] = None
    manifest_path: Optional[str] = None

    dataset_tag: Optional[str] = None
    noise_tag: Optional[str] = None
    cache_namespace: Optional[str] = None

    # new open-set validation controls
    open_val_frac: Optional[float] = None    # defaults to val_frac when None
    build_balanced_val_open: bool = True
    manifold_balance_seed: Optional[int] = None


@dataclass
class RawSourceRecord:
    path: str
    protocol_name: str
    source_type: str
    source_name: str
    dataset_tag: Optional[str] = None
    noise_tag: Optional[str] = None


# -----------------------------
# helpers
# -----------------------------
def _coerce_name_list(
    values: Optional[Union[str, int, Sequence[Union[str, int]]]],
    valid_name_to_idx: Dict[str, int],
    field_name: str,
) -> Optional[List[int]]:
    if values is None:
        return None

    if isinstance(values, (str, int, np.integer)):
        values = [values]

    out = []
    for v in values:
        if isinstance(v, str):
            if v not in valid_name_to_idx:
                raise ValueError(f"Unknown {field_name} name: {v}")
            out.append(valid_name_to_idx[v])
        else:
            iv = int(v)
            if iv < 0 or iv >= len(valid_name_to_idx):
                raise ValueError(f"Invalid {field_name} index: {iv}")
            out.append(iv)

    return sorted(set(out))


def joint_label(proto_idx: int, pa_idx: int) -> int:
    return int(proto_idx) * len(PA_NAMES) + int(pa_idx)


def get_joint_class_names() -> List[str]:
    return [f"{proto}_{pa}" for proto in PROTO_NAMES for pa in PA_NAMES]


def _slugify(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    bad = '<>:"/\\|?* '
    out = "".join("_" if c in bad else c for c in s)
    return out


def _infer_proto_name_from_path(path: str) -> str:
    parts = os.path.normpath(path).split(os.sep)
    for proto in PROTO_NAMES:
        if proto in parts:
            return proto
    raise ValueError(f"Could not infer protocol name from path: {path}")


def _is_default_source_signature(setup: DataSetup) -> bool:
    return (
        setup.source_type == "digital"
        and setup.source_name == "pilot_noisy_torch"
        and setup.source_glob is None
        and setup.manifest_path is None
        and setup.dataset_tag is None
        and setup.noise_tag is None
        and setup.cache_namespace is None
    )


def _source_signature(setup: DataSetup) -> Optional[str]:
    if _is_default_source_signature(setup):
        return None

    parts = [
        _slugify(setup.source_type) or "unknown_source_type",
        _slugify(setup.source_name) or "unknown_source_name",
        _slugify(setup.dataset_tag),
        _slugify(setup.noise_tag),
        _slugify(setup.cache_namespace),
    ]
    parts = [p for p in parts if p is not None]
    return "__".join(parts) if parts else None


def _default_cache_root(root: str, cache_len: Optional[int], normalize: bool, setup: Optional[DataSetup] = None) -> str:
    suffix = "norm" if normalize else "raw"

    base = (
        os.path.join(os.path.expanduser(root), "_feature_cache_full", suffix)
        if cache_len is None
        else os.path.join(os.path.expanduser(root), f"_feature_cache_len{cache_len}", suffix)
    )

    if setup is None:
        return base

    sig = _source_signature(setup)
    if sig is None:
        return base

    return os.path.join(base, sig)


def _infer_x_layout(xshape: Tuple[int, int, int]) -> Tuple[int, int, int]:
    dims = list(xshape)
    if len(dims) != 3:
        raise ValueError(f"Expected X to be 3D, got shape {xshape}")

    if 2 not in dims:
        raise ValueError(f"Could not find I/Q channel dimension of size 2 in shape {xshape}")

    ch_axis = dims.index(2)
    remaining_axes = [a for a in range(3) if a != ch_axis]
    remaining_sizes = [dims[a] for a in remaining_axes]

    sample_axis = remaining_axes[int(np.argmin(remaining_sizes))]
    time_axis = [a for a in remaining_axes if a != sample_axis][0]

    return ch_axis, sample_axis, time_axis


def _load_iq_sample_from_h5(
    Xds: h5py.Dataset,
    local_idx: int,
    ch_axis: int,
    sample_axis: int,
    time_axis: int,
) -> np.ndarray:
    if sample_axis == 0:
        x = np.array(Xds[local_idx, :, :], dtype=np.float32)
        orig_remaining = [1, 2]
    elif sample_axis == 1:
        x = np.array(Xds[:, local_idx, :], dtype=np.float32)
        orig_remaining = [0, 2]
    else:
        x = np.array(Xds[:, :, local_idx], dtype=np.float32)
        orig_remaining = [0, 1]

    ch_pos = orig_remaining.index(ch_axis)
    time_pos = orig_remaining.index(time_axis)
    x = np.transpose(x, (ch_pos, time_pos))

    if x.shape[0] != 2:
        raise ValueError(f"Expected IQ shape [2, W], got {x.shape}")

    return x


def compute_feature_stack(iq: np.ndarray, normalize: bool = True) -> np.ndarray:
    """
    iq: [2, W]
    returns [8, W] = [IQ(2), FFT(2), DCT(2), POLAR(2)]
    """
    if iq.ndim != 2 or iq.shape[0] != 2:
        raise ValueError(f"Expected iq shape [2, W], got {iq.shape}")

    xt = iq.astype(np.float32, copy=True)
    complex_signal = xt[0] + 1j * xt[1]

    xf_complex = fft(complex_signal)
    xf = np.stack([xf_complex.real, xf_complex.imag], axis=0).astype(np.float32)

    xc0 = dct(xt[0], type=2, norm="ortho")
    xc1 = dct(xt[1], type=2, norm="ortho")
    xc = np.stack([xc0, xc1], axis=0).astype(np.float32)

    magnitude = np.abs(complex_signal).astype(np.float32)
    phase = np.angle(complex_signal).astype(np.float32)
    polar = np.stack([magnitude, phase], axis=0).astype(np.float32)

    if normalize:
        xt = np.tanh(xt)
        xf = np.tanh(xf)
        xc = np.tanh(xc)
        polar[0] = np.tanh(polar[0])
        polar[1] = np.sin(polar[1])

    combined = np.vstack((xt, xf, xc, polar)).astype(np.float32)
    return combined


def reduce_feature_length(x: np.ndarray, out_len: Optional[int]) -> np.ndarray:
    if out_len is None or x.shape[-1] == out_len:
        return x.astype(np.float32, copy=False)

    xt = torch.from_numpy(x[None, ...])
    with torch.no_grad():
        yt = F.adaptive_avg_pool1d(xt, out_len)
    return yt[0].cpu().numpy().astype(np.float32, copy=False)


def _load_manifest_records(setup: DataSetup) -> List[RawSourceRecord]:
    if setup.manifest_path is None:
        return []

    manifest_path = os.path.expanduser(setup.manifest_path)
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("Manifest JSON must be a list of source records")

    records: List[RawSourceRecord] = []
    for row in payload:
        path = os.path.expanduser(row["path"])
        protocol_name = row.get("protocol_name") or _infer_proto_name_from_path(path)
        source_type = row.get("source_type", setup.source_type)
        source_name = row.get("source_name", setup.source_name or "unknown_source")
        dataset_tag = row.get("dataset_tag", setup.dataset_tag)
        noise_tag = row.get("noise_tag", setup.noise_tag)

        records.append(
            RawSourceRecord(
                path=path,
                protocol_name=protocol_name,
                source_type=source_type,
                source_name=source_name,
                dataset_tag=dataset_tag,
                noise_tag=noise_tag,
            )
        )

    return records


def discover_raw_sources(setup: DataSetup) -> List[RawSourceRecord]:
    root = os.path.expanduser(setup.root)

    if setup.manifest_path is not None:
        records = _load_manifest_records(setup)
        if not records:
            raise FileNotFoundError("Manifest contained no usable source records")
        return sorted(records, key=lambda r: r.path)

    if setup.source_glob is not None:
        pattern = setup.source_glob
        if not os.path.isabs(pattern):
            pattern = os.path.join(root, pattern)
    else:
        source_name = setup.source_name or "*"
        if setup.source_type == "any":
            pattern = os.path.join(root, "*", "*", source_name, "*.mat")
        else:
            pattern = os.path.join(root, "*", setup.source_type, source_name, "*.mat")

    raw_files = sorted(glob.glob(pattern))
    if not raw_files:
        raise FileNotFoundError(f"No raw source files found with pattern: {pattern}")

    records = []
    for raw_path in raw_files:
        protocol_name = _infer_proto_name_from_path(raw_path)
        records.append(
            RawSourceRecord(
                path=raw_path,
                protocol_name=protocol_name,
                source_type=setup.source_type,
                source_name=setup.source_name or "unknown_source",
                dataset_tag=setup.dataset_tag,
                noise_tag=setup.noise_tag,
            )
        )

    return records


def _cache_file_name(rec: RawSourceRecord) -> str:
    parts = [
        _slugify(rec.protocol_name) or "unknown_proto",
        _slugify(rec.source_type) or "unknown_source_type",
        _slugify(rec.source_name) or "unknown_source_name",
        _slugify(rec.dataset_tag),
        _slugify(rec.noise_tag),
        os.path.basename(rec.path).replace(".mat", ".h5"),
    ]
    parts = [p for p in parts if p is not None]
    return "__".join(parts)


# -----------------------------
# precompute/cache
# -----------------------------
def build_feature_cache(setup: DataSetup) -> str:
    root = os.path.expanduser(setup.root)
    cache_root = setup.cache_root or _default_cache_root(root, setup.cache_len, setup.normalize, setup)
    os.makedirs(cache_root, exist_ok=True)

    raw_records = discover_raw_sources(setup)

    for rec in raw_records:
        cache_path = os.path.join(cache_root, _cache_file_name(rec))

        if os.path.isfile(cache_path) and not setup.force_rebuild_cache:
            continue

        with h5py.File(rec.path, "r") as fin:
            if "X" not in fin or "y" not in fin or "proto" not in fin:
                raise KeyError(f"{rec.path} is missing one of required keys: X, y, proto")

            Xds = fin["X"]
            y = np.array(fin["y"]).reshape(-1).astype(np.int64)
            proto = np.array(fin["proto"]).reshape(-1).astype(np.int64)

            xshape = tuple(Xds.shape)
            ch_axis, sample_axis, time_axis = _infer_x_layout(xshape)
            n_samples = xshape[sample_axis]

            if n_samples != len(y) or n_samples != len(proto):
                raise ValueError(
                    f"Mismatch in {rec.path}: X.shape={xshape}, len(y)={len(y)}, len(proto)={len(proto)}"
                )

            first_iq = _load_iq_sample_from_h5(Xds, 0, ch_axis, sample_axis, time_axis)
            first_feat = reduce_feature_length(
                compute_feature_stack(first_iq, normalize=setup.normalize),
                setup.cache_len,
            )
            out_len = first_feat.shape[-1]

            if os.path.isfile(cache_path):
                os.remove(cache_path)

            with h5py.File(cache_path, "w") as fout:
                fout.create_dataset(
                    "Xfeat",
                    shape=(n_samples, 8, out_len),
                    dtype="float32",
                    chunks=(1, 8, out_len),
                )
                fout.create_dataset("y_pa", data=y.astype(np.int64))
                fout.create_dataset("proto", data=proto.astype(np.int64))
                fout.create_dataset(
                    "y_joint",
                    data=np.array([joint_label(int(proto[i]), int(y[i])) for i in range(n_samples)], dtype=np.int64),
                )

                # file-level provenance
                fout.attrs["source_path"] = rec.path
                fout.attrs["protocol_name"] = rec.protocol_name
                fout.attrs["source_type"] = rec.source_type
                fout.attrs["source_name"] = rec.source_name
                fout.attrs["dataset_tag"] = "" if rec.dataset_tag is None else str(rec.dataset_tag)
                fout.attrs["noise_tag"] = "" if rec.noise_tag is None else str(rec.noise_tag)
                fout.attrs["normalize"] = int(setup.normalize)
                fout.attrs["cache_len"] = -1 if setup.cache_len is None else int(setup.cache_len)

                for key in OPTIONAL_SAMPLE_META_KEYS:
                    if key in fin:
                        arr = np.array(fin[key]).reshape(-1)
                        if len(arr) == n_samples:
                            fout.create_dataset(key, data=arr)

                fout["Xfeat"][0] = first_feat

                for i in range(1, n_samples):
                    iq = _load_iq_sample_from_h5(Xds, i, ch_axis, sample_axis, time_axis)
                    feat = compute_feature_stack(iq, normalize=setup.normalize)
                    feat = reduce_feature_length(feat, setup.cache_len)
                    fout["Xfeat"][i] = feat

    return cache_root


# -----------------------------
# cached dataset
# -----------------------------
class CachedFeatureDataset(Dataset):
    def __init__(self, setup: DataSetup):
        if setup.task not in {"pa", "joint"}:
            raise ValueError("setup.task must be 'pa' or 'joint'")

        self.setup = setup
        self.root = os.path.expanduser(setup.root)
        self.task = setup.task
        self.return_metadata = setup.return_metadata

        self.protocol_filter = _coerce_name_list(setup.protocols, PROTO_NAME_TO_IDX, "protocol")
        self.pa_filter = _coerce_name_list(setup.pas, PA_NAME_TO_IDX, "PA")

        self.cache_root = setup.cache_root or _default_cache_root(self.root, setup.cache_len, setup.normalize, setup)
        if not os.path.isdir(self.cache_root):
            raise FileNotFoundError(
                f"Cache root {self.cache_root} does not exist. Run build_feature_cache(setup) first."
            )

        self.files = sorted(glob.glob(os.path.join(self.cache_root, "*.h5")))
        if not self.files:
            raise FileNotFoundError(f"No cache files found in {self.cache_root}")

        self.index: List[Dict[str, Any]] = []
        self._cache: Dict[str, h5py.File] = {}
        self._build_index()

    @property
    def class_names(self) -> List[str]:
        if self.task == "pa":
            return list(PA_NAMES)
        return get_joint_class_names()

    def _build_index(self):
        for path in self.files:
            with h5py.File(path, "r") as f:
                Xshape = tuple(f["Xfeat"].shape)
                y_pa = np.array(f["y_pa"]).reshape(-1).astype(np.int64)
                proto = np.array(f["proto"]).reshape(-1).astype(np.int64)
                y_joint = np.array(f["y_joint"]).reshape(-1).astype(np.int64)

                n_samples = Xshape[0]
                if n_samples != len(y_pa) or n_samples != len(proto) or n_samples != len(y_joint):
                    raise ValueError(f"Cache file mismatch in {path}")

                source_type = f.attrs.get("source_type", "")
                source_name = f.attrs.get("source_name", "")
                dataset_tag = f.attrs.get("dataset_tag", "")
                noise_tag = f.attrs.get("noise_tag", "")
                protocol_name_attr = f.attrs.get("protocol_name", "")

                for i in range(n_samples):
                    pa_label = int(y_pa[i])
                    proto_label = int(proto[i])

                    if self.protocol_filter is not None and proto_label not in self.protocol_filter:
                        continue
                    if self.pa_filter is not None and pa_label not in self.pa_filter:
                        continue

                    self.index.append({
                        "path": path,
                        "local_idx": i,
                        "proto": proto_label,
                        "proto_name": PROTO_NAMES[proto_label],
                        "pa": pa_label,
                        "pa_name": PA_NAMES[pa_label],
                        "label_pa": pa_label,
                        "label_joint": int(y_joint[i]),
                        "label": pa_label if self.task == "pa" else int(y_joint[i]),
                        "source_type": str(source_type),
                        "source_name": str(source_name),
                        "dataset_tag": str(dataset_tag) if dataset_tag != "" else None,
                        "noise_tag": str(noise_tag) if noise_tag != "" else None,
                        "protocol_name_attr": str(protocol_name_attr),
                    })

        if not self.index:
            raise ValueError("No samples remained after applying dataset filters.")

    def _get_file(self, path: str) -> h5py.File:
        if path not in self._cache:
            self._cache[path] = h5py.File(path, "r")
        return self._cache[path]

    def close(self):
        for f in self._cache.values():
            try:
                f.close()
            except Exception:
                pass
        self._cache = {}

    def __del__(self):
        self.close()

    def __len__(self):
        return len(self.index)

    def __getitem__(self, idx: int):
        rec = self.index[idx]
        f = self._get_file(rec["path"])

        x = np.array(f["Xfeat"][rec["local_idx"]], dtype=np.float32)
        y = int(rec["label"])

        x_t = torch.from_numpy(x)
        y_t = torch.tensor(y, dtype=torch.long)

        if self.return_metadata:
            meta = {
                "dataset_index": idx,
                "path": rec["path"],
                "local_idx": rec["local_idx"],
                "proto": rec["proto"],
                "proto_name": rec["proto_name"],
                "pa": rec["pa"],
                "pa_name": rec["pa_name"],
                "label_pa": rec["label_pa"],
                "label_joint": rec["label_joint"],
                "label": rec["label"],
                "source_type": rec["source_type"],
                "source_name": rec["source_name"],
                "dataset_tag": rec["dataset_tag"],
                "noise_tag": rec["noise_tag"],
            }

            for key in OPTIONAL_SAMPLE_META_KEYS:
                if key in f:
                    value = f[key][rec["local_idx"]]
                    if isinstance(value, bytes):
                        value = value.decode()
                    elif hasattr(value, "item"):
                        try:
                            value = value.item()
                        except Exception:
                            pass
                    meta[key] = value

            return x_t, y_t, meta

        return x_t, y_t


# -----------------------------
# splitting
# -----------------------------
def stratified_split_indices(
    dataset: Dataset,
    labels: Optional[Sequence[int]] = None,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    seed: int = 0,
) -> Tuple[List[int], List[int], List[int]]:
    if train_frac <= 0 or val_frac < 0 or (train_frac + val_frac) >= 1.0:
        raise ValueError("Need 0 < train_frac, 0 <= val_frac, and train_frac + val_frac < 1")

    rng = np.random.default_rng(seed)

    if labels is None:
        labels = [rec["label"] for rec in dataset.index]

    labels = np.asarray(labels)
    train_idx, val_idx, test_idx = [], [], []

    for lab in np.unique(labels):
        idx = np.where(labels == lab)[0]
        rng.shuffle(idx)

        n = len(idx)
        n_train = int(train_frac * n)
        n_val = int(val_frac * n)

        train_idx.extend(idx[:n_train].tolist())
        val_idx.extend(idx[n_train:n_train + n_val].tolist())
        test_idx.extend(idx[n_train + n_val:].tolist())

    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    rng.shuffle(test_idx)

    return train_idx, val_idx, test_idx


class RemappedSubset(Dataset):
    def __init__(
        self,
        subset: Subset,
        known_label_map: Dict[int, int],
        open_label: Optional[int] = None,
    ):
        self.subset = subset
        self.known_label_map = dict(known_label_map)
        self.open_label = open_label

    def __len__(self):
        return len(self.subset)

    def __getitem__(self, idx):
        out = self.subset[idx]

        if isinstance(out, tuple) and len(out) == 3:
            x, y, meta = out
            old_y = int(y.item())
            if old_y in self.known_label_map:
                new_y = self.known_label_map[old_y]
            else:
                if self.open_label is None:
                    raise ValueError(f"Label {old_y} not in known_label_map.")
                new_y = self.open_label
            return x, torch.tensor(new_y, dtype=torch.long), meta

        x, y = out
        old_y = int(y.item())
        if old_y in self.known_label_map:
            new_y = self.known_label_map[old_y]
        else:
            if self.open_label is None:
                raise ValueError(f"Label {old_y} not in known_label_map.")
            new_y = self.open_label
        return x, torch.tensor(new_y, dtype=torch.long)


def _stratified_take_indices(
    indices: Sequence[int],
    labels: Sequence[int],
    target_n: int,
    seed: int,
) -> List[int]:
    """
    Take a stratified subset of `indices` with total size `target_n`.
    """
    indices = np.asarray(indices, dtype=int)
    labels = np.asarray(labels)

    if target_n <= 0:
        return []
    if target_n >= len(indices):
        return indices.tolist()

    rng = np.random.default_rng(seed)

    unique_labels = np.unique(labels)
    by_class = {}
    for cls in unique_labels:
        cls_idx = indices[labels == cls].copy()
        rng.shuffle(cls_idx)
        by_class[int(cls)] = cls_idx

    total = len(indices)
    raw_targets = {}
    floor_targets = {}
    for cls, cls_idx in by_class.items():
        raw = target_n * (len(cls_idx) / total)
        raw_targets[cls] = raw
        floor_targets[cls] = min(len(cls_idx), int(np.floor(raw)))

    taken = sum(floor_targets.values())
    remainder = target_n - taken

    frac_order = sorted(
        by_class.keys(),
        key=lambda c: (raw_targets[c] - floor_targets[c]),
        reverse=True,
    )

    for cls in frac_order:
        if remainder <= 0:
            break
        if floor_targets[cls] < len(by_class[cls]):
            floor_targets[cls] += 1
            remainder -= 1

    out = []
    for cls, cls_idx in by_class.items():
        out.extend(cls_idx[:floor_targets[cls]].tolist())

    rng.shuffle(out)
    return out


def _split_open_indices_by_pa(
    dataset: CachedFeatureDataset,
    unknown_pa_idx: List[int],
    open_val_frac: float,
    seed: int,
) -> Tuple[List[int], List[int]]:
    """
    Split withheld/open PA samples into val_open and test_open.
    Stratifies across withheld PA labels.
    """
    rng = np.random.default_rng(seed)

    by_pa: Dict[int, List[int]] = {pa: [] for pa in unknown_pa_idx}
    for i, rec in enumerate(dataset.index):
        pa = int(rec["pa"])
        if pa in unknown_pa_idx:
            by_pa[pa].append(i)

    val_open_idx, test_open_idx = [], []

    for pa in unknown_pa_idx:
        idx = np.array(by_pa[pa], dtype=int)
        rng.shuffle(idx)

        n = len(idx)
        n_val_open = int(open_val_frac * n)

        val_open_idx.extend(idx[:n_val_open].tolist())
        test_open_idx.extend(idx[n_val_open:].tolist())

    rng.shuffle(val_open_idx)
    rng.shuffle(test_open_idx)
    return val_open_idx, test_open_idx


def make_pa_open_set_splits(
    dataset: CachedFeatureDataset,
    unknown_pas: Union[str, int, Sequence[Union[str, int]]],
    train_frac: float = 0.70,
    val_frac: float = 0.15,
    open_val_frac: Optional[float] = None,
    seed: int = 0,
    open_label: int = -1,
    build_balanced_val_open: bool = True,
    manifold_balance_seed: Optional[int] = None,
) -> Dict[str, Any]:
    if dataset.task != "pa":
        raise ValueError("make_pa_open_set_splits requires dataset.task == 'pa'")

    unknown_pa_idx = _coerce_name_list(unknown_pas, PA_NAME_TO_IDX, "PA")
    if unknown_pa_idx is None or len(unknown_pa_idx) == 0:
        raise ValueError("unknown_pas must specify at least one PA")

    open_val_frac = val_frac if open_val_frac is None else float(open_val_frac)
    if open_val_frac < 0 or open_val_frac >= 1.0:
        raise ValueError("open_val_frac must satisfy 0 <= open_val_frac < 1")

    # Only use PA classes that are actually present after dataset-level filters
    # such as setup.pas/protocols/source filters. Otherwise catalog paper sets
    # that intentionally exclude a PA can create output classes with zero support.
    present_pa_idx = sorted({int(rec["pa"]) for rec in dataset.index})
    known_pa_idx = [i for i in present_pa_idx if i not in unknown_pa_idx]

    missing_unknown = [i for i in unknown_pa_idx if i not in present_pa_idx]
    if missing_unknown:
        raise ValueError(
            "Unknown PA(s) are not present after dataset filters: "
            f"{[PA_NAMES[i] for i in missing_unknown]} | "
            f"present={[PA_NAMES[i] for i in present_pa_idx]}"
        )

    if len(known_pa_idx) == 0:
        raise ValueError("All present PAs withheld; no known classes remain.")

    rng = np.random.default_rng(seed)

    known_by_pa: Dict[int, List[int]] = {pa: [] for pa in known_pa_idx}

    for i, rec in enumerate(dataset.index):
        pa = int(rec["pa"])
        if pa in known_pa_idx:
            known_by_pa[pa].append(i)

    train_idx, val_idx, test_known_idx = [], [], []

    for pa in known_pa_idx:
        idx = np.array(known_by_pa[pa], dtype=int)
        rng.shuffle(idx)

        n = len(idx)
        n_train = int(train_frac * n)
        n_val = int(val_frac * n)

        train_idx.extend(idx[:n_train].tolist())
        val_idx.extend(idx[n_train:n_train + n_val].tolist())
        test_known_idx.extend(idx[n_train + n_val:].tolist())

    rng.shuffle(train_idx)
    rng.shuffle(val_idx)
    rng.shuffle(test_known_idx)

    val_open_idx, test_open_idx = _split_open_indices_by_pa(
        dataset=dataset,
        unknown_pa_idx=unknown_pa_idx,
        open_val_frac=open_val_frac,
        seed=seed,
    )

    known_label_map = {old_pa: new_lab for new_lab, old_pa in enumerate(known_pa_idx)}

    # full splits
    train_raw = Subset(dataset, train_idx)
    val_raw = Subset(dataset, val_idx)
    test_known_raw = Subset(dataset, test_known_idx)
    val_open_raw = Subset(dataset, val_open_idx)
    test_open_raw = Subset(dataset, test_open_idx)

    train_ds = RemappedSubset(train_raw, known_label_map, open_label=None)
    val_ds = RemappedSubset(val_raw, known_label_map, open_label=None)
    test_known_ds = RemappedSubset(test_known_raw, known_label_map, open_label=None)
    val_open_ds = RemappedSubset(val_open_raw, known_label_map, open_label=open_label)
    test_open_ds = RemappedSubset(test_open_raw, known_label_map, open_label=open_label)

    # balanced manifold validation splits
    val_known_balanced_ds = None
    val_open_balanced_ds = None
    val_known_balanced_raw = None
    val_open_balanced_raw = None
    n_val_known_balanced = None
    n_val_open_balanced = None

    if build_balanced_val_open and len(val_idx) > 0 and len(val_open_idx) > 0:
        balance_seed = seed if manifold_balance_seed is None else int(manifold_balance_seed)
        target_n = min(len(val_idx), len(val_open_idx))

        known_labels_for_balance = np.array([dataset.index[i]["pa"] for i in val_idx], dtype=int)
        open_labels_for_balance = np.array([dataset.index[i]["pa"] for i in val_open_idx], dtype=int)

        val_known_balanced_idx = _stratified_take_indices(
            indices=val_idx,
            labels=known_labels_for_balance,
            target_n=target_n,
            seed=balance_seed,
        )
        val_open_balanced_idx = _stratified_take_indices(
            indices=val_open_idx,
            labels=open_labels_for_balance,
            target_n=target_n,
            seed=balance_seed + 1,
        )

        val_known_balanced_raw = Subset(dataset, val_known_balanced_idx)
        val_open_balanced_raw = Subset(dataset, val_open_balanced_idx)

        val_known_balanced_ds = RemappedSubset(
            val_known_balanced_raw,
            known_label_map,
            open_label=None,
        )
        val_open_balanced_ds = RemappedSubset(
            val_open_balanced_raw,
            known_label_map,
            open_label=open_label,
        )

        n_val_known_balanced = len(val_known_balanced_idx)
        n_val_open_balanced = len(val_open_balanced_idx)

    meta = {
        "known_pa_idx": known_pa_idx,
        "unknown_pa_idx": unknown_pa_idx,
        "known_pa_names": [PA_NAMES[i] for i in known_pa_idx],
        "unknown_pa_names": [PA_NAMES[i] for i in unknown_pa_idx],
        "known_label_map": known_label_map,
        "open_label": open_label,
        "num_classes": len(known_pa_idx),
        "class_names": [PA_NAMES[i] for i in known_pa_idx],

        "n_train": len(train_idx),
        "n_val": len(val_idx),
        "n_test_known": len(test_known_idx),
        "n_val_open": len(val_open_idx),
        "n_test_open": len(test_open_idx),
        "n_val_known_balanced": n_val_known_balanced,
        "n_val_open_balanced": n_val_open_balanced,

        "task": dataset.setup.task,
        "split_mode": dataset.setup.split_mode,
        "source_type": dataset.setup.source_type,
        "source_name": dataset.setup.source_name,
        "dataset_tag": dataset.setup.dataset_tag,
        "noise_tag": dataset.setup.noise_tag,
    }

    return {
        "train": train_ds,
        "val": val_ds,
        "test_known": test_known_ds,
        "val_open": val_open_ds,
        "test_open": test_open_ds,

        "train_raw": train_raw,
        "val_raw": val_raw,
        "test_known_raw": test_known_raw,
        "val_open_raw": val_open_raw,
        "test_open_raw": test_open_raw,

        "val_known_balanced": val_known_balanced_ds,
        "val_open_balanced": val_open_balanced_ds,
        "val_known_balanced_raw": val_known_balanced_raw,
        "val_open_balanced_raw": val_open_balanced_raw,

        "meta": meta,
    }


# -----------------------------
# top-level build entrypoint
# -----------------------------
def build_data_from_setup(
    setup: DataSetup,
    batch_size: int = 2,
    num_workers: int = 0,
    pin_memory: bool = True,
) -> Dict[str, Any]:
    if getattr(setup, "skip_cache_build", False):
        print(
            f"DATA_STAGE | cache_only=true | cache_root={setup.cache_root}",
            flush=True,
        )
    else:
        build_feature_cache(setup)

    ds = CachedFeatureDataset(setup)

    out: Dict[str, Any] = {"dataset": ds, "setup": setup}

    if setup.split_mode == "closed":
        train_idx, val_idx, test_idx = stratified_split_indices(
            ds,
            train_frac=setup.train_frac,
            val_frac=setup.val_frac,
            seed=setup.seed,
        )

        train_ds = Subset(ds, train_idx)
        val_ds = Subset(ds, val_idx)
        test_ds = Subset(ds, test_idx)

        meta = {
            "num_classes": len(ds.class_names),
            "class_names": ds.class_names,
            "n_train": len(train_ds),
            "n_val": len(val_ds),
            "n_test": len(test_ds),
            "task": setup.task,
            "split_mode": setup.split_mode,
            "source_type": setup.source_type,
            "source_name": setup.source_name,
            "dataset_tag": setup.dataset_tag,
            "noise_tag": setup.noise_tag,
        }

        out.update({
            "train_ds": train_ds,
            "val_ds": val_ds,
            "test_ds": test_ds,
            "train_loader": DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=pin_memory),
            "val_loader": DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory),
            "test_loader": DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory),
            "meta": meta,
        })
        return out

    if setup.split_mode == "open_pa":
        if setup.task != "pa":
            raise ValueError("open_pa split_mode currently requires task='pa'")

        split = make_pa_open_set_splits(
            ds,
            unknown_pas=setup.unknown_pas,
            train_frac=setup.train_frac,
            val_frac=setup.val_frac,
            open_val_frac=setup.open_val_frac,
            seed=setup.seed,
            build_balanced_val_open=setup.build_balanced_val_open,
            manifold_balance_seed=setup.manifold_balance_seed,
        )

        out.update({
            "train_ds": split["train"],
            "val_ds": split["val"],
            "test_known_ds": split["test_known"],
            "val_open_ds": split["val_open"],
            "test_open_ds": split["test_open"],

            "val_known_balanced_ds": split["val_known_balanced"],
            "val_open_balanced_ds": split["val_open_balanced"],

            "train_loader": DataLoader(split["train"], batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=pin_memory),
            "val_loader": DataLoader(split["val"], batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory),
            "test_known_loader": DataLoader(split["test_known"], batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory),
            "val_open_loader": DataLoader(split["val_open"], batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory),
            "test_open_loader": DataLoader(split["test_open"], batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory),

            "val_known_balanced_loader": None if split["val_known_balanced"] is None else DataLoader(
                split["val_known_balanced"], batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory
            ),
            "val_open_balanced_loader": None if split["val_open_balanced"] is None else DataLoader(
                split["val_open_balanced"], batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory
            ),

            "meta": split["meta"],
        })
        return out

    raise ValueError("setup.split_mode must be 'closed' or 'open_pa'")