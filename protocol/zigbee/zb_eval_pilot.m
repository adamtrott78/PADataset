function zb_eval_pilot()
%ZB_EVAL_PILOT Evaluate saved Zigbee pilot windows and emit evidence pack.

    P = pa_paths();
    cfg = pa_load_cfg(fullfile(P.config, "starter.json"));
    pa_validate_cfg(cfg);

    data_root = fullfile(pa_root(), "data", "zigbee", "digital", "pilot");
    out_root  = fullfile(pa_root(), "results", "zigbee", "digital", "zb_eval_pilot");
    ev_root   = fullfile(out_root, "evidence_pack");

    if ~exist(out_root,"dir"), mkdir(out_root); end
    if ~exist(ev_root,"dir"), mkdir(ev_root); end

    session_id = 1;

    PAs     = ["PA2","PA3","PA4","PA8"];
    evalPAs = ["PA2","PA3","PA4","PA8"];

    K  = numel(PAs);
    Ke = numel(evalPAs);

    accept_counts = zeros(K,Ke);
    total_counts  = zeros(K,1);

    typical = struct();
    special = struct();

    for pi = 1:K
        pa = PAs(pi);
        infile = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", session_id, pa));
        fprintf("Loading %s\n", infile);

        S = load(infile);
        Xsig = S.Xsig_all;
        meta = S.meta;

        N = size(Xsig,2);
        if numel(meta) ~= N
            error("Meta length mismatch in %s", infile);
        end

        for i = 1:N
            session_id_i = meta(i).session_id;
            tape_id      = meta(i).tape_id;
            seg_id       = meta(i).segment_id;
            window_id    = meta(i).window_id;

            x_sig = Xsig(:,i);

            % self validation
            [x_fin, vr_self] = eval_self(pa, cfg, x_sig, session_id_i, tape_id, seg_id, window_id);

            total_counts(pi) = total_counts(pi) + 1;

            % cross validation
            for ej = 1:Ke
                pa_eval = evalPAs(ej);
                [~, vr2] = eval_self(pa_eval, cfg, x_sig, session_id_i, tape_id, seg_id, window_id);
                accept_counts(pi, ej) = accept_counts(pi, ej) + double(vr2.valid);
            end

            % pick one typical valid example for each PA
            if ~isfield(typical, char(pa)) && vr_self.valid
                typical.(char(pa)) = struct("idx",i,"x",x_fin,"vr",vr_self);
            end

            % special PA4 cases
            if pa == "PA4"
                if ~isfield(special,"PA4_as_PA3")
                    [~, vr_pa3] = pa_process_window_pa3_v01(cfg, x_sig, session_id_i, tape_id, seg_id, window_id);
                    if vr_pa3.valid
                        special.PA4_as_PA3 = struct("idx",i,"x",x_fin,"vr_pa4",vr_self,"vr_pa3",vr_pa3);
                    end
                end
                if ~isfield(special,"PA4_rejected") && ~vr_self.valid
                    special.PA4_rejected = struct("idx",i,"x",x_fin,"vr",vr_self);
                end
            end
        end
    end

    rates = accept_counts ./ max(1,total_counts);
    T = array2table(rates, "VariableNames", cellstr(evalPAs), "RowNames", cellstr(PAs));

    fprintf("\n=== Zigbee cross-PA acceptance rates (columns are validators) ===\n");
    disp(T);

    save(fullfile(out_root,"pilot_summary.mat"), ...
        "cfg","T","accept_counts","total_counts","PAs","evalPAs","typical","special");
    fprintf("Saved: %s\n", fullfile(out_root,"pilot_summary.mat"));

    write_typical(ev_root, cfg, typical);
    write_special(ev_root, cfg, special);

    fprintf("Evidence pack written to: %s\n", ev_root);
end


function [x_fin, vr] = eval_self(pa, cfg, x_sig, session_id, tape_id, seg_id, window_id)
    switch string(pa)
        case "PA2"
            [x_fin, vr] = pa_process_window_pa2_v01(cfg, x_sig, session_id, tape_id, seg_id, window_id);
        case "PA3"
            [x_fin, vr] = pa_process_window_pa3_v01(cfg, x_sig, session_id, tape_id, seg_id, window_id);
        case "PA4"
            [x_fin, vr] = pa_process_window_pa4_v01(cfg, x_sig, session_id, tape_id, seg_id, window_id);
        case "PA8"
            [x_fin, vr] = pa_process_window_pa8_v01(cfg, x_sig, session_id, tape_id, seg_id, window_id);
        otherwise
            error("Unknown PA %s", pa);
    end
end


function write_typical(ev_root, cfg, typical)
    PAs = ["PA2","PA3","PA4","PA8"];
    for pa = PAs
        if ~isfield(typical, char(pa)), continue; end
        d = fullfile(ev_root, "typical", char(pa));
        if ~exist(d,"dir"), mkdir(d); end
        ex = typical.(char(pa));
        out = fullfile(d, sprintf("%s_typical_idx%03d.png", pa, ex.idx));
        zb_pilot_plot_evidence(pa, cfg, ex.x, ex.vr, out, []);
    end
end


function write_special(ev_root, cfg, special)
    d = fullfile(ev_root, "special");
    if ~exist(d,"dir"), mkdir(d); end

    if isfield(special,"PA4_as_PA3")
        ex = special.PA4_as_PA3;
        out = fullfile(d, sprintf("PA4_as_PA3_idx%03d.png", ex.idx));
        zb_pilot_plot_evidence("PA4", cfg, ex.x, ex.vr_pa4, out, ex.vr_pa3);
    end

    if isfield(special,"PA4_rejected")
        ex = special.PA4_rejected;
        out = fullfile(d, sprintf("PA4_rejected_idx%03d.png", ex.idx));
        zb_pilot_plot_evidence("PA4", cfg, ex.x, ex.vr, out, []);
    end
end


function zb_pilot_plot_evidence(pa, cfg, x, vr, out_png, vr_alt)
% 3-panel figure:
%  (1) envelope + evidence mask overlay (+ repeat intervals for PA8)
%  (2) spectrogram
%  (3) dominant-bin trace

    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    W  = numel(x);
    tms = (0:W-1)/Fs*1e3;

    mask = false(W,1);

    if string(pa) == "PA2"
        bp = pa_get_nested(cfg,"validation.detectors.burst.params");
        e23 = pa_detect_E2E3(x, round(Fs), ...
            double(bp.power_smoothing_s), ...
            double(bp.refractory_s), ...
            double(bp.thresholds.hi_mad_k), ...
            double(bp.thresholds.lo_mad_k));
        if ~isempty(e23.rise_idx) && ~isempty(e23.fall_idx)
            a = e23.rise_idx(1);
            b = e23.fall_idx(end);
            mask(max(1,a):min(W,b)) = true;
        end

    elseif any(string(pa) == ["PA3","PA4"])
        snr_quiet = vr.proc.snr_quiet_db;
        smooth_s  = double(pa_get_nested(cfg,"validation.detectors.burst.params.power_smoothing_s"));
        close_s   = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
        occ_k     = double(pa_get_nested(cfg,"validation.detectors.burst.params.thresholds.occ_sigma_k"));

        occ = pa_detect_occupancy_from_quiet(x, Fs, snr_quiet, smooth_s, occ_k, close_s, 0);
        mask = occ.mask;

    elseif string(pa) == "PA8"
        if isfield(vr,"det") && isfield(vr.det,"repeat") && ...
           isfield(vr.det.repeat,"intervals") && ~isempty(vr.det.repeat.intervals)
            iv = vr.det.repeat.intervals;
            a = iv(1,1);
            b = iv(end,2);
            a = max(1,min(W,a));
            b = max(1,min(W,b));
            if b >= a
                mask(a:b) = true;
            end
        end
    end

    close_s = double(pa_get_nested(cfg,"validation.detectors.burst.mask_close_s"));
    kclose = max(1, round(close_s * Fs));
    mask = pa_mask_close(mask, kclose);

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
    yy = max(env) * 0.9;
    plot(tms(mask), yy*ones(sum(mask),1), ".", "MarkerSize", 2);

    if string(pa) == "PA8"
        if isfield(vr,"det") && isfield(vr.det,"repeat") && ...
           isfield(vr.det.repeat,"intervals") && ~isempty(vr.det.repeat.intervals)
            iv = vr.det.repeat.intervals;
            for r = 1:size(iv,1)
                a = iv(r,1);
                b = iv(r,2);
                xline(tms(a), "b-");
                xline(tms(b), "b-");
            end
        end
    end

    grid on;
    xlabel("Time (ms)");
    ylabel("|x|^2");

    ttl = sprintf("Zigbee %s | valid=%d | %s", pa, vr.valid, vr.reject_reason);
    if ~isempty(vr_alt)
        ttl = ttl + sprintf(" | alt_valid=%d (%s)", vr_alt.valid, vr_alt.reject_reason);
    end
    title(ttl, "Interpreter","none");

    nexttile;
    win = hann(nfft,"periodic");
    [S,F,T] = spectrogram(x, win, nfft-hop, nfft, Fs, "centered");
    imagesc(T*1e3, F/1e6, 10*log10(abs(S).^2 + 1e-12));
    axis xy;
    xlabel("Time (ms)");
    ylabel("Freq (MHz)");
    title("Spectrogram (dB)");
    colorbar;

    nexttile;
    plot(fj.bin_trace, "-");
    grid on;
    xlabel("STFT frame");
    ylabel("Dominant bin state (1..nbins)");
    title(sprintf("freq.jump.count=%d", fj.count), "Interpreter","none");

    exportgraphics(f, out_png);
    close(f);
end