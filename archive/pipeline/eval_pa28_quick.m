function eval_pa28_quick()
%EVAL_PA28_QUICK Fast PA2/PA8-only validator check + small evidence pack.
% Requires pilot files:
%   pilot_out_v01/data/pilot_S01_PA2.mat
%   pilot_out_v01/data/pilot_S01_PA8.mat
%
% Outputs:
%   pilot_out_v01/evidence_pack_pa28_quick/pa28_quick_summary.mat
%   pilot_out_v01/evidence_pack_pa28_quick/png/*.png

    cfg = pa_load_cfg("starter.json");
    pa_validate_cfg(cfg);

    out_root  = fullfile("pilot_out_v01");
    data_root = fullfile(out_root, "data");
    ev_root   = fullfile(out_root, "evidence_pack_pa28_quick");
    if ~exist(ev_root,"dir"), mkdir(ev_root); end

    session_id = 1;

    % speed knobs
    N_eval = 120;    % evaluate first N windows from each file
    make_plots = true;

    fPA2 = fullfile(data_root, sprintf("pilot_S%02d_PA2.mat", session_id));
    fPA8 = fullfile(data_root, sprintf("pilot_S%02d_PA8.mat", session_id));

    S2 = load(fPA2); X2 = S2.Xsig_all; M2 = S2.meta;
    S8 = load(fPA8); X8 = S8.Xsig_all; M8 = S8.meta;

    N2 = min(N_eval, size(X2,2));
    N8 = min(N_eval, size(X8,2));

    % acceptance counts: rows=generated [PA2;PA8], cols=validator [PA2, PA8]
    A = zeros(2,2);
    T = [N2; N8];

    % evidence slots
    ev = struct();

    % ---- eval PA2 windows ----
    for i = 1:N2
        sid = M2(i).session_id; tid = M2(i).tape_id; seg = M2(i).segment_id; wid = M2(i).window_id;
        x = X2(:,i);

        [x2, v2] = pa_process_window_pa2_v01(cfg, x, sid, tid, seg, wid);
        [~,  v8] = pa_process_window_pa8_v01(cfg, x, sid, tid, seg, wid);

        A(1,1) = A(1,1) + double(v2.valid);
        A(1,2) = A(1,2) + double(v8.valid);

        if ~isfield(ev,"PA2_typical") && v2.valid
            ev.PA2_typical = pack(x2, v2, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA2_rejected") && ~v2.valid
            ev.PA2_rejected = pack(x2, v2, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA2_as_PA8") && v8.valid
            ev.PA2_as_PA8 = pack(x2, v2, sid, tid, seg, wid, i);
        end
    end

    % ---- eval PA8 windows ----
    for i = 1:N8
        sid = M8(i).session_id; tid = M8(i).tape_id; seg = M8(i).segment_id; wid = M8(i).window_id;
        x = X8(:,i);

        [x8, v8] = pa_process_window_pa8_v01(cfg, x, sid, tid, seg, wid);
        [~,  v2] = pa_process_window_pa2_v01(cfg, x, sid, tid, seg, wid);

        A(2,1) = A(2,1) + double(v2.valid);
        A(2,2) = A(2,2) + double(v8.valid);

        if ~isfield(ev,"PA8_typical") && v8.valid
            ev.PA8_typical = pack(x8, v8, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA8_rejected") && ~v8.valid
            ev.PA8_rejected = pack(x8, v8, sid, tid, seg, wid, i);
        end
        if ~isfield(ev,"PA8_as_PA2") && v2.valid
            ev.PA8_as_PA2 = pack(x8, v8, sid, tid, seg, wid, i);
        end
    end

    rates = A ./ max(1, T);
    row_labels = ["gen_PA2"; "gen_PA8"];
    col_labels = ["val_PA2","val_PA8"];

    disp("=== PA2/PA8 quick acceptance rates (rows=generated, cols=validator) ===");
    fprintf("          %7s  %7s\n", col_labels(1), col_labels(2));
    fprintf("%-8s  %7.3f  %7.3f\n", row_labels(1), rates(1,1), rates(1,2));
    fprintf("%-8s  %7.3f  %7.3f\n", row_labels(2), rates(2,1), rates(2,2));

    tbl = struct();
    tbl.row_labels = row_labels;
    tbl.col_labels = col_labels;
    tbl.rates = rates;

    save(fullfile(ev_root, "pa28_quick_summary.mat"), "cfg", "tbl", "A", "T", "ev");
    fprintf("Saved: %s\n", fullfile(ev_root, "pa28_quick_summary.mat"));

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
% 3-panel: envelope + mask dots, spectrogram, plus a text panel for repeat stats when present.

    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    W  = numel(x);
    tms = (0:W-1)/Fs*1e3;

    % mask for overlay:
    % - PA2: burst-train span from E2/E3
    % - PA8: train span from detected repeat intervals (vr.det.repeat.intervals)
    mask = false(W,1);

    if contains(tag,"PA2")
        bp = pa_get_nested(cfg,"validation.detectors.burst.params");
        e23 = pa_detect_E2E3(x, round(Fs), double(bp.power_smoothing_s), double(bp.refractory_s), ...
                             double(bp.thresholds.hi_mad_k), double(bp.thresholds.lo_mad_k));
        if ~isempty(e23.rise_idx) && ~isempty(e23.fall_idx)
            a = e23.rise_idx(1); b = e23.fall_idx(end);
            mask(max(1,a):min(W,b)) = true;
        end
    elseif contains(tag,"PA8")
        if isfield(vr,"det") && isfield(vr.det,"repeat") && isfield(vr.det.repeat,"intervals") && ~isempty(vr.det.repeat.intervals)
            iv = vr.det.repeat.intervals;
            a = iv(1,1); b = iv(end,2);
            a = max(1,min(W,a)); b = max(1,min(W,b));
            if b>=a, mask(a:b)=true; end
        end
    end

    close_s = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
    kclose = max(1, round(close_s * Fs));
    mask = pa_mask_close(mask, kclose);

    nfft = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.nfft"));
    hop  = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.hop"));
    win  = hann(nfft,"periodic");

    f = figure("Visible","off","Color","w","Position",[100 100 1400 900]);
    tiledlayout(3,1,"Padding","compact","TileSpacing","compact");

    % Panel 1: envelope + mask
    nexttile;
    env = abs(x).^2;
    plot(tms, env, "k"); hold on;
    if any(mask)
        yy = max(env)*0.9;
        plot(tms(mask), yy*ones(sum(mask),1), ".", "MarkerSize",2);
    end
    grid on; xlabel("Time (ms)"); ylabel("|x|^2");
    title(sprintf("%s | valid=%d | %s", tag, vr.valid, vr.reject_reason), "Interpreter","none");

    % Panel 2: spectrogram
    nexttile;
    [S,F,T] = spectrogram(x, win, nfft-hop, nfft, Fs, "centered");
    imagesc(T*1e3, F/1e6, 10*log10(abs(S).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)"); title("Spectrogram (dB)");
    colorbar;

    % Panel 3: stats text
    nexttile;
    axis off;
    txt = "";
    if isfield(vr,"det") && isfield(vr.det,"repeat")
        rr = vr.det.repeat;
        if isfield(rr,"count")
            txt = txt + sprintf("repeat.detected=%d  used=%d\n", rr.count.detected, rr.count.used);
        end
        if isfield(rr,"span")
            txt = txt + sprintf("repeat.span.frac=%.3f\n", rr.span.frac);
        end
        if isfield(rr,"similarity")
            txt = txt + sprintf("repeat.sim.score=%.3f\n", rr.similarity.score);
        end
    end
    if txt == ""
        txt = "no repeat metrics in vr.det";
    end
    text(0.05,0.8,txt,"FontSize",14);

    exportgraphics(f, out_png);
    close(f);
end