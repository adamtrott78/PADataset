function btCfg = bt_make_ble_cfg(cfg)
%BT_MAKE_BLE_CFG Build Bluetooth LE waveform cfg from cfg and validate Fs.

    fmt = string(pa_get_nested(cfg, "bluetooth_base_waveform.format"));
    assert(fmt == "BLE", "Only BLE supported in v0.1");

    btCfg = struct();
    btCfg.Mode              = string(pa_get_nested(cfg, "bluetooth_base_waveform.mode"));
    btCfg.ChannelIndex      = double(pa_get_nested(cfg, "bluetooth_base_waveform.channel_index"));
    btCfg.SamplesPerSymbol  = double(pa_get_nested(cfg, "bluetooth_base_waveform.samples_per_symbol"));
    btCfg.AccessAddressHex  = char(pa_get_nested(cfg, "bluetooth_base_waveform.access_address"));
    btCfg.AccessAddress     = hexToBits32ColLocal(btCfg.AccessAddressHex);
    btCfg.WhitenStatus      = char(pa_get_nested(cfg, "bluetooth_base_waveform.whiten_status"));
    btCfg.ModulationIndex   = double(pa_get_nested(cfg, "bluetooth_base_waveform.modulation_index"));
    btCfg.PulseLength       = double(pa_get_nested(cfg, "bluetooth_base_waveform.pulse_length"));

    btCfg.PDUType           = char(pa_get_nested(cfg, "bluetooth_base_waveform.pdu_type"));
    btCfg.AdvertiserAddress = char(pa_get_nested(cfg, "bluetooth_base_waveform.advertiser_address"));
    btCfg.AdvertisingData   = char(pa_get_nested(cfg, "bluetooth_base_waveform.advertising_data"));

    fs_cfg = double(pa_get_nested(cfg, "rates.fs_hz"));

    switch btCfg.Mode
        case {"LE1M","LE500K","LE125K"}
            symrate = 1e6;
        case "LE2M"
            symrate = 2e6;
        otherwise
            error("Unsupported Bluetooth LE mode: %s", btCfg.Mode);
    end

    fs_eff = btCfg.SamplesPerSymbol * symrate;

    assert(btCfg.ChannelIndex == round(btCfg.ChannelIndex) && ...
           btCfg.ChannelIndex >= 0 && btCfg.ChannelIndex <= 39, ...
           "bluetooth_base_waveform.channel_index must be an integer in [0,39]");

    assert(btCfg.SamplesPerSymbol == round(btCfg.SamplesPerSymbol) && ...
           btCfg.SamplesPerSymbol >= 1, ...
           "bluetooth_base_waveform.samples_per_symbol must be a positive integer");

    assert(any(string(btCfg.WhitenStatus) == ["On","Off"]), ...
        "bluetooth_base_waveform.whiten_status must be 'On' or 'Off'");

    assert(btCfg.ModulationIndex >= 0.45 && btCfg.ModulationIndex <= 0.55, ...
        "bluetooth_base_waveform.modulation_index must be in [0.45, 0.55]");

    assert(btCfg.PulseLength == round(btCfg.PulseLength) && ...
           btCfg.PulseLength >= 1 && btCfg.PulseLength <= 4, ...
           "bluetooth_base_waveform.pulse_length must be an integer in [1,4]");

    assert(abs(fs_eff - fs_cfg) < 1e-6, ...
        "Bluetooth sample rate mismatch: SamplesPerSymbol*symbolRate=%.6f vs rates.fs_hz=%.6f", ...
        fs_eff, fs_cfg);

    btCfg.SampleRate = fs_eff;
end

function bits = hexToBits32ColLocal(h)
%HEXTOBITS32COLLOCAL Convert 8-char hex string to 32x1 binary column vector.
    h = upper(char(h));
    assert(numel(h) == 8, "AccessAddress hex string must be 8 characters.");

    bits = zeros(32,1);
    k = 1;
    for i = 1:2:numel(h)
        byte = hex2dec(h(i:i+1));
        b = dec2bin(byte, 8) - '0';   % 1x8 numeric row
        bits(k:k+7) = b(:);           % make it a column
        k = k + 8;
    end
end