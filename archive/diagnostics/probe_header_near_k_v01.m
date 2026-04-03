function probe_header_near_k_v01()
    this = fileparts(mfilename("fullpath"));
    addpath(fullfile(this,"common"));

    T = load(fullfile(this,"pilot_out_v01","ota_rx_tape_v03","ota_tape_S01_v03.mat"), "x_tape", "rx_cfg");
    S = load(fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat"), "tx_params", "sync");

    x = T.x_tape(:);
    p = S.tx_params;
    sync = S.sync;

    k0 = 7000001;
    ks = [k0-2*p.frameLen : 5000 : k0+3*p.frameLen];

    fprintf("Probe around k0=%d\n", k0);
    fprintf("      k      r       crc   pa_id   wid    seq\n");

    for k = ks
        if k < 1 || (k + p.frameLen + p.W - 1) > numel(x), continue; end

        ph = x(k : k+p.frameLen-1);
        r = pa_corr_ratio_v03(ph(1:p.Lpre), sync.win_preamble);

        hdr_samp = ph(p.Lpre + (1:p.Lhdr));
        [pa_id, wid, seq, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);

        if r >= 6 || crc_ok
            fprintf("%8d  %6.2f    %d    %5d  %5d  %5d\n", ...
                k, r, crc_ok, double(pa_id), double(wid), double(seq));
        end
    end
end