function rx_pilot_all_pas_usrp_v01(ip, fc_hz, rx_gain_db)
%RX_PILOT_ALL_PAS_USRP_V01 Receive OTA pilot stream and save windows by PA.
% Companion to tx_pilot_all_pas_usrp_v01 (PA2->PA3->PA4->PA8).
%
% OUTPUT:
%   ota_rx_out_v01/data/ota_rx_S01_PA2.mat  (Xrx_all, meta_rx, rx_cfg)
%   ota_rx_out_v01/data/ota_rx_S01_PA3.mat
%   ota_rx_out_v01/data/ota_rx_S01_PA4.mat
%   ota_rx_out_v01/data/ota_rx_S01_PA8.mat
%
% Usage:
%   rx_pilot_all_pas_usrp_v01("192.168.10.2", 2.437e9, 20);

    % ---------------- fixed v0.1 constants (must match TX) ----------------
    Fs = 20e6;
    W  = 400000;          % 20ms @ 20MS/s
    session_id = 1;
    tape_id    = 1;

    % TX script settings (must match)
    preroll_s = 0.050;    % zeros before first payload
    guard_s   = 0.010;    % zeros between windows
    guardN    = round(guard_s * Fs);

    % USRP N210 clocking at 20 MS/s
    mcr = 100e6;
    decim = mcr / Fs;
    if abs(decim - round(decim)) > 1e-9
        error("MasterClockRate/Fs must be integer. Got %g", decim);
    end
    decim = round(decim);

    % Receiver framing
    frameLen = 4000;      % same as TX (not required but convenient)
    if mod(W,frameLen) ~= 0
        error("frameLen must divide W exactly (for sanity).");
    end

    % Where to read "how many windows per PA" from
    data_root = fullfile("pilot_out_v01","data");
    PAs = ["PA2","PA3","PA4","PA8"];

    % Output root
    out_root = fullfile("ota_rx_out_v01");
    out_data = fullfile(out_root,"data");
    if ~exist(out_data,"dir"), mkdir(out_data); end

    % ---------------- load TX meta to know counts + tx window_ids ----------------
    txN = struct();   % txN.PA2 = N, etc
    txIDs = struct(); % txIDs.PA2 = sorted window_id list

    for pa = PAs
        f = fullfile(data_root, sprintf("pilot_S%02d_%s.mat", session_id, pa));
        if ~isfile(f), error("Missing pilot TX file: %s", f); end
        S = load(f,"meta","Xsig_all");
        N = size(S.Xsig_all,2);
        if numel(S.meta) ~= N, error("Meta mismatch in %s", f); end
        ids = zeros(1,N);
        for i = 1:N, ids(i) = S.meta(i).window_id; end
        ids = sort(ids,"ascend");
        txN.(char(pa)) = N;
        txIDs.(char(pa)) = ids;
    end

    fprintf("RX plan: PA2=%d, PA3=%d, PA4=%d, PA8=%d windows\n", ...
        txN.PA2, txN.PA3, txN.PA4, txN.PA8);

    % ---------------- build receiver ----------------
    rx = comm.SDRuReceiver( ...
        "Platform", "N200/N210/USRP2", ...
        "IPAddress", ip, ...
        "CenterFrequency", fc_hz, ...
        "Gain", rx_gain_db, ...
        "MasterClockRate", mcr, ...
        "DecimationFactor", decim, ...
        "SamplesPerFrame", frameLen, ...
        "OutputDataType", "single", ...
        "ChannelMapping", 1);

    rx_cfg = struct( ...
        "ip", ip, ...
        "fc_hz", fc_hz, ...
        "rx_gain_db", rx_gain_db, ...
        "Fs_hz", Fs, ...
        "MasterClockRate", mcr, ...
        "DecimationFactor", decim, ...
        "SamplesPerFrame", frameLen, ...
        "W", W, ...
        "guardN", guardN, ...
        "preroll_s", preroll_s, ...
        "guard_s", guard_s);

    fprintf("RX START | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | Fs=%.3f MS/s\n", ...
        ip, fc_hz/1e9, rx_gain_db, Fs/1e6);
    fprintf("Start RX first, then run TX script. RX will auto-align on first payload.\n");

    % ---------------- streaming state ----------------
    stash = complex(zeros(0,1,"single"), zeros(0,1,"single"));
    stash_overruns = 0;
    g_samp = int64(0);  % global sample counter for all received samples (excluding stash management)

    % helper: pull one frame and append to stash
    function pull_frame()
        % NOTE: comm.SDRuReceiver returns [data, len, overrun] in current support pkgs
        [y, len, overrun] = rx(); %#ok<ASGLU>
        if overrun, stash_overruns = stash_overruns + 1; end
        if len > 0
            y = y(1:len);
            stash = [stash; y]; %#ok<AGROW>
            g_samp = g_samp + int64(len);
        end
    end

    % helper: read exactly N samples (single complex), deterministic (uses stash)
    function [xN, over_ct, start_g] = readN(N)
        N = int64(N);
        over_ct = 0;
        start_g = g_samp - int64(numel(stash)) + 1; % g-index of stash(1)
        while int64(numel(stash)) < N
            pull_frame();
            over_ct = stash_overruns; %#ok<NASGU>
        end
        xN = stash(1:double(N));
        stash = stash(double(N+1):end);
        start_g = start_g; %#ok<NASGU>
        over_ct = stash_overruns;
    end

    % ---------------- initial alignment: find first payload start ----------------
    % We expect TX preroll to be "quiet" (mostly noise). Detect first sustained power rise.
    base_frames = max(10, ceil(0.020*Fs/frameLen));  % ~20ms baseline
    p_hist = zeros(base_frames,1);
    got = 0;

    while got < base_frames
        pull_frame();
        if numel(stash) >= frameLen
            blk = stash(1:frameLen);
            stash = stash(frameLen+1:end);
            got = got + 1;
            p_hist(got) = mean(abs(double(blk)).^2);
        end
    end

    medp = median(p_hist);
    madp = median(abs(p_hist - medp)) + 1e-18;
    thr  = medp + 10*madp;          % deterministic threshold
    consec_need = 3;

    fprintf("Align: baseline med=%.3e mad=%.3e thr=%.3e\n", medp, madp, thr);

    consec = 0;
    align_found = false;

    % Search forward for first "on" region
    while ~align_found
        pull_frame();
        if numel(stash) < frameLen, continue; end

        blk = stash(1:frameLen);
        stash = stash(frameLen+1:end);

        p = mean(abs(double(blk)).^2);
        if p > thr
            consec = consec + 1;
        else
            consec = 0;
        end

        if consec >= consec_need
            % We are in the first payload region. Now refine within a small buffer:
            % Grab extra samples and find first sample where smoothed power crosses a threshold.
            refineN = int64(5*frameLen); % 5 frames = 20k samples = 1ms
            [buf, ~, ~] = readN(refineN);

            % build refined threshold from baseline sigma estimate
            % Use simple power smoothing like your burst detector (0.1ms)
            Ms = max(1, round(0.0001*Fs));
            pw = filter(ones(Ms,1)/Ms, 1, abs(double(buf)).^2);
            % threshold at baseline + 6*MAD (same spirit as E2/E3)
            thr_samp = medp + 6*madp;

            k0 = find(pw > thr_samp, 1, "first");
            if isempty(k0)
                % if refine failed, keep searching
                continue;
            end

            % Discard samples before k0 so the next sample read starts at payload onset
            buf = buf(k0:end);
            stash = [buf; stash]; %#ok<AGROW>

            rx_cfg.align = struct( ...
                "baseline_med_pow", medp, ...
                "baseline_mad_pow", madp, ...
                "frame_thr_pow", thr, ...
                "sample_thr_pow", thr_samp, ...
                "refine_k0", k0);

            fprintf("Align: payload onset found at refine_k0=%d samples into refine buffer.\n", k0);
            align_found = true;
        end
    end

    % ---------------- capture windows in TX order ----------------
    for pa = PAs
        N = txN.(char(pa));
        Xrx_all = complex(zeros(W, N, "single"), zeros(W, N, "single"));
        meta_rx = repmat(struct(), 1, N);

        fprintf("CAPTURE %s (%d windows)\n", pa, N);

        for i = 1:N
            tx_win_id = txIDs.(char(pa))(i);

            % read window
            [xw, over_ct, start_g] = readN(W);
            Xrx_all(:,i) = xw;

            meta_rx(i).schema_version = pa_get_nested(pa_load_cfg("starter.json"),"schema_version");
            meta_rx(i).session_id = session_id;
            meta_rx(i).tape_id = tape_id;
            meta_rx(i).segment_id = 0;              % OTA: not using virtual segments here
            meta_rx(i).window_id = tx_win_id;       % preserve TX identity
            meta_rx(i).pa_type = char(pa);
            meta_rx(i).fs_hz = Fs;
            meta_rx(i).window_length_s = W/Fs;
            meta_rx(i).rx_start_sample_global = int64(start_g);
            meta_rx(i).rx_overrun_count_total = int64(over_ct);

            % discard guard
            [~, ~, ~] = readN(guardN);

            if mod(i,25)==0 || i==N
                fprintf("  %s %d/%d | underrun/overrun_total=%d\n", pa, i, N, stash_overruns);
            end
        end

        out_file = fullfile(out_data, sprintf("ota_rx_S%02d_%s.mat", session_id, pa));
        save(out_file, "Xrx_all", "meta_rx", "rx_cfg", "-v7");
        fprintf("Saved %s\n", out_file);
    end

    release(rx);
    fprintf("RX DONE | total_overruns=%d\n", stash_overruns);
end