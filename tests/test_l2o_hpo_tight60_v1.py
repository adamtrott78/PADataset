import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "manifests" / "configs" / "l2o_hpo_tight60_v1"
MANIFEST = ROOT / "manifests" / "l2o_hpo_tight60_v1.json"

EXPECTED = {
    "PA2-PA3": {"t000", "t001", "t002", "t007"},
    "PA2-PA8": {"t000", "t001", "t002", "t005"},
    "PA3-PA8": {"t000", "t002", "t003", "t007"},
}
PARAMS = (
    "lr", "weight_decay", "lambda_center", "label_smoothing",
    "entropy_loss_weight", "mlp_dropout", "grad_clip_norm",
    "scheduler_name", "batch_size",
)

def _name(pair, recipe):
    return f"l2o_hpo_tight60_{pair.replace('-', '_')}_{recipe}.json"

def test_tight60_completion_contract():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["source_pr37_head"] == "ab87931408651b0b3516d910b13474822fb2a93d"
    assert manifest["protocol"]["max_epochs"] == 60
    assert manifest["protocol"]["cosine_t_max_epochs"] == 60
    assert manifest["protocol"]["selection_evidence"] == "known_validation_only"
    assert manifest["protocol"]["target_open_osr_allowed_for_selection"] is False

    expected_files = {_name(pair, recipe) for pair, recipes in EXPECTED.items() for recipe in recipes}
    actual_files = {p.name for p in CFG.glob("*.json")}
    assert actual_files == expected_files

    for pair, recipes in EXPECTED.items():
        for recipe in recipes:
            cfg = json.loads((CFG / _name(pair, recipe)).read_text())
            source_path = ROOT / cfg["hpo_trial"]["source_wave0_config"]
            src = json.loads(source_path.read_text())

            assert cfg["epochs"] == 60
            assert cfg["early_stopping_patience"] == 10
            assert cfg["early_stopping_mode"] == "known_only"
            assert cfg["model_selection_metric"] == "val_macro_f1"
            assert cfg["open_val_frac"] == 0
            assert cfg["build_balanced_val_open"] is False
            assert cfg["require_true_val_open"] is False
            assert cfg["allow_val_open_fallback"] is False
            assert cfg["quarantine_target_until_test"] is True
            assert cfg["target_unknown_pa"] == src["target_unknown_pa"]
            assert cfg["surrogate_open_pa"] == src["surrogate_open_pa"]

            trial = cfg["hpo_trial"]
            assert trial["stage"] == "tight60"
            assert trial["canonical_pair"] == pair
            assert trial["selection_evidence"] == "known_validation_only"
            assert trial["target_metrics_allowed_for_selection"] is False
            assert trial["test_metrics_allowed_for_selection"] is False
            assert trial["params"] == src["hpo_trial"]["params"]

            for key in PARAMS:
                assert cfg.get(key) == src.get(key)

            if cfg["scheduler_name"] == "cosine":
                assert cfg["scheduler_t_max_epochs"] == 60
                assert trial["scheduler_t_max_epochs"] == 60
            elif cfg["scheduler_name"] == "plateau":
                assert "scheduler_t_max_epochs" not in cfg
                assert trial["scheduler_t_max_epochs"] is None
            else:
                raise AssertionError(cfg["scheduler_name"])
