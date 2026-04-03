function [Xsig, meta, sched] = bt_gen_windows_pa2_stream(cfg, session_id, tape_id, segment_id, plan)
%BT_GEN_WINDOWS_PA2_STREAM Build Bluetooth PA2 windows in streaming style.
% Mirrors the Wi-Fi PA2 approach:
%   - one segment-level burst schedule
%   - windows are cropped views of that schedule
%   - dense BLE packets inside each burst
%
% Inputs:
%   cfg, session_id, tape_id, segment_id
%   plan.Fs
%   plan.W
%   plan.starts
%   plan.L   (optional; if absent, uses max window end)
%
% Outputs:
%   Xsig  [W x M] complex single
%   meta  per-window metadata
%   sched segment-level burst schedule diagnostics

    Fs = int64(plan.Fs);
    W  = int64(plan.W);
    starts = int64(plan.starts(:));
    M = int64(numel(starts));
    ends = starts + W - 1;

    if isfield(plan, "L")
        L = int64(plan.L);
    else
        L = max(ends);
    end

    % sort windows by start for efficient overlap checks
    [startsS, ord] = sort(starts);
    endsS = ends(ord);
    invord = zeros(size(ord));
    invord(ord) = 1:numel(ord);

    XsigS = complex(zeros(double(W), double(M), "single"), ...
                    zeros(double(W), double(M), "single"));

    master_seed = pa_get_nested(cfg, "generator.seeds.master_seed");
    schema      = pa_get_nested(cfg, "schema_version");

    pa2 = pa_get_nested(cfg, "pas.PA2.params");
    on_rng  = double(pa2.burst_on_s);
    ibi_rng = double(pa2.ibi_mean_s);
    jit_rng = double(pa2.ibi_jitter_frac);

    btCfg = bt_make_ble_cfg(cfg);

    % segment-level RNG for schedule
    [~, seed_op] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, 0, "PA2_segment_ops");
    rs = RandStream("mt19937ar","Seed",double(seed_op));

    min_gap_samps = int64(round(0.0002 * double(Fs)));   % 0.2 ms
    L_need = min(L, max(endsS));

    t = int64(1);
    pkt_idx = int64(1);
    wi = 1;

    burst_starts = zeros(0,1);
    burst_lens   = zeros(0,1);
    ibi_samps_v  = zeros(0,1);

    while t <= L_need && wi <= M
        burst_on_s = on_rng(1) + (on_rng(2)-on_rng(1)) * rand(rs);
        burst_on   = int64(max(1, round(burst_on_s * double(Fs))));
        burst_end  = t + burst_on - 1;

        if burst_end > L_need
            break;
        end

        % generate enough BLE packets to cover this burst, then truncate
        xb = complex(zeros(0,1,"single"), zeros(0,1,"single"));
        while int64(numel(xb)) < burst_on
            [~, seed_payload] = pa_sha_seed(master_seed, schema, session_id, tape_id, segment_id, pkt_idx, "payload");
            [x_pkt, ~] = bt_gen_packet(uint32(seed_payload), btCfg);
            xb = [xb; x_pkt]; %#ok<AGROW>
            pkt_idx = pkt_idx + 1;
        end
        xb = xb(1:double(burst_on));

        % advance past windows that end before this burst starts
        while wi <= M && endsS(wi) < t
            wi = wi + 1;
        end

        % copy overlap into every overlapping window
        wj = wi;
        while wj <= M && startsS(wj) <= burst_end
            ovL = max(t, startsS(wj));
            ovR = min(burst_end, endsS(wj));
            if ovL <= ovR
                b0 = ovL - t + 1;
                b1 = ovR - t + 1;
                w0 = ovL - startsS(wj) + 1;
                w1 = ovR - startsS(wj) + 1;

                XsigS(double(w0):double(w1), double(wj)) = ...
                    XsigS(double(w0):double(w1), double(wj)) + xb(double(b0):double(b1));
            end
            wj = wj + 1;
        end

        burst_starts(end+1,1) = double(t); %#ok<AGROW>
        burst_lens(end+1,1)   = double(burst_on); %#ok<AGROW>

        ibi_mean_s = ibi_rng(1) + (ibi_rng(2)-ibi_rng(1)) * rand(rs);
        jit_frac   = jit_rng(1) + (jit_rng(2)-jit_rng(1)) * rand(rs);
        ibi_s      = ibi_mean_s + (2*rand(rs)-1) * (jit_frac * ibi_mean_s);
        ibi        = int64(max(1, round(ibi_s * double(Fs))));

        % enforce non-overlap + small guard gap
        if ibi < burst_on + min_gap_samps
            ibi = burst_on + min_gap_samps;
        end

        ibi_samps_v(end+1,1) = double(ibi); %#ok<AGROW>
        t = t + ibi;
    end

    % unsort back to requested plan order
    Xsig = XsigS(:, invord);

    % segment-level schedule
    sched = struct();
    sched.L_need = double(L_need);
    sched.burst_starts_samp = burst_starts;
    sched.burst_len_samp    = burst_lens;
    sched.ibi_samp          = ibi_samps_v;

    % per-window metadata
    meta = repmat(struct(), 1, double(M));

    if isempty(burst_starts)
        burst_intervals = zeros(0,2);
    else
        burst_intervals = [burst_starts, burst_starts + burst_lens - 1];
    end

    starts_plan = starts(:);
    ends_plan   = ends(:);

    for i = 1:double(M)
        a = double(starts_plan(i));
        b = double(ends_plan(i));

        keep = burst_intervals(:,1) <= b & burst_intervals(:,2) >= a;
        iv = burst_intervals(keep,:);

        meta(i).schema_version      = pa_get_nested(cfg, "schema_version");
        meta(i).session_id          = session_id;
        meta(i).tape_id             = tape_id;
        meta(i).segment_id          = segment_id;
        meta(i).window_id           = i;
        meta(i).pa_type             = "PA2";
        meta(i).protocol            = "bluetooth";
        meta(i).fs_hz               = double(Fs);
        meta(i).window_length_s     = double(pa_get_nested(cfg, "windowing.window_length_s"));
        meta(i).window_start_sample = double(starts_plan(i));
        meta(i).burst_count         = size(iv,1);
        meta(i).burst_intervals_abs = iv;
    end
end