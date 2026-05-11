function make_pa_slide_png_pipeline_v01(cfg_file, session_id, out_dir)
    P = pa_paths();
%MAKE_PA_SLIDE_PNG_PIPELINE_V01 Slide-ready PNGs using your actual pipeline.
% Uses pa_process_window_pa*_v01 + shared detectors (pa_detect_*).
%
% Output:
%   out_dir/PA2.png, PA3.png, PA4.png, PA8.png
%
% Usage:
%   make_pa_slide_png_pipeline_v01("starter.json", 1, fullfile("pa_slide_png"));

    if nargin < 1 || isempty(cfg_file), cfg_file = fullfile(P.config,"starter.json"); end
    if nargin < 2 || isempty(session_id), session_id = 1; end
    if nargin < 3 || isempty(out_dir), out_dir = P.results_wifi_digital_make_pa_slide; end
    if ~exist(out_dir,"dir"), mkdir(out_dir); end

    if ~(contains(string(cfg_file), filesep) || isfile(cfg_file))
        cfg_file = fullfile(P.config, string(cfg_file));
    end
    cfg = pa_load_cfg(cfg_file);
    pa_validate_cfg(cfg);

    data_root = P.data_wifi_pilot;
    PAs = ["PA2","PA3","PA4","PA8"];

    % --- pick typical example per PA using the real pipeline ---
    ex = struct();
    for pa = PAs
        f = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", session_id, pa));
        if ~isfile(f), error("Missing pilot file: %s", f); end
        S = load(f,"Xsig_all","meta");
        X = S.Xsig_all; M = S.meta;

        found = false;
        for i = 1:size(X,2)
            sid = M(i).session_id; tid = M(i).tape_id; seg = M(i).segment_id; wid = M(i).window_id;
            x = X(:,i);
            [x_fin, vr] = run_pa_pipeline(pa, cfg, x, sid, tid, seg, wid);
            if vr.valid
                ex.(char(pa)) = struct("x",x_fin,"vr",vr,"meta",M(i),"idx",i);
                found = true;
                break;
            end
        end
        if ~found
            error("Could not find a valid example for %s (self validation never passed).", pa);
        end
        fprintf("Picked %s idx=%d (window_id=%d)\n", pa, ex.(char(pa)).idx, ex.(char(pa)).meta.window_id);
    end

    % --- render PNGs ---
    render_pa2(cfg, ex.PA2.x, ex.PA2.vr, fullfile(out_dir,"PA2.png"));
    render_pa3(cfg, ex.PA3.x, ex.PA3.vr, fullfile(out_dir,"PA3.png"));
    render_pa4(cfg, ex.PA4.x, ex.PA4.vr, fullfile(out_dir,"PA4.png"));
    render_pa8(cfg, ex.PA8.x, ex.PA8.vr, fullfile(out_dir,"PA8.png"));

    fprintf("Wrote slide PNGs to: %s\n", out_dir);
end

% ---------------- pipeline dispatch ----------------

function [x_fin, vr] = run_pa_pipeline(pa, cfg, x, sid, tid, seg, wid)
    switch string(pa)
        case "PA2"
            [x_fin, vr] = pa_process_window_pa2_v01(cfg, x, sid, tid, seg, wid);
        case "PA3"
            [x_fin, vr] = pa_process_window_pa3_v01(cfg, x, sid, tid, seg, wid);
        case "PA4"
            [x_fin, vr] = pa_process_window_pa4_v01(cfg, x, sid, tid, seg, wid);
        case "PA8"
            [x_fin, vr] = pa_process_window_pa8_v01(cfg, x, sid, tid, seg, wid);
        otherwise
            error("Unknown PA: %s", pa);
    end
end

% ---------------- shared helpers ----------------

function [SdB, F_MHz, T_ms] = compute_spec(x, Fs)
    nfft = 2048; hop = 512;
    win = hann(nfft,"periodic");
    [S,F,T] = spectrogram(x, win, nfft-hop, nfft, Fs, "centered");
    SdB = 10*log10(abs(S).^2 + 1e-12);
    F_MHz = F/1e6;
    T_ms = T*1e3;
end

function mask = close_mask(cfg, mask, Fs)
    close_s = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
    kclose = max(1, round(close_s * Fs));
    mask = pa_mask_close(mask, kclose);
end

function [occ_mask, occ] = occupancy_mask_from_pipeline(cfg, x, vr)
    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    bp = pa_get_nested(cfg,"validation.detectors.burst.params");
    smooth_s = double(bp.power_smoothing_s);
    close_s  = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
    occ_k    = double(pa_get_nested(cfg,"validation.detectors.burst.params.thresholds.occ_sigma_k"));

    snr_quiet = vr.proc.snr_quiet_db; % pipeline-chosen quiet SNR for this window
    occ = pa_detect_occupancy_from_quiet(x, Fs, snr_quiet, smooth_s, occ_k, close_s, 0);
    occ_mask = occ.mask;
end

% ---------------- renderers ----------------

function render_pa2(cfg, x, vr, out_png)
    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    W = numel(x);
    tms = (0:W-1)/Fs*1e3;

    % Burst-train span from pipeline edges (PA2 is about burst timing)
    mask = false(W,1);
    if isfield(vr,"det") && isfield(vr.det,"burst") && isfield(vr.det.burst,"edges")
        st = vr.det.burst.edges.start.idx;
        en = vr.det.burst.edges.end.idx;
        if ~isempty(st) && ~isempty(en)
            a = st(1); b = en(end);
            a = max(1,min(W,a)); b = max(1,min(W,b));
            if b>=a, mask(a:b)=true; end
        end
    end
    mask = close_mask(cfg, mask, Fs);

    [SdB,F_MHz,T_ms] = compute_spec(x, Fs);

    burst_len_ms = [];
    gap_ms = [];
    if isfield(vr.det,"burst") && isfield(vr.det.burst,"len_s")
        burst_len_ms = double(vr.det.burst.len_s(:))*1e3;
    end
    if isfield(vr.det,"burst") && isfield(vr.det.burst,"ibi_s")
        gap_ms = double(vr.det.burst.ibi_s(:))*1e3;
    end

    f = figure("Visible","off","Color","w","Position",[80 80 1500 900]);
    tiledlayout(2,1,"Padding","compact","TileSpacing","compact");

    nexttile;
    imagesc(T_ms, F_MHz, SdB); axis xy;
    xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title("PA2 — Burst Timing Acquisition (spectrogram)");
    colorbar;

    nexttile;
    stairs(tms, double(mask), "LineWidth", 1.5); grid on; ylim([-0.1 1.1]);
    xlabel("Time (ms)"); ylabel("On/Off");
    nb = 0; if isfield(vr.det.burst.edges.start,"count"), nb = vr.det.burst.edges.start.count; end
    mb = 0; if ~isempty(burst_len_ms), mb = max(burst_len_ms); end
    mg = 0; if ~isempty(gap_ms), mg = max(gap_ms); end
    title(sprintf("Burst timeline — bursts=%d | maxBurst=%.2f ms | maxGap=%.2f ms", nb, mb, mg));

    exportgraphics(f, out_png);
    close(f);
end

function render_pa3(cfg, x, vr, out_png)
    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    W = numel(x);
    tms = (0:W-1)/Fs*1e3;

    % Occupancy from your shared detector (uses the same quiet SNR the pipeline used)
    [mask, occ] = occupancy_mask_from_pipeline(cfg, x, vr);

    [SdB,F_MHz,T_ms] = compute_spec(x, Fs);

    f = figure("Visible","off","Color","w","Position",[80 80 1500 900]);
    tiledlayout(2,1,"Padding","compact","TileSpacing","compact");

    nexttile;
    imagesc(T_ms, F_MHz, SdB); axis xy;
    xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title("PA3 — Steady-State Characterization (spectrogram)");
    colorbar;

    nexttile;
    stairs(tms, double(mask), "LineWidth", 1.5); grid on; ylim([-0.1 1.1]);
    xlabel("Time (ms)"); ylabel("Occupied");
    title(sprintf("Occupancy — duty=%.2f | components=%d (should look mostly continuous)", ...
        occ.duty_frac, numel(occ.starts)));

    exportgraphics(f, out_png);
    close(f);
end

function render_pa4(cfg, x, vr, out_png)
    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));

    [SdB,F_MHz,T_ms] = compute_spec(x, Fs);

    % Prefer pipeline's trace if present; else compute a simple centroid trace.
    hop_trace = [];
    if isfield(vr,"det") && isfield(vr.det,"freq") && isfield(vr.det.freq,"jump") && isfield(vr.det.freq.jump,"centroid")
        hop_trace = double(vr.det.freq.jump.centroid(:)) / 1e6; % MHz
    else
        % fallback: recompute centroid from spectrogram power
        nfft = 2048; hop = 512;
        win = hann(nfft,"periodic");
        [S,F,T] = spectrogram(x, win, nfft-hop, nfft, Fs, "centered");
        P = abs(S).^2 + 1e-12;
        Fc = (F(:)'*P) ./ sum(P,1);   % Hz
        hop_trace = Fc(:)/1e6;        % MHz
        T_ms = T(:)*1e3;
    end

    f = figure("Visible","off","Color","w","Position",[80 80 1500 900]);
    tiledlayout(2,1,"Padding","compact","TileSpacing","compact");

    nexttile;
    imagesc(T_ms, F_MHz, SdB); axis xy;
    xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title("PA4 — Frequency Agility Characterization (spectrogram)");
    colorbar;

    nexttile;
    plot(linspace(0,20,numel(hop_trace)), hop_trace, "LineWidth", 1.5); grid on;
    xlabel("Time (ms)"); ylabel("Centroid (MHz)");
    title("Hop signature — step-like centroid changes indicate hops");

    exportgraphics(f, out_png);
    close(f);
end

function render_pa8(cfg, x, vr, out_png)
    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    W = numel(x);
    tms = (0:W-1)/Fs*1e3;

    [SdB,F_MHz,T_ms] = compute_spec(x, Fs);

    % Repeat intervals should already be in vr.det.repeat.intervals (pipeline output)
    intervals = [];
    if isfield(vr,"det") && isfield(vr.det,"repeat") && isfield(vr.det.repeat,"intervals")
        intervals = vr.det.repeat.intervals;
    end

    % For the bottom panel, show a simple "on/off" strip from repeat TRAIN span if possible.
    mask = false(W,1);
    if ~isempty(intervals)
        a = intervals(1,1); b = intervals(end,2);
        a = max(1,min(W,a)); b = max(1,min(W,b));
        if b>=a, mask(a:b)=true; end
    end
    mask = close_mask(cfg, mask, Fs);

    sim_score = NaN;
    used_rep = 0;
    if isfield(vr.det,"repeat") && isfield(vr.det.repeat,"similarity") && isfield(vr.det.repeat.similarity,"score")
        sim_score = double(vr.det.repeat.similarity.score);
    end
    if isfield(vr.det,"repeat") && isfield(vr.det.repeat,"count") && isfield(vr.det.repeat.count,"used")
        used_rep = double(vr.det.repeat.count.used);
    end

    f = figure("Visible","off","Color","w","Position",[80 80 1500 900]);
    tiledlayout(2,1,"Padding","compact","TileSpacing","compact");

    nexttile;
    imagesc(T_ms, F_MHz, SdB); axis xy;
    xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title("PA8 — Replay / Repeat Template Mining (spectrogram)");
    colorbar;

    nexttile;
    stairs(tms, double(mask), "LineWidth", 1.5); grid on; ylim([-0.1 1.1]);
    xlabel("Time (ms)"); ylabel("Replay span");
    if ~isnan(sim_score)
        title(sprintf("Repeat structure — repeatsUsed=%d | similarity=%.3f", used_rep, sim_score));
    else
        title(sprintf("Repeat structure — repeatsUsed=%d | similarity=N/A", used_rep));
    end

    exportgraphics(f, out_png);
    close(f);
end