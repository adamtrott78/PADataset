function audit_pilot_lengths_v01()
    this = fileparts(mfilename("fullpath"));
    data_root = fullfile(this,"pilot_out_v01","data");
    PAs = ["PA8","PA2","PA3","PA4"];

    for pa = PAs
        f = fullfile(data_root, sprintf("pilot_S01_%s.mat", pa));
        S = load(f, "Xsig_all", "meta");

        nSamp = size(S.Xsig_all, 1);
        nWin  = size(S.Xsig_all, 2);

        ids = arrayfun(@(m) double(m.window_id), S.meta);
        fprintf("%s | rows=%d | cols=%d | wid[min,max]=[%d,%d]\n", ...
            pa, nSamp, nWin, min(ids), max(ids));
    end
end