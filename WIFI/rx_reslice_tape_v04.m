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
    k = 1;
    Lrec = p.frameLen + p.W + p.guardN;

    % skip start-sync frames at beginning (known count)
    k = 1 + p.N_start_frames * p.frameLen;

    stop_seen = false;

    while (k + p.frameLen + p.W - 1) <= numel(x_tape)
        ph = x_tape(k : k+p.frameLen-1);

        % quick verify preamble is present near start of PH frame
        r = pa_corr_ratio_v03(ph(1:p.Lpre), sync.win_preamble);
        if r < 8
            % try small local re-lock (±0.25 frame)
            [k2, ok] = local_relock(x_tape, k, p, sync);
            if ~ok
                k = k + Lrec; % give up on this record, jump forward
                continue;
            end
            k = k2;
            ph = x_tape(k : k+p.frameLen-1);
        end

        % decode header from PH frame
        hdr_samp = ph(p.Lpre + (1:p.Lhdr));
        [pa_id, wid, seq, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);

        if ~crc_ok
            % CRC fail: advance one record and continue (or could scan forward)
            k = k + Lrec;
            continue;
        end

        if pa_id == 15 && wid == 65535
            stop_seen = true;
            fprintf("STOP header found at k=%d\n", k);
            break;
        end

        pa = id_to_pa(pa_id);
        if pa == ""
            k = k + Lrec;
            continue;
        end

        payload = x_tape(k+p.frameLen : k+p.frameLen+p.W-1);

        c = counts.(char(pa)) + 1;
        counts.(char(pa)) = c;
        X.(char(pa))(:,c) = payload;

        meta = struct();
        meta.schema_version = "ota_v03";
        meta.session_id = 1;
        meta.tape_id = 1;
        meta.segment_id = 0;
        meta.window_id = uint16(wid);
        meta.pa_type = char(pa);
        meta.fs_hz = rx_cfg.Fs;
        meta.window_length_s = p.W / rx_cfg.Fs;
        meta.seq = uint16(seq);
        meta.k_ph = int64(k);
        M.(char(pa))(c) = meta;

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

function [k2, ok] = local_relock(x, k, p, sync)
    ok = false; k2 = k;
    win = round(0.25 * p.frameLen);
    a = max(1, k-win);
    b = min(numel(x), k+win+p.frameLen-1);
    buf = x(a:b);

    % correlate the preamble against buf (decimate for speed)
    ds = 10;
    bd = double(buf(1:ds:end));
    pd = double(sync.win_preamble(1:ds:end));

    nfft = 2^nextpow2(numel(bd)+numel(pd)-1);
    c = abs(ifft(fft(bd,nfft).*fft(conj(flipud(pd)),nfft)));
    c = c(numel(pd):numel(pd)+numel(bd)-1);

    [pk, idx] = max(c);
    med = median(c)+1e-12;
    ratio = pk/med;
    if ratio < 12, return; end

    k0d = idx;
    k0 = a + (k0d-1)*ds;     % approx
    k2 = k0; ok = true;
end

function pa = id_to_pa(pa_id)
    switch uint8(pa_id)
        case 2, pa = "PA2";
        case 3, pa = "PA3";
        case 4, pa = "PA4";
        case 8, pa = "PA8";
        otherwise, pa = "";
    end
end

function [x_d, Fs_d, ok] = load_digital_by_window_id(wifi_root, pa, wid)
    f = fullfile(wifi_root, "pilot_out_v01", "data", sprintf("pilot_S01_%s.mat", pa));
    if ~isfile(f), x_d=[]; Fs_d=[]; ok=false; return; end
    S = load(f,"Xsig_all","meta");
    ids = arrayfun(@(m) double(m.window_id), S.meta);
    j = find(ids==wid, 1, "first");
    if isempty(j), x_d=[]; Fs_d=[]; ok=false; return; end
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