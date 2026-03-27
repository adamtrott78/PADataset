function make_digital_as_tx12p5_v01()
% Make a "digital-as-transmitted" copy: same samples, updated fs_hz + window_length_s.
    wifi_root = fileparts(mfilename("fullpath"));
    in_root = fullfile(wifi_root,"pilot_out_v01","data");
    out_root = fullfile(wifi_root,"pilot_out_v01","data_dig_as_tx12p5");
    if ~exist(out_root,"dir"), mkdir(out_root); end

    Fs_tx = 12.5e6;        % if interp/decim=8 with mcr=100e6
    PAs = ["PA2","PA3","PA4","PA8"];

    for pa = PAs
        fin = fullfile(in_root, sprintf("pilot_S01_%s.mat", pa));
        S = load(fin, "Xsig_all", "meta");
        X = S.Xsig_all; meta = S.meta;

        for i = 1:numel(meta)
            meta(i).fs_hz = Fs_tx;
            meta(i).window_length_s = size(X,1)/Fs_tx;
        end

        fout = fullfile(out_root, sprintf("pilot_S01_%s.mat", pa));
        Xsig_all = X; %#ok<NASGU>  % keep canonical name used everywhere else
        save(fout, "Xsig_all", "meta", "-v7");
        fprintf("Wrote %s\n", fout);
    end
end