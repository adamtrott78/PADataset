function eval_pa34_quick()
%EVAL_PA34_QUICK Fast PA3/PA4-only validator check + small evidence pack.

    cfg = pa_load_cfg("starter.json");
    pa_validate_cfg(cfg);

    out_root  = fullfile("pilot_out_v01");
    data_root = fullfile(out_root, "data");
    ev_root   = fullfile(out_root, "evidence_pack_pa34_quick");
    if ~exist(ev_root,"dir"), mkdir(ev_root); end

    session_id = 1;

    % speed knobs
    N_eval = 80;   % evaluate first N windows from each file (increase if needed)
    make_plots = true;

    files = struct();
    files.PA3 = fullfile(data_root, sprintf("pilot_S%02d_PA3.mat", session_id));
    files.PA4 = fullfile(data_root, sprintf("pilot_S%02d_PA4.mat", session_id));

    S3 = load(files.PA3); X3 = S3.Xsig_all; M3 = S3.meta;
    S4 = load(files.PA4); X4 = S4.Xsig_all; M4 = S4.meta;

    N3 = min(N_eval, size(X3,2));
    N4 = min(N_eval, size(X4,2));

    % acceptance counts: rows=generated [PA3;PA4], cols=validator [PA3, PA4]
    A = zeros(2,2);
    T = [N3; N4];

    % evidence slots
    ev = struct();

    % ---- eval PA3 windows ----
    for i = 1:N3
        sid = M3(i).session_id; tid = M3(i).tape_id; seg = M3(i).segment_id; wid = M3(i).window_id;
        x = X3(:,i);

        [x3, v3] = pa_process_window_pa3_v01(cfg, x, sid, tid, seg, wid);
        [~,  v4] = pa_process_window_pa4_v01(cfg, x, sid, tid, seg, wid);

        A(1,1) = A(1,1) + double(v3.valid);
        A(1,2) = A(1,2) + double(v4.valid);

        if ~isfield(ev,"PA3_typical") && v3.valid
            ev.PA3_typical = pack(x3, v3, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA3_rejected") && ~v3.valid
            ev.PA3_rejected = pack(x3, v3, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA3_as_PA4") && v4.valid
            ev.PA3_as_PA4 = pack(x3, v3, sid, tid, seg, wid, i);
        end
    end

    % ---- eval PA4 windows ----
    for i = 1:N4
        sid = M4(i).session_id; tid = M4(i).tape_id; seg = M4(i).segment_id; wid = M4(i).window_id;
        x = X4(:,i);

        [x4, v4] = pa_process_window_pa4_v01(cfg, x, sid, tid, seg, wid);
        [~,  v3] = pa_process_window_pa3_v01(cfg, x, sid, tid, seg, wid);

        A(2,1) = A(2,1) + double(v3.valid);
        A(2,2) = A(2,2) + double(v4.valid);

        if ~isfield(ev,"PA4_typical") && v4.valid
            ev.PA4_typical = pack(x4, v4, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA4_rejected") && ~v4.valid
            ev.PA4_rejected = pack(x4, v4, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA4_as_PA3") && v3.valid
            ev.PA4_as_PA3 = pack(x4, v4, sid, tid, seg, wid, i);
        end
    end

    rates = A ./ max(1, T);
    row_labels = ["gen_PA3"; "gen_PA4"];
    col_labels = ["val_PA3","val_PA4"];
    
    disp("=== PA3/PA4 quick acceptance rates (rows=generated, cols=validator) ===");
    fprintf("          %7s  %7s\n", col_labels(1), col_labels(2));
    fprintf("%-8s  %7.3f  %7.3f\n", row_labels(1), rates(1,1), rates(1,2));
    fprintf("%-8s  %7.3f  %7.3f\n", row_labels(2), rates(2,1), rates(2,2));
    
    tbl = struct();
    tbl.row_labels = row_labels;
    tbl.col_labels = col_labels;
    tbl.rates = rates;

    save(fullfile(ev_root, "pa34_quick_summary.mat"), "cfg", "tbl", "A", "T", "ev");
    fprintf("Saved: %s\n", fullfile(ev_root, "pa34_quick_summary.mat"));

    if make_plots
        write_ev(ev_root, cfg, ev);
        fprintf("Evidence pack written to: %s\n", ev_root);
    end
end

function s = pack(x, vr, sid, tid, seg, wid, idx)
    s = struct("x",x,"vr",vr,"session_id",sid,"tape_id",tid,"segment_id",seg,"window_id",wid,"idx",idx);
end

function write_ev(ev_root, cfg, ev)
    d = fullfile(ev_root, "png");
    if exist(d,"dir"), rmdir(d,"s"); end
    mkdir(d);

    names = fieldnames(ev);
    for k = 1:numel(names)
        nm = names{k};
        ex = ev.(nm);
        out = fullfile(d, nm + ".png");
        plot_one(cfg, nm, ex.x, ex.vr, out);
    end
end

function plot_one(cfg, tag, x, vr, out_png)
% 3-panel: envelope + mask dots, spectrogram, freq-state bin trace + jump count
    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    W  = numel(x);
    tms = (0:W-1)/Fs*1e3;

    % occupancy-ish mask for PA3/PA4 (noise-referenced using snr_quiet)
    mask = false(W,1);
    if isfield(vr,"proc") && isfield(vr.proc,"snr_quiet_db")
        snr_quiet = vr.proc.snr_quiet_db;
        occ_k = double(pa_get_nested(cfg,"validation.detectors.burst.params.thresholds.occ_sigma_k"));
        sigma_q = 10^(-double(snr_quiet)/20);
        th_pow = (occ_k * sigma_q)^2;
        smooth_s = double(pa_get_nested(cfg,"validation.detectors.burst.params.power_smoothing_s"));
        M = max(1, round(smooth_s * Fs));
        ps = filter(ones(M,1)/M, 1, abs(x).^2);
        mask = ps > th_pow;
        close_s = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
        kclose = max(1, round(close_s * Fs));
        mask = pa_mask_close(mask, kclose);
    end

    nfft = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.nfft"));
    hop  = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.hop"));
    nb   = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.nbins"));

    B = pa_stft_bins32(x, nfft, hop, nb);
    pframes = double(pa_get_nested(cfg,"validation.detectors.freq.params.persistence_frames"));
    sframes = double(pa_get_nested(cfg,"validation.detectors.freq.params.smooth_frames"));
    dbins   = double(pa_get_nested(cfg,"validation.detectors.freq.params.min_delta_bins"));
    fj = pa_detect_freq_jump(B, pframes, sframes, dbins);

    f = figure("Visible","off","Color","w","Position",[100 100 1400 900]);
    tiledlayout(3,1,"Padding","compact","TileSpacing","compact");

    nexttile;
    env = abs(x).^2;
    plot(tms, env, "k"); hold on;
    if any(mask)
        yy = max(env)*0.9;
        plot(tms(mask), yy*ones(sum(mask),1), ".", "MarkerSize",2);
    end
    grid on; xlabel("Time (ms)"); ylabel("|x|^2");
    title(sprintf("%s | valid=%d | %s", tag, vr.valid, vr.reject_reason), "Interpreter","none");

    nexttile;
    win = hann(nfft,"periodic");
    [S,F,T] = spectrogram(x, win, nfft-hop, nfft, Fs, "centered");
    imagesc(T*1e3, F/1e6, 10*log10(abs(S).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)"); title("Spectrogram (dB)");
    colorbar;

    nexttile;
    plot(fj.bin_trace, "-"); grid on;
    xlabel("STFT frame"); ylabel("Dominant bin state (1..nbins)");
    title(sprintf("freq.jump.count=%d", fj.count), "Interpreter","none");

    exportgraphics(f, out_png);
    close(f);
end