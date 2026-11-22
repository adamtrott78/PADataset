import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(path):
    return (ROOT / path).read_text()


def test_repaired_sources_parse():
    for path in [
        "evaluate.py",
        "experiments/l2o_directional_contract.py",
        "experiments/l2o_pair_cached_dqnguard.py",
    ]:
        ast.parse(_text(path), filename=path)


def test_directional_contract_restores_proven_track_a_eval_partition():
    text = _text("experiments/l2o_directional_contract.py")
    assert 'target_cfg["open_val_frac"] = 0.15' in text
    assert 'target_cfg["build_balanced_val_open"] = True' in text
    assert 'surrogate_cfg["open_val_frac"] = 0.15' in text
    assert 'surrogate_cfg["build_balanced_val_open"] = True' in text
    assert 'surrogate_cfg["require_true_val_open"] = True' in text
    assert 'surrogate_cfg["allow_val_open_fallback"] = False' in text


def test_empty_optional_loader_is_guarded():
    text = _text("evaluate.py")
    marker = "def collect_split_outputs_from_loader"
    start = text.index(marker)
    body = text[start:start + 2500]
    assert "if not all_y:" in body
    assert "return None" in body


def test_pair_cache_persists_before_directional_dqn():
    text = _text("experiments/l2o_pair_cached_dqnguard.py")
    assert "def save_split(" in text
    assert "os.replace(tmp, path)" in text
    assert "status=COLLECT_DONE" in text
    assert 'paths["val_known"]' in text
    assert 'paths["test_known"]' in text
    assert 'f"val_open_{args.pair_a}"' in text
    assert 'f"test_open_{args.pair_a}"' in text
    assert 'f"val_open_{args.pair_b}"' in text
    assert 'f"test_open_{args.pair_b}"' in text
    first_eval = text.index("rows.append(evaluate_direction(")
    assert text.index("COLLECT_DONE") < first_eval


def test_pair_cache_is_cpu_only_and_provenance_bound():
    text = _text("experiments/l2o_pair_cached_dqnguard.py")
    assert 'if args.device != "cpu":' in text
    assert "if torch.cuda.is_available():" in text
    assert '"checkpoint_sha256": sha256_file(checkpoint_path)' in text
    assert '"config_sha256": sha256_file(config_path)' in text
    assert '"target_partition_open_val_frac": 0.15' in text
    assert '"surrogate_partition_open_val_frac": 0.15' in text
