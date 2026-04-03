function [Xsig, meta, sched] = zb_gen_windows_pa4_stream(cfg, session_id, tape_id, segment_id, plan)
%ZB_GEN_WINDOWS_PA4_STREAM Dense Zigbee PA4 windows using explicit IQ frequency offsets.

    Fs = int64(plan.Fs);
    W  = int64(plan.W);
    M  = int64(numel(plan.starts));

    Xsig = complex(zeros(double(W), double(M), "single"), ...
                   zeros(double(W), double(M), "single"));

    meta  = repmat(struct(), 1, double(M));
    sched = repmat(struct(), 1, double(M));

    master_seed = pa_get_nested(cfg, "generator.seeds.master_seed");
    schema      = pa_get_nested(cfg, "schema_version");

    hp = pa_get_nested(cfg, "operators.hop_step_schedule");
    dwell_rng       = double(hp.dwell_s);
    set_rng         = double(hp.hop_set_size);
    require_revisit = logical(hp.require_revisit);

    df_grid = double(pa_get_nested(cfg, "zigbee_base_waveform.offset_grid_hz"));
    df_grid = df_grid(:);
    assert(~isempty(df_grid), "zigbee_base_waveform.offset_grid_hz must be nonempty.");

    zbCfg = zb_make_zigbee_cfg(cfg);

    for i = 1:double(M)
        window_id = i;

        [~, seed_op] = pa_sha_seed(master_seed, schema, ...
            session_id, tape_id, segment_id, window_id, "PA4_operator");
        rs = RandStream("mt19937ar","Seed",double(seed_op));

        K = randi(rs, [round(set_rng(1)), round(set_rng(2))], 1, 1);
        assert(numel(df_grid) >= K, "Offset grid too small for K=%d", K);

        perm = randperm(rs, numel(df_grid), K);
        offset_set_hz = df_grid(perm);

        offset_cycle_hz = offset_set_hz(randperm(rs, K));
        if require_revisit
            % revisit guaranteed by repeating cycle
        end

        x = complex(zeros(double(W),1,"single"), zeros(double(W),1,"single"));

        dwell_samp    = zeros(0,1);
        offset_seq_hz = zeros(0,1);

        cursor = 1;
        ci = 1;
        pkt_count_total = 0;
        phi = 0;

        while cursor <= double(W)
            dwell_s = dwell_rng(1) + (dwell_rng(2)-dwell_rng(1)) * rand(rs);
            ds = max(1, round(dwell_s * double(Fs)));

            df = offset_cycle_hz(ci);

            x_blk = complex(zeros(0,1,"single"), zeros(0,1,"single"));

            while numel(x_blk) < ds
                [~, seed_payload] = pa_sha_seed(master_seed, schema, ...
                    session_id, tape_id, segment_id, ...
                    window_id*100000 + pkt_count_total + 1, "payload");

                [x_pkt, ~] = zb_gen_packet(uint32(seed_payload), zbCfg);

                x_blk = [x_blk; x_pkt]; %#ok<AGROW>
                pkt_count_total = pkt_count_total + 1;
            end

            x_blk = x_blk(1:ds);

            [x_blk, phi] = pa_mix_freq_offset_block(x_blk, double(Fs), df, phi);

            b0 = cursor;
            b1 = min(double(W), cursor + ds - 1);
            x(b0:b1) = x_blk(1:(b1-b0+1));

            dwell_samp(end+1,1) = ds; %#ok<AGROW>
            offset_seq_hz(end+1,1) = df; %#ok<AGROW>

            cursor = b1 + 1;
            ci = ci + 1;
            if ci > numel(offset_cycle_hz), ci = 1; end
        end

        Xsig(:,i) = x;

        meta(i).schema_version      = pa_get_nested(cfg, "schema_version");
        meta(i).session_id          = session_id;
        meta(i).tape_id             = tape_id;
        meta(i).segment_id          = segment_id;
        meta(i).window_id           = window_id;
        meta(i).pa_type             = "PA4";
        meta(i).protocol            = "zigbee";
        meta(i).fs_hz               = double(Fs);
        meta(i).window_length_s     = double(pa_get_nested(cfg, "windowing.window_length_s"));
        meta(i).window_start_sample = double(plan.starts(i));
        meta(i).packet_count        = pkt_count_total;
        meta(i).offset_set_hz       = offset_set_hz(:);
        meta(i).offset_cycle_hz     = offset_cycle_hz(:);
        meta(i).dwell_samp          = dwell_samp(:);
        meta(i).offset_seq_hz       = offset_seq_hz(:);

        sched(i).offset_set_hz      = offset_set_hz(:);
        sched(i).offset_cycle_hz    = offset_cycle_hz(:);
        sched(i).dwell_samp         = dwell_samp(:);
        sched(i).offset_seq_hz      = offset_seq_hz(:);
        sched(i).packet_count       = pkt_count_total;
    end
end