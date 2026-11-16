from __future__ import annotations

from unittest.mock import patch

import evaluate


def test_empty_optional_loader_returns_none_without_collection():
    with patch.object(evaluate, "collect_split_outputs_from_loader") as collect:
        out = evaluate._collect_optional_split_outputs_from_loader(
            object(), [], "val_open"
        )
    assert out is None
    collect.assert_not_called()


def test_missing_optional_loader_returns_none_without_collection():
    with patch.object(evaluate, "collect_split_outputs_from_loader") as collect:
        out = evaluate._collect_optional_split_outputs_from_loader(
            object(), None, "val_open"
        )
    assert out is None
    collect.assert_not_called()


def test_nonempty_optional_loader_delegates_to_strict_collector():
    handle = object()
    loader = [object()]
    sentinel = object()
    with patch.object(
        evaluate,
        "collect_split_outputs_from_loader",
        return_value=sentinel,
    ) as collect:
        out = evaluate._collect_optional_split_outputs_from_loader(
            handle, loader, "val_open"
        )
    assert out is sentinel
    collect.assert_called_once_with(handle, loader, "val_open")


def test_build_bundle_uses_optional_collection_only_for_optional_splits():
    source = evaluate.build_osr_eval_bundle.__code__.co_names
    assert "_collect_optional_split_outputs_from_loader" in source
    assert "collect_split_outputs_from_loader" in source
