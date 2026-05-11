function make_png_pairs_from_spliced_v01()
    P = pa_paths();
%MAKE_PNG_PAIRS_FROM_SPLICED_V01 Create DIG vs OTA PNG pairs by window_id.
%
% Reads:
%   pilot_out_v01/data_ota_v03_spliced/ota_rx_S01_PA*.mat   (Xrx_all, meta_rx)
%   pilot_out_v01/data/pilot_S01_PA*.mat                   (Xsig_all, meta)
%
% Writes:
%   pilot_out_v01/evidence_pack_ota_v03/png_pairs/DIG_vs_OTA_<PA>_wXXXX.png

    addpath(P.txrx);

    in_ota = P.data_wifi_spliced_v05;
    in_dig = P.data_wifi_pilot;
    out_png = P.results_rx_resplice_v05_png_pairs;
    if exist(out_png,"dir"), rmdir(out_png,"s"); end
    mkdir(out_png);

    cfg = pa_load_cfg(fullfile(P.config,"starter_ota12.json")); % only used for nfft/hop; ok if you change later

    PAs = ["PA2","PA3","PA4","PA8"];

    % load digital once per PA, build map: window_id -> column index
    dig = struct();
    for pa = PAs
        f = fullfile(in_dig, sprintf("pilot_S01_%s.mat", pa));
        assert(isfile(f), "Missing digital: %s", f);
        S = load(f,"Xsig_all","meta");
        ids = arrayfun(@(m) double(m.window_id), S.meta);
        dig.(char(pa)).X = S.Xsig_all;
        dig.(char(pa)).Fs = double(S.meta(1).fs_hz);
        dig.(char(pa)).ids = ids;

        % fast lookup
        dig.(char(pa)).id2col = containers.Map('KeyType','double','ValueType','double');
        for k = 1:numel(ids)
            dig.(char(pa)).id2col(ids(k)) = k;
        end
    end

    % now iterate OTA and write pngs
    for pa = PAs
        f = fullfile(in_ota, sprintf("ota_rx_S01_%s.mat", pa));
        assert(isfile(f), "Missing OTA spliced: %s", f);
        T = load(f,"Xrx_all","meta_rx","rx_cfg");
        Xo = T.Xrx_all;
        Mo = T.meta_rx;
        Fs_o = double(Mo(1).fs_hz);

        N = size(Xo,2);
        fprintf("PNG pairs %s | %d windows | Fs_o=%.6f MS/s\n", pa, N, Fs_o/1e6);

        for i = 1:N
            wid = double(Mo(i).window_id);

            if ~isKey(dig.(char(pa)).id2col, wid)
                % if you want, you can log missing IDs here
                continue;
            end
            j = dig.(char(pa)).id2col(wid);

            xd = dig.(char(pa)).X(:,j);
            Fs_d = dig.(char(pa)).Fs;

            xo = Xo(:,i);

            out = fullfile(out_png, sprintf("DIG_vs_OTA_%s_w%04d.png", pa, wid));
            plot_pair_dig_vs_ota_local(cfg, pa, xd, Fs_d, xo, Fs_o, out);
        end
    end

    fprintf("Done. PNGs in: %s\n", out_png);
end

% ---------- plotting: same as your preferred style ----------
function plot_pair_dig_vs_ota_local(cfg, pa, x_d, Fs_d, x_o, Fs_o, out_png)
    x_d = x_d(:); x_o = x_o(:);

    nfft = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.nfft"));
    hop  = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.hop"));
    win  = hann(nfft,"periodic");

    td = (0:numel(x_d)-1)/Fs_d*1e3;
    to = (0:numel(x_o)-1)/Fs_o*1e3;

    f = figure("Visible","off","Color","w","Position",[100 100 1700 950]);
    tiledlayout(2,2,"Padding","compact","TileSpacing","compact");

    % DIG spectrogram
    nexttile;
    [Sd,Fd,Td2] = spectrogram(x_d, win, nfft-hop, nfft, Fs_d, "centered");
    imagesc(Td2*1e3, Fd/1e6, 10*log10(abs(Sd).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title(pa+" (DIG)"); colorbar;

    % OTA spectrogram
    nexttile;
    [So,Fo,To2] = spectrogram(x_o, win, nfft-hop, nfft, Fs_o, "centered");
    imagesc(To2*1e3, Fo/1e6, 10*log10(abs(So).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)");
    title(pa+" (OTA)"); colorbar;

    % DIG waveform I/Q
    nexttile;
    plot(td, real(x_d)); hold on;
    plot(td, imag(x_d), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q");
    title("Waveform (DIG)");
    legend("I = real(x)","Q = imag(x)","Location","northeast");

    % OTA waveform I/Q
    nexttile;
    plot(to, real(x_o)); hold on;
    plot(to, imag(x_o), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q");
    title("Waveform (OTA)");
    legend("I = real(x)","Q = imag(x)","Location","northeast");

    exportgraphics(f, out_png);
    close(f);
end