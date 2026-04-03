function inspect_tape_ranges_v01()
%INSPECT_TAPE_RANGES_V02 Inspect arbitrary ranges from tx_tape and ota_tape
% using the EXACT same plotting style as rx_reslice plot_pair_dig_vs_ota_v04().
%
% Put this file in WIFI/ and run:
%   inspect_tape_ranges_v02
%
% Edit the "cases" section to change start indices / lengths.

    this = fileparts(mfilename("fullpath"));
    addpath(fullfile(this,"common"));

    % --------- load TX tape ---------
    tx_file = fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat");
    assert(isfile(tx_file), "Missing TX file: %s", tx_file);
    TX = load(tx_file, "tx_tape", "tx_params");
    tx_tape = TX.tx_tape(:);
    p = TX.tx_params;

    % --------- load OTA tape ---------
    ota_file = fullfile(this,"pilot_out_v01","ota_rx_tape_v03","ota_tape_S01_v03.mat");
    assert(isfile(ota_file), "Missing OTA file: %s", ota_file);
    OT = load(ota_file, "x_tape", "rx_cfg");
    x_tape = OT.x_tape(:);
    rx_cfg = OT.rx_cfg;

    Fs_tx  = double(rx_cfg.Fs); % use RX Fs for both unless you have a separate TX Fs saved
    Fs_ota = double(rx_cfg.Fs);

    % record length (useful for picking default ranges)
    Lrec = double(p.frameLen + p.W + p.guardN);

    fprintf("\nTX len=%d | OTA len=%d | Fs=%.6f MS/s | frameLen=%d | W=%d | guardN=%d | Lrec=%d\n\n", ...
        numel(tx_tape), numel(x_tape), Fs_ota/1e6, p.frameLen, p.W, p.guardN, Lrec);

    % ===================== USER CONTROLS =====================
    % Each case produces ONE PNG: (TX segment) vs (OTA segment)
    %
    % Start indices are MATLAB 1-based.
    %
    % Default "len" is 1 record (Lrec). Change to 5*Lrec if you want.
    %
    % For your loop:
    %   RELOCK try | k=7000001
    %   RELOCK try | k=6823281
    %
    % If you believe TX/OTA are roughly aligned but offset by ~100k, you can
    % set tx_start = ota_start - 100000 (clamped).
    %
        cases = [
        struct("tag","last_good_k6300001", ...
               "tx_start", 6300001, ...
               "ota_start", 6300001, ...
               "len", Lrec);
    
        struct("tag","first_fail_k7000001", ...
               "tx_start", 7000001, ...
               "ota_start", 7000001, ...
               "len", Lrec);
    
        struct("tag","first_fail_wide_k7000001", ...
               "tx_start", 7000001, ...
               "ota_start", 7000001, ...
               "len", 3*Lrec);
    
        struct("tag","after_fail_k7700001", ...
               "tx_start", 7700001, ...
               "ota_start", 7700001, ...
               "len", Lrec);
    
        struct("tag","context_k6650001", ...
               "tx_start", 6650001, ...
               "ota_start", 6650001, ...
               "len", 4*Lrec)
    ];
    % =========================================================

    out_dir = fullfile(this,"pilot_out_v01","evidence_pack_ota_v03","tape_inspect");
    if ~exist(out_dir,"dir"), mkdir(out_dir); end

    for ci = 1:numel(cases)
        C = cases(ci);

        [x_d, ktd0, ktd1] = slice_safe(tx_tape, C.tx_start, C.len);
        [x_o, kto0, kto1] = slice_safe(x_tape,  C.ota_start, C.len);

        fprintf("CASE %d/%d: %s\n", ci, numel(cases), C.tag);
        fprintf("  TX  [%d .. %d]  (N=%d)\n", ktd0, ktd1, numel(x_d));
        fprintf("  OTA [%d .. %d]  (N=%d)\n", kto0, kto1, numel(x_o));

        out_png = fullfile(out_dir, sprintf("TAPE_%s_tx%d_ota%d_N%d.png", ...
                              C.tag, ktd0, kto0, min(numel(x_d), numel(x_o))));

        % EXACT plotting layout from rx_reslice (copied verbatim below)
        plot_pair_dig_vs_ota_v04(C.tag, x_d, Fs_tx, x_o, Fs_ota, out_png);

        fprintf("  wrote: %s\n\n", out_png);
    end
end

function [seg, lo, hi] = slice_safe(x, start_k, len)
    x = x(:);
    start_k = max(1, round(double(start_k)));
    len = max(1, round(double(len)));
    lo = min(numel(x), start_k);
    hi = min(numel(x), lo + len - 1);
    seg = x(lo:hi);
end

% ================= EXACT COPY of your plotter =================
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