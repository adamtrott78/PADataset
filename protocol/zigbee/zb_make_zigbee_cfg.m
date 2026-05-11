function zbCfg = zb_make_zigbee_cfg(cfg)
%ZB_MAKE_ZIGBEE_CFG Build strict Zigbee O-QPSK cfg from cfg and validate Fs.

    fmt = string(pa_get_nested(cfg, "zigbee_base_waveform.format"));
    assert(fmt == "OQPSK", "Only OQPSK supported in v0.1");

    band_mhz = double(pa_get_nested(cfg, "zigbee_base_waveform.band_mhz"));
    assert(any(band_mhz == [780, 868, 915, 2380, 2450]), ...
        "zigbee_base_waveform.band_mhz must be one of [780, 868, 915, 2380, 2450]");

    samples_per_chip = double(pa_get_nested(cfg, "zigbee_base_waveform.samples_per_chip"));
    assert(samples_per_chip == round(samples_per_chip) && ...
           samples_per_chip >= 2 && mod(samples_per_chip, 2) == 0, ...
           "zigbee_base_waveform.samples_per_chip must be an even positive integer");

    psdu_length_bytes = double(pa_get_nested(cfg, "zigbee_base_waveform.psdu_length_bytes"));
    assert(psdu_length_bytes == round(psdu_length_bytes) && ...
           psdu_length_bytes >= 0 && psdu_length_bytes <= 127, ...
           "zigbee_base_waveform.psdu_length_bytes must be an integer in [0,127]");

    fs_cfg = double(pa_get_nested(cfg, "rates.fs_hz"));

    % Let MATLAB derive SampleRate internally
    zbCfg = lrwpanOQPSKConfig( ...
        Band=band_mhz, ...
        SamplesPerChip=samples_per_chip, ...
        PSDULength=psdu_length_bytes);

    fs_eff = double(zbCfg.SampleRate);

    assert(abs(fs_eff - fs_cfg) < 1e-6, ...
        "Zigbee sample rate mismatch: lrwpanOQPSKConfig.SampleRate=%.6f vs rates.fs_hz=%.6f", ...
        fs_eff, fs_cfg);
end