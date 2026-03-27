function test()
    cfg = pa_load_cfg("starter_ota12.json");
    disp(pa_get_nested(cfg,"rates.fs_hz"));
    disp(pa_get_nested(cfg,"windowing.window_length_s"));
end