function pa_validate_cfg(cfg)
%PA_VALIDATE_CFG Assert invariants and required fields for v0.1 starter (semantic detector IDs only).

    must(cfg, "schema_version");
    must(cfg, "rates.fs_hz");
    must(cfg, "windowing.window_length_s");

    must(cfg, "wlan_base_waveform.format");
    must(cfg, "wlan_base_waveform.channel_bandwidth");
    must(cfg, "wlan_base_waveform.mcs");
    must(cfg, "wlan_base_waveform.psdu_length_bytes");
    must(cfg, "wlan_base_waveform.num_tx_antennas");
    must(cfg, "wlan_base_waveform.oversampling_factor");

    must(cfg, "windowing.alignment_jitter_policy.max_jitter_s");
    must(cfg, "windowing.padding_policy.evidence_span_frac_min");
    must(cfg, "windowing.padding_policy.types");

    must(cfg, "generator.seeds.master_seed");
    must(cfg, "generator.structure.segment_min_seconds");
    must(cfg, "generator.structure.segment_max_seconds");

    must(cfg, "operators.freq_translation.max_abs_offset_hz");

    % Validation: semantic detector blocks
    must(cfg, "validation.drop_reject.discontinuity_rule.r_threshold");

    must(cfg, "validation.detectors.burst.edges.enabled");
    must(cfg, "validation.detectors.burst.params.power_smoothing_s");
    must(cfg, "validation.detectors.burst.params.refractory_s");
    must(cfg, "validation.detectors.burst.params.thresholds.hi_mad_k");
    must(cfg, "validation.detectors.burst.params.thresholds.lo_mad_k");
    must(cfg, "validation.detectors.burst.mask_close_s");

    must(cfg, "validation.detectors.stationarity.enabled");
    must(cfg, "validation.detectors.stationarity.params.nfft");
    must(cfg, "validation.detectors.stationarity.params.hop");
    must(cfg, "validation.detectors.stationarity.params.nbins");

    must(cfg, "validation.thresholds.stationarity.energy_high");
    must(cfg, "validation.thresholds.stationarity.shape_high");
    must(cfg, "validation.thresholds.repeat.similarity_min");
    must(cfg, "validation.thresholds.freq.jump_min_count");
    must(cfg, "validation.thresholds.burst.min_count");

    % Starter 4 PAs
    must(cfg, "pas.PA2"); must(cfg, "pas.PA3"); must(cfg, "pas.PA4"); must(cfg, "pas.PA8");

    % PA8 recorded-noise flag (optional but schema-stable)
    must(cfg, "pas.PA8.params.recorded_noise.enable");
    must(cfg, "pas.PA8.params.recorded_noise.snr_db");

    % Invariants
    fs = pa_get_nested(cfg, "rates.fs_hz");
    wl = pa_get_nested(cfg, "windowing.window_length_s");
    assert(abs(double(fs) - 20e6) < 1e-6, "Invariant failed: rates.fs_hz must be 20e6");
    assert(abs(double(wl) - 0.020) < 1e-12, "Invariant failed: windowing.window_length_s must be 0.020");

    % WLAN invariants
    fmt = string(pa_get_nested(cfg, "wlan_base_waveform.format"));
    cbw = string(pa_get_nested(cfg, "wlan_base_waveform.channel_bandwidth"));
    assert(fmt == "NonHT", "Starter v0.1 requires wlan_base_waveform.format == 'NonHT'");
    assert(cbw == "CBW20", "Starter v0.1 requires wlan_base_waveform.channel_bandwidth == 'CBW20'");

    % Segment length bounds
    smin = pa_get_nested(cfg, "generator.structure.segment_min_seconds");
    smax = pa_get_nested(cfg, "generator.structure.segment_max_seconds");
    assert(smin > 0 && smax >= smin, "Invalid segment_min/max_seconds");

    % Jitter sanity
    J = pa_get_nested(cfg, "windowing.alignment_jitter_policy.max_jitter_s");
    assert(J >= 0 && J <= 0.010, "max_jitter_s must be in [0,0.010] for v0.1 assumptions");
end

function must(cfg, path)
    try
        pa_get_nested(cfg, path);
    catch
        error("Missing required config field: %s", path);
    end
end