function [Xsig, meta] = zb_gen_windows_pa3_stream(cfg, session_id, tape_id, segment_id, plan)
%ZB_GEN_WINDOWS_PA3_STREAM Dense Zigbee packet-train PA3 windows (no intentional gaps).

    Fs = int64(plan.Fs);
    W  = int64(plan.W);
    M  = int64(numel(plan.starts));

    Xsig = complex(zeros(double(W), double(M), "single"), ...
                   zeros(double(W), double(M), "single"));

    meta = repmat(struct(), 1, double(M));

    master_seed = pa_get_nested(cfg, "generator.seeds.master_seed");
    schema      = pa_get_nested(cfg, "schema_version");

    zbCfg = zb_make_zigbee_cfg(cfg);

    for i = 1:double(M)
        window_id = i;

        x_buf = complex(zeros(0,1,"single"), zeros(0,1,"single"));
        pkt_count = 0;
        pkt_info_last = struct();

        while numel(x_buf) < double(W)
            [~, seed_payload] = pa_sha_seed(master_seed, schema, ...
                session_id, tape_id, segment_id, window_id*100000 + pkt_count + 1, "payload");

            [x_pkt, pkt_info] = zb_gen_packet(uint32(seed_payload), zbCfg);

            x_buf = [x_buf; x_pkt]; %#ok<AGROW>
            pkt_count = pkt_count + 1;
            pkt_info_last = pkt_info;
        end

        Xsig(:,i) = x_buf(1:double(W));

        meta(i).schema_version      = pa_get_nested(cfg, "schema_version");
        meta(i).session_id          = session_id;
        meta(i).tape_id             = tape_id;
        meta(i).segment_id          = segment_id;
        meta(i).window_id           = window_id;
        meta(i).pa_type             = "PA3";
        meta(i).protocol            = "zigbee";
        meta(i).fs_hz               = double(Fs);
        meta(i).window_length_s     = double(pa_get_nested(cfg, "windowing.window_length_s"));
        meta(i).window_start_sample = double(plan.starts(i));
        meta(i).packet_count        = pkt_count;
        meta(i).zb_band_mhz         = double(zbCfg.Band);
        meta(i).zb_samples_per_chip = double(zbCfg.SamplesPerChip);
        meta(i).zb_psdu_length      = double(zbCfg.PSDULength);
        meta(i).zb_packet_nsamp     = pkt_info_last.nsamp;
    end
end