from pathlib import Path


def test_stft_launcher_anchors_cwd_before_preflight_imports():
    text = Path("scripts/mth602/run_stft_track_ablation_local.sh").read_text(
        encoding="utf-8"
    )

    root_pos = text.index('ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"')
    cd_pos = text.index('cd "$ROOT"', root_pos)
    preflight_pos = text.index("=== PREFLIGHT: ENVIRONMENT + RAW OTA ACCESS ===", cd_pos)
    import_pos = text.index("from experiments import", preflight_pos)

    assert root_pos < cd_pos < preflight_pos < import_pos
    assert 'export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"' in text


def test_stft_launcher_still_refuses_tmp_and_preserves_resume_semantics():
    text = Path("scripts/mth602/run_stft_track_ablation_local.sh").read_text(
        encoding="utf-8"
    )

    assert 'case "$ROOT" in' in text
    assert '/tmp/*)' in text
    assert 'Refusing transient /tmp checkout' in text
    assert '--force' not in text
    assert '--probe-only' in text


def test_stft_provenance_preflight_freezes_canonical_core_universe():
    cpu_text = Path("experiments/pa_build_stft_track_cache.py").read_text(
        encoding="utf-8"
    )
    gpu_text = Path("experiments/pa_build_stft_track_cache_gpu.py").read_text(
        encoding="utf-8"
    )

    assert "EXPECTED_CORE_PROTOCOLS" in cpu_text
    assert "EXPECTED_CORE_SHARDS = tuple(range(1, 21))" in cpu_text
    assert "EXPECTED_CORE_SUFFIXES" in cpu_text
    assert "Expected exactly 360 canonical unified-core STFT sources" in cpu_text
    assert '"ignored_noncanonical_records"' in cpu_text
    assert "discover_stft_core_sources(setup)" in gpu_text
    assert "resolved_all = [" in gpu_text
    assert '"provenance_records_resolved": len(resolved_all)' in gpu_text
    assert '"canonical_source_records"' in gpu_text
    assert '"ignored_noncanonical_records"' in gpu_text
    assert 'mode="unique basename"' not in gpu_text
