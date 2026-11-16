from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "evaluate.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _function_node(name: str) -> ast.FunctionDef:
    matches = [
        node for node in TREE.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(matches) == 1
    return matches[0]


def _load_optional_helper(strict_collector):
    node = _function_node("_collect_optional_split_outputs_from_loader")
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"collect_split_outputs_from_loader": strict_collector}
    exec(compile(module, "evaluate.py", "exec"), namespace)
    return namespace["_collect_optional_split_outputs_from_loader"]


def test_empty_optional_loader_returns_none_without_collection():
    calls = []

    def strict(*args):
        calls.append(args)
        return object()

    helper = _load_optional_helper(strict)
    assert helper(object(), [], "val_open") is None
    assert calls == []


def test_missing_optional_loader_returns_none_without_collection():
    calls = []

    def strict(*args):
        calls.append(args)
        return object()

    helper = _load_optional_helper(strict)
    assert helper(object(), None, "val_open") is None
    assert calls == []


def test_nonempty_optional_loader_delegates_to_strict_collector():
    calls = []
    sentinel = object()
    handle = object()
    loader = [object()]

    def strict(*args):
        calls.append(args)
        return sentinel

    helper = _load_optional_helper(strict)
    assert helper(handle, loader, "val_open") is sentinel
    assert calls == [(handle, loader, "val_open")]


def test_build_bundle_keeps_required_splits_strict_and_optional_splits_tolerant():
    node = _function_node("build_osr_eval_bundle")
    direct_strict = 0
    optional = 0
    for call in ast.walk(node):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
            continue
        if call.func.id == "collect_split_outputs_from_loader":
            direct_strict += 1
        elif call.func.id == "_collect_optional_split_outputs_from_loader":
            optional += 1

    assert direct_strict == 3
    assert optional == 3
