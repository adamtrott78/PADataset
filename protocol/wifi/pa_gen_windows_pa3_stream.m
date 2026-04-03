function [Xsig, sched] = pa_gen_windows_pa3_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan)
%PA_GEN_WINDOWS_PA3_STREAM Build signal-only PA3 windows without allocating full segment.
% Continuous occupancy: back-to-back NonHT packets (no gaps).
% Output:
%   Xsig [W x M] complex single (columns = windows in plan order)

    Fs = int64(plan.Fs); W = int64(plan.W); L = int64(plan.L);
    starts = int64(plan.starts(:)); M = int64(numel(starts));
    ends   = starts + W - 1;

    % Sort windows by start for efficient overlap checks, return in plan order
    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord)); invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg,"generator.seeds.master_seed");
    schema      = pa_get_nested(cfg,"schema_version");

    % only simulate until last needed window end
    L_need = min(L, max(endsS));

    t = int64(1);          % current packet start sample (1-indexed)
    pkt_idx = int64(1);    % global packet index within segment (deterministic seeding)
    wi = 1;                % pointer into sorted windows

    pkt_count = 0;

    while t <= L_need && wi <= M
        % per-packet deterministic seeds
        [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
        [~, seed_scr]     = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "scrambler");
        rs_scr = RandStream("mt19937ar","Seed",double(seed_scr));
        scr = randi(rs_scr, [1 127], 1, 1);

        x_pkt = pa_gen_packet(uint32(seed_payload), scr, wlanCfg);
        pkt_len = int64(numel(x_pkt));
        pkt_end = t + pkt_len - 1;

        if pkt_end > L_need
            % truncate packet if it runs past L_need (fine for streaming)
            keep = double(L_need - t + 1);
            if keep <= 0, break; end
            x_pkt = x_pkt(1:keep);
            pkt_len = int64(numel(x_pkt));
            pkt_end = t + pkt_len - 1;
        end

        pkt_count = pkt_count + 1;

        % advance pointer past windows that end before this packet starts
        while wi <= M && endsS(wi) < t
            wi = wi + 1;
        end

        % copy overlaps into all windows overlapping this packet
        wj = wi;
        while wj <= M && startsS(wj) <= pkt_end
            ovL = max(t, startsS(wj));
            ovR = min(pkt_end, endsS(wj));
            if ovL <= ovR
                p0 = ovL - t + 1;              % packet-local idx
                p1 = ovR - t + 1;
                w0 = ovL - startsS(wj) + 1;    % window-local idx
                w1 = ovR - startsS(wj) + 1;
                XsigS(double(w0):double(w1), double(wj)) = XsigS(double(w0):double(w1), double(wj)) + x_pkt(double(p0):double(p1));
            end
            wj = wj + 1;
        end

        % next packet immediately after (continuous)
        t = pkt_end + 1;
        pkt_idx = pkt_idx + 1;
    end

    Xsig = XsigS(:, invord);

    sched = struct();
    sched.L_need = double(L_need);
    sched.packet_count = pkt_count;
end