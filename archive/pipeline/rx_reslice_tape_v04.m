function rx_reslice_tape_v04()
%RX_RESLICE_TAPE_V04 Offline reslice: find per-window headers -> extract payload -> save per PA -> 40 PNGs.

    this = fileparts(mfilename("fullpath"));
    addpath(fullfile(this,"common"));

    tape_file = fullfile(this,"pilot_out_v01","ota_rx_tape_v03","ota_tape_S01_v03.mat");
    T = load(tape_file, "x_tape", "rx_cfg");
    x_tape = T.x_tape;
    rx_cfg = T.rx_cfg;

    tape_spec = fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat");
    S = load(tape_spec, "tx_params", "sync");
    p = S.tx_params;
    sync = S.sync;

    out_data = fullfile(this,"pilot_out_v01","data_ota_v03_spliced");
    if ~exist(out_data,"dir"), mkdir(out_data); end

    fprintf("RESLICE | tape=%d samples | Fs=%.6f MS/s | frameLen=%d\n", numel(x_tape), rx_cfg.Fs/1e6, p.frameLen);

    % storage
    PAs = ["PA2","PA3","PA4","PA8"];
    X = struct(); M = struct(); counts = struct();
    for pa = PAs
        X.(char(pa)) = complex(zeros(p.W, 400, "single"), zeros(p.W, 400, "single")); % oversized; trim later
        M.(char(pa)) = repmat(struct(), 1, 400);
        counts.(char(pa)) = 0;
    end

    % parsing
    Lrec = p.frameLen + p.W + p.guardN;

    % When we lose lock, do NOT jump a whole record. Scan forward a bit.
    scan_step = max(1, round(0.2 * p.frameLen));   % 20k if frameLen=100k

    % Find the first *valid* record anywhere in the tape:
    % (preamble present) AND (header CRC OK) AND (PA ID is one of PA2/3/4/8)
    [k, ok0, rr0] = find_first_record(x_tape, p, sync, 8);
    if ~ok0
        error("Start lock failed: no valid (preamble+CRC) record found in tape.");
    end
    fprintf("Start lock: k=%d | ratio=%.2f\n", k, rr0);
    
    % ---- progress counters ----
    t0 = tic; tPrint = tic;
    nIter = 0; nOK = 0; nScan = 0;
    relockTry = 0; relockFail = 0; nCRCFail = 0; nBadPA = 0;
    consecFail = 0;
    
    stop_seen = false;

    while (k + p.frameLen + p.W - 1) <= numel(x_tape)

        nIter = nIter + 1;

        if toc(tPrint) > 1.0
            fprintf("RESLICE prog | k=%d (%.1f%%) | ok=%d | scan=%d | crcFail=%d | relockFail=%d | badPA=%d | consecFail=%d | elapsed=%.1fs\n", ...
                k, 100*double(k)/double(numel(x_tape)), nOK, nScan, nCRCFail, relockFail, nBadPA, consecFail, toc(t0));
            tPrint = tic;
        end

        ph = x_tape(k : k+p.frameLen-1);

        % quick verify preamble is present near start of PH frame
        r = pa_corr_ratio_v03(ph(1:p.Lpre), sync.win_preamble);

        if r < 8
            relockTry = relockTry + 1;
            fprintf("RELOCK try | k=%d (%.1f%%) | r=%.2f\n", k, 100*double(k)/double(numel(x_tape)), r);
        
            [k2, ok, bestval] = local_relock(x_tape, k, p, sync); % updated signature below
        
            % Hard rule: relock must move FORWARD, otherwise we will oscillate forever
            if ~ok || k2 <= k
                relockFail = relockFail + 1;
                k = k + scan_step;
                continue;
            end
        
            fprintf("RELOCK ok  | k->%d (+%d) | bestval=%.3f\n", k2, k2-k, bestval);
            k = k2;
        
            if (k + p.frameLen + p.W - 1) > numel(x_tape), break; end
            ph = x_tape(k : k+p.frameLen-1);
        end

        % decode header from PH frame
        hdr_samp = ph(p.Lpre + (1:p.Lhdr));
        [pa_id, wid, seq, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);
        
        if ~crc_ok
            nCRCFail = nCRCFail + 1;
            consecFail = consecFail + 1;
            k = k + scan_step;
            nScan = nScan + 1;
            continue;
        end

        if pa_id == 15 && wid == 65535
            stop_seen = true;
            fprintf("STOP header found at k=%d\n", k);
            break;
        end

        pa = id_to_pa(pa_id);
        
        if pa == ""
            nBadPA = nBadPA + 1;
            consecFail = consecFail + 1;
            k = k + scan_step;
            nScan = nScan + 1;
            continue;
        end

        payload = x_tape(k+p.frameLen : k+p.frameLen+p.W-1);

        c = counts.(char(pa)) + 1;
        counts.(char(pa)) = c;
        X.(char(pa))(:,c) = payload;

        pa_key = char(pa); 

        meta = struct( ...
            "schema_version", "ota_v03", ...
            "session_id", 1, ...
            "tape_id", 1, ...
            "segment_id", 0, ...
            "window_id", uint16(wid), ...
            "pa_type", pa_key, ...
            "fs_hz", double(rx_cfg.Fs), ...
            "window_length_s", double(p.W) / double(rx_cfg.Fs), ...
            "seq", uint16(seq), ...
            "k_ph", int64(k) );
        
        % --- FIX: initialize M.(pa_key) with a real template (not struct()) ---
        if ~isfield(M, pa_key) || isempty(M.(pa_key)) || isempty(fieldnames(M.(pa_key)))
            % match whatever you used to preallocate X.(pa_key)
            if isfield(X, pa_key) && ~isempty(X.(pa_key))
                Nmax = size(X.(pa_key), 2);
            else
                Nmax = 1; % fallback
            end
            M.(pa_key) = repmat(meta, 1, Nmax);
        end
        
        M.(pa_key)(c) = meta;
        
        nOK = nOK + 1;
        consecFail = 0;

        k = k + Lrec;
    end

    % save per PA
    for pa = PAs
        c = counts.(char(pa));
        Xrx_all = X.(char(pa))(:,1:c);
        meta_rx = M.(char(pa))(1:c);

        out = fullfile(out_data, sprintf("ota_rx_S01_%s.mat", pa));
        save(out, "Xrx_all", "meta_rx", "rx_cfg", "-v7.3");
        fprintf("Saved %s | %d windows\n", out, c);
    end

    % make 40 pngs (10 per PA)
    png_root = fullfile(this,"pilot_out_v01","evidence_pack_ota_v03","png");
    if exist(png_root,"dir"), rmdir(png_root,"s"); end
    mkdir(png_root);

    for pa = PAs
        c = counts.(char(pa));
        K = min(10, c);
        for i = 1:K
            wid = double(M.(char(pa))(i).window_id);
            x_o = X.(char(pa))(:,i);

            [x_d, Fs_d, ok] = load_digital_by_window_id(this, pa, wid);
            if ~ok, continue; end

            outpng = fullfile(png_root, sprintf("DIG_vs_OTA_%s_w%04d.png", pa, wid));
            plot_pair_dig_vs_ota_v04(pa, x_d, Fs_d, x_o, rx_cfg.Fs, outpng);
        end
    end

    fprintf("RESLICE DONE | stop_seen=%d | PNGs: %s\n", stop_seen, png_root);
end

function [k0, ok, best_r] = find_first_record(x_tape, p, sync, r_thr)
% Scan the tape for the first frame that looks like a real record:
% preamble present AND header CRC OK AND PA ID is valid.

    ok = false; k0 = 1; best_r = 0;

    % try a few candidate alignments in case tape starts mid-frame
    offs = unique([ ...
        1, ...
        1 + round(p.frameLen/4), ...
        1 + round(p.frameLen/2), ...
        1 + round(3*p.frameLen/4) ]);

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;

    for o = offs
        for k = o : p.frameLen : kmax
            ph = x_tape(k : k+p.frameLen-1);

            r = pa_corr_ratio_v03(ph(1:p.Lpre), sync.win_preamble);
            if r < r_thr
                continue;
            end

            hdr_samp = ph(p.Lpre + (1:p.Lhdr));
            [pa_id, ~, ~, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);
            if ~crc_ok
                continue;
            end

            pa = id_to_pa(pa_id);
            if pa == ""
                continue;
            end

            k0 = k;
            best_r = r;
            ok = true;
            return;
        end
    end
end

function [kbest, ratio] = refine_k_fullrate(x, k0, pre, R)
% Fast refine around k0 using one-shot FFT correlation in a small window.
% Returns kbest (1-based) and peak/median ratio inside refine window.

    pre = double(pre(:));
    Lp = numel(pre);

    a = max(1, k0 - R);
    b = min(numel(x) - Lp + 1, k0 + R);
    if b < a
        kbest = k0; ratio = 0; return;
    end

    % segment that contains all candidate alignments
    seg = double(x(a : b + Lp - 1));

    nfft = 2^nextpow2(numel(seg) + Lp - 1);
    C = abs(ifft(fft(seg, nfft) .* fft(conj(flipud(pre)), nfft)));

    % valid correlation positions correspond to candidate k in [a..b]
    C = C(Lp : Lp + (b - a));

    [pk, idx] = max(C);
    med = median(C) + 1e-12;
    ratio = pk / med;

    kbest = a + idx - 1;
end

function [k2, ok, bestval] = local_relock(x, k, p, sync)
% Forward-only relock:
%  - search around k, but only accept candidates >= k (prevents bouncing backward)
%  - after coarse FFT corr, do a small full-rate refine
%  - reject false peaks by requiring bestval >= min_corr

    ok = false; k2 = k; bestval = 0;

    win = round(3.0 * p.frameLen);     % search span
    a = max(1, k - win);
    b = min(numel(x), k + win + p.frameLen - 1);
    buf = x(a:b);

    % coarse correlation (decimated)
    ds = 10;
    bd = double(buf(1:ds:end));
    pd = double(sync.win_preamble(1:ds:end));

    nfft = 2^nextpow2(numel(bd) + numel(pd) - 1);
    c = abs(ifft(fft(bd,nfft) .* fft(conj(flipud(pd)),nfft)));
    c = c(numel(pd):numel(pd)+numel(bd)-1);

    med = median(c) + 1e-12;
    thr = 12 * med;

    idxs = find(c >= thr);
    if isempty(idxs), return; end

    % map to full-rate candidate k values
    kcand = a + (idxs-1)*ds;

    % IMPORTANT: forward-only candidates (prevents k oscillation)
    kcand = kcand(kcand >= k);
    if isempty(kcand), return; end

    % choose the earliest strong candidate (not the strongest anywhere)
    k0 = kcand(1);

    % refine near k0 (small window; fast)
    [kref, bestval] = refine_k_fullrate(x, k0, sync.win_preamble, 30);

    % quality gate: if we don't actually look like the preamble, reject
    min_corr = 0.25;
    if bestval < min_corr
        ok = false; k2 = k; return;
    end

    kmax = numel(x) - (p.frameLen + p.W) + 1;
    k2 = min(max(1, kref), kmax);

    ok = true;
end

function pa = id_to_pa(pa_id)
    switch double(pa_id)
        case 2, pa = "PA2";
        case 3, pa = "PA3";
        case 4, pa = "PA4";
        case 8, pa = "PA8";
        otherwise, pa = "";
    end
end

function [x_d, Fs_d, ok] = load_digital_by_window_id(wifi_root, pa, wid)
    f = fullfile(wifi_root, "pilot_out_v01", "data", sprintf("pilot_S01_%s.mat", pa));
    if ~isfile(f)
        x_d = [];
        Fs_d = [];
        ok = false;
        return;
    end

    S = load(f, "Xsig_all", "meta");
    ids = arrayfun(@(m) double(m.window_id), S.meta);
    j = find(ids == wid, 1, "first");

    if isempty(j)
        x_d = [];
        Fs_d = [];
        ok = false;
        return;
    end

    x_d = S.Xsig_all(:,j);
    Fs_d = double(S.meta(j).fs_hz);
    ok = true;
end

function plot_pair_dig_vs_ota_v04(pa, x_d, Fs_d, x_o, Fs_o, out_png)
    nfft = 1024; hop = 256;
    win = hann(nfft,"periodic");

    td = (0:numel(x_d)-1)/Fs_d*1e3;
    to = (0:numel(x_o)-1)/Fs_o*1e3;

    f = figure("Visible","off","Color","w","Position",[100 100 1700 950]);
    tiledlayout(2,2,"Padding","compact","TileSpacing","compact");

    nexttile;
    [Sd,Fd,Td2] = spectrogram(x_d, win, nfft-hop, nfft, Fs_d, "centered");
    imagesc(Td2*1e3, Fd/1e6, 10*log10(abs(Sd).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title(pa+" (DIG)"); colorbar;

    nexttile;
    [So,Fo,To2] = spectrogram(x_o, win, nfft-hop, nfft, Fs_o, "centered");
    imagesc(To2*1e3, Fo/1e6, 10*log10(abs(So).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title(pa+" (OTA)"); colorbar;

    nexttile;
    plot(td, real(x_d)); hold on; plot(td, imag(x_d), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q"); title("Waveform (DIG)");
    legend("I","Q","Location","northeast");

    nexttile;
    plot(to, real(x_o)); hold on; plot(to, imag(x_o), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q"); title("Waveform (OTA)");
    legend("I","Q","Location","northeast");

    exportgraphics(f, out_png);
    close(f);
end