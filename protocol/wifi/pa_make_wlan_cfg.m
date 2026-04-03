function wlanCfg = pa_make_wlan_cfg(cfg)
%PA_MAKE_WLAN_CFG Build wlanNonHTConfig from YAML cfg and validate Fs.

    fmt = string(pa_get_nested(cfg, "wlan_base_waveform.format"));
    assert(fmt == "NonHT", "Only NonHT supported in v0.1");

    wlanCfg = wlanNonHTConfig;
    wlanCfg.ChannelBandwidth     = char(pa_get_nested(cfg, "wlan_base_waveform.channel_bandwidth"));
    wlanCfg.MCS                  = double(pa_get_nested(cfg, "wlan_base_waveform.mcs"));
    wlanCfg.PSDULength           = double(pa_get_nested(cfg, "wlan_base_waveform.psdu_length_bytes"));
    wlanCfg.NumTransmitAntennas  = double(pa_get_nested(cfg, "wlan_base_waveform.num_tx_antennas"));

    osf = double(pa_get_nested(cfg, "wlan_base_waveform.oversampling_factor"));
    fs_cfg = double(pa_get_nested(cfg, "rates.fs_hz"));
    fs_eff = wlanSampleRate(wlanCfg) * osf;

    assert(abs(fs_eff - fs_cfg) < 1e-6, "WLAN sample rate mismatch: wlanSampleRate(cfg)*OSF=%.6f vs rates.fs_hz=%.6f", fs_eff, fs_cfg);
end