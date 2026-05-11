function [Xsig, meta, sched] = bt_gen_windows_pa1_stream(cfg, session_id, tape_id, segment_id, plan)
%BT_GEN_WINDOWS_PA1_STREAM Bluetooth PA1 = survey/probing scan (no revisits within a scan sweep).
% Segment-based schedule; windows are cropped views of the scan.

    Fs = int64(plan.Fs);
    W  = int64(plan.W);
    starts = int64(plan.starts(:));
    M = int64(numel(starts));
    ends = starts + W - 1;

    if isfield(plan,"L")
        L = int64(plan.L);
    else
        L = max(ends);
    end

    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord)); invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % PA1 params
    dwell_rng = double(pa_get_nested(cfg,"pas.PA1.params.dwell_s"));
    scan_rng  = double(pa_get_nested(cfg,"pas.PA1.params.scan_set_size"));

    og = pa_get_nested(cfg,"pas.PA1.params.offset_grid_hz");
    gmin = double(og.min_hz); gmax = double(og.max_hz); gstep = double(og.step_hz);
    grid = (ceil(gmin/gstep):floor(gmax/gstep)) * gstep;
    grid = grid(:);
    assert(~isempty(grid), "PA1 offset_grid_hz empty after limits");

    btCfg = bt_make_ble_cfg(cfg);

    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA1_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    L_need = min(L, max(endsS));

    t = int64(1);
    pkt_idx = int64(1);
    wi = 1;
    phi = 0;

    % schedule logs (block-level)
    blk_starts = zeros(0,1);
    blk_lens   = zeros(0,1);
    blk_df_hz  = zeros(0,1);
    blk_scanid = zeros(0,1);

    scan_id = 0;

    while t <= L_need && wi <= M
        scan_id = scan_id + 1;
        Kscan = randi(rs, [round(scan_rng(1)), round(scan_rng(2))], 1, 1);
        assert(numel(grid) >= Kscan, "Offset grid too small for scan_set_size=%d", Kscan);

        dir = 1; if rand(rs) < 0.5, dir = -1; end
        if dir == 1
            i0 = randi(rs, [1, numel(grid)-Kscan+1], 1, 1);
            idxs = i0:(i0+Kscan-1);
        else
            i0 = randi(rs, [Kscan, numel(grid)], 1, 1);
            idxs = i0:-1:(i0-Kscan+1);
        end
        scan_offsets = grid(idxs);

        for k = 1:numel(scan_offsets)
            if t > L_need || wi > M, break; end

            dwell_s = dwell_rng(1) + (dwell_rng(2)-dwell_rng(1)) * rand(rs);
            ds = int64(max(1, round(dwell_s * double(Fs))));
            blk_end = t + ds - 1;
            if blk_end > L_need
                ds = L_need - t + 1;
                if ds <= 0, break; end
                blk_end = t + ds - 1;
            end

            df = double(scan_offsets(k));

            % generate dense BLE packets to fill ds
            x_blk = complex(zeros(0,1,"single"), zeros(0,1,"single"));
            while numel(x_blk) < double(ds)
                [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
                [x_pkt, ~] = bt_gen_packet(uint32(seed_payload), btCfg);
                x_blk = [x_blk; x_pkt]; %#ok<AGROW>
                pkt_idx = pkt_idx + 1;
            end
            x_blk = x_blk(1:double(ds));

            [x_blk, phi] = pa_mix_freq_offset_block(x_blk, double(Fs), df, phi);

            % advance past windows ending before this block
            while wi <= M && endsS(wi) < t
                wi = wi + 1;
            end

            % overlap copy into windows
            wj = wi;
            while wj <= M && startsS(wj) <= blk_end
                ovL = max(t, startsS(wj));
                ovR = min(blk_end, endsS(wj));
                if ovL <= ovR
                    b0 = ovL - t + 1;
                    b1 = ovR - t + 1;
                    w0 = ovL - startsS(wj) + 1;
                    w1 = ovR - startsS(wj) + 1;
                    XsigS(double(w0):double(w1), double(wj)) = XsigS(double(w0):double(w1), double(wj)) + x_blk(double(b0):double(b1));
                end
                wj = wj + 1;
            end

            blk_starts(end+1,1) = double(t); %#ok<AGROW>
            blk_lens(end+1,1)   = double(ds); %#ok<AGROW>
            blk_df_hz(end+1,1)  = df; %#ok<AGROW>
            blk_scanid(end+1,1) = double(scan_id); %#ok<AGROW>

            t = blk_end + 1;
        end
    end

    Xsig = XsigS(:, invord);

    sched = struct();
    sched.L_need = double(L_need);
    sched.block_starts_samp = blk_starts(:);
    sched.block_len_samp    = blk_lens(:);
    sched.block_df_hz       = blk_df_hz(:);
    sched.block_scan_id     = blk_scanid(:);

    % per-window meta (lightweight overlap selection)
    meta = repmat(struct(), 1, double(M));
    starts_plan = starts(:);
    ends_plan   = ends(:);

    blk_iv = [blk_starts, blk_starts + blk_lens - 1];

    for i = 1:double(M)
        a = double(starts_plan(i)); b = double(ends_plan(i));
        keep = blk_iv(:,1) <= b & blk_iv(:,2) >= a;

        meta(i).schema_version      = pa_get_nested(cfg,"schema_version");
        meta(i).session_id          = session_id;
        meta(i).tape_id             = tape_id;
        meta(i).segment_id          = segment_id;
        meta(i).window_id           = i;
        meta(i).pa_type             = "PA1";
        meta(i).protocol            = "bluetooth";
        meta(i).fs_hz               = double(Fs);
        meta(i).window_length_s     = double(pa_get_nested(cfg,"windowing.window_length_s"));
        meta(i).window_start_sample = double(starts_plan(i));
        meta(i).scan_blocks_in_window = sum(keep);
    end
end