function smoke_test_v01()
    cfg_path = "starter.json";
    cfg = pa_load_cfg(cfg_path);
    pa_validate_cfg(cfg);

    wlanCfg = pa_make_wlan_cfg(cfg);

    % Deterministic seeds
    master_seed = pa_get_nested(cfg, "generator.seeds.master_seed");
    schema      = pa_get_nested(cfg, "schema_version");
    [~, seed_payload] = pa_sha_seed(master_seed, schema, 1, 1, 1, 1, "payload");
    [~, seed_scr]     = pa_sha_seed(master_seed, schema, 1, 1, 1, 1, "scrambler");

    % Scrambler init in [1..127]
    rs  = RandStream("mt19937ar","Seed",double(seed_scr));
    scr = randi(rs, [1 127], 1, 1);

    [x1, info1] = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);
    [x2, ~]     = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);

    fprintf("Packet nsamp: %d\n", info1.nsamp);
    fprintf("Bitwise equal: %d\n", isequal(x1, x2));
    fprintf("RMS (raw): %.6f\n", sqrt(mean(abs(double(x1)).^2)));

    % Quick sanity: confirm cfg-driven N
    fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    T  = double(pa_get_nested(cfg,"windowing.window_length_s"));
    fprintf("Window N (nominal): %d\n", round(fs*T));
end