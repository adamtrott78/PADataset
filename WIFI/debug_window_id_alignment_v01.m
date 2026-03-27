function debug_window_id_alignment_v01()
    wifi_root = fileparts(mfilename("fullpath"));

    PAs = ["PA2","PA3","PA4","PA8"];
    K = 10; % number of OTA windows to test per PA

    cfg = pa_load_cfg("starter_ota12.json");
    nfft = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.nfft"));
    hop  = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.hop"));
    nb   = double(pa_get_nested(cfg,"validation.detectors.stationarity.params.nbins"));

    for pa = PAs
        % --- load OTA ---
        f_ota = fullfile(wifi_root, "pilot_out_v01", "data_ota", sprintf("ota_rx_S01_%s.mat", pa));
        So = load(f_ota, "Xrx_all", "meta_rx");
        Xo = So.Xrx_all; Mo = So.meta_rx;

        Fs = double(pa_get_nested(cfg, "rates.fs_hz")); % use cfg Fs (12.5e6)
        No = size(Xo,2);

        % --- load digital (as-tx preferred) ---
        [Xd, Md] = load_digital_pack(wifi_root, pa);
        dig_ids = arrayfun(@(m) double(m.window_id), Md);

        fprintf("\n=== %s alignment check ===\n", pa);
        for i = 1:min(K,No)
            wid_o = double(Mo(i).window_id);
            xo = pa_preprocess_ota_basic(Xo(:,i));
            vo = feat_stft_logmag(xo, Fs, nfft, hop, nb);

            % search near expected window_id first (cheap)
            cand = find(abs(dig_ids - wid_o) <= 50);
            if isempty(cand), cand = 1:numel(dig_ids); end

            best_s = -inf; best_j = 1;
            for jj = cand(:).'
                xd = pa_preprocess_ota_basic(Xd(:,jj));
                vd = feat_stft_logmag(xd, Fs, nfft, hop, nb);
                s = (vo.'*vd) / (norm(vo)*norm(vd) + 1e-12);
                if s > best_s
                    best_s = s; best_j = jj;
                end
            end

            wid_d = dig_ids(best_j);
            fprintf("OTA idx=%3d wid=%3d  -> best DIG idx=%3d wid=%3d  sim=%.3f  delta(wid)=%+d\n", ...
                i, wid_o, best_j, wid_d, best_s, (wid_d - wid_o));
        end
    end
end

function [X, meta] = load_digital_pack(wifi_root, pa)
    f1 = fullfile(wifi_root, "pilot_out_v01", "data_dig_as_tx12p5", sprintf("pilot_S01_%s.mat", pa));
    f2 = fullfile(wifi_root, "pilot_out_v01", "data",              sprintf("pilot_S01_%s.mat", pa));
    if isfile(f1), f = f1; else, f = f2; end
    S = load(f);
    if isfield(S,"Xsig_all"), X = S.Xsig_all; else, X = S.X; end
    meta = S.meta;
end

function v = feat_stft_logmag(x, Fs, nfft, hop, nb)
    B = pa_stft_bins32(x, nfft, hop, nb);      % [nb x T], nonnegative
    v = log(double(B) + 1e-12);
    v = v(:);
    v = v - mean(v);
end