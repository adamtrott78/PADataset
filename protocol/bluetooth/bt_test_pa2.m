function bt_test_pa2(n_windows)
%BT_TEST_PA2 Generate and immediately validate Bluetooth PA2 windows only.

    if nargin < 1 || isempty(n_windows)
        n_windows = 200;
    end

    P = pa_paths();
    cfg = pa_load_cfg(fullfile(P.config, "starter.json"));

    Fs = round(double(pa_get_nested(cfg,"rates.fs_hz")));
    W  = round(double(pa_get_nested(cfg,"windowing.window_length_s")) * Fs);

    session_id = 1;
    tape_id    = 1;
    segment_id = 1;

    starts = int64(1 + (0:n_windows-1)*W).';
    plan = struct();
    plan.Fs = Fs;
    plan.W = W;
    plan.starts = starts;

    fprintf("Generating %d Bluetooth PA2 windows...\n", n_windows);
    [Xsig, meta] = bt_gen_windows_pa2_stream(cfg, session_id, tape_id, segment_id, plan);

    reasons = strings(1, size(Xsig,2));
    valid = false(1, size(Xsig,2));

    fprintf("Evaluating %d Bluetooth PA2 windows...\n", n_windows);
    for i = 1:size(Xsig,2)
        [~, vr] = pa_process_window_pa2_v01(cfg, Xsig(:,i), ...
            meta(i).session_id, meta(i).tape_id, meta(i).segment_id, meta(i).window_id);
        reasons(i) = string(vr.reject_reason);
        valid(i) = logical(vr.valid);
    end

    acc = mean(valid);
    fprintf("\nBluetooth PA2 acceptance: %.2f%% (%d/%d)\n", 100*acc, sum(valid), n_windows);

    tabulate(cellstr(reasons.'))

    out_root = fullfile(pa_root(), "results", "bluetooth", "digital", "bt_test_pa2");
    if ~exist(out_root, "dir"), mkdir(out_root); end

    save(fullfile(out_root, "bt_test_pa2_summary.mat"), ...
        "cfg", "Xsig", "meta", "reasons", "valid", "acc", "Fs", "W", "-v7.3");

    fprintf("Saved: %s\n", fullfile(out_root, "bt_test_pa2_summary.mat"));
end