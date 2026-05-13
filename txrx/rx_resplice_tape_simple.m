function rx_resplice_tape_simple(protocol, dataset_id, shard_id, varargin)
%RX_RESPLICE_TAPE_SIMPLE
% Simplified operator-assisted OTA resplicer for shard recordings.
%
% Design:
%   - Operator can provide an initial seed header location.
%   - When the forward chain breaks, the function prints the expected next
%     header location and can jump to operator-provided fallback anchors.
%   - Forward chaining only; no backward recovery.
%   - Slip hypotheses are in 100k-sample steps, matching the SDR loss mode.
%
% Usage examples:
%   rx_resplice_tape_simple("bluetooth", "high_run01", 1, 'seed_k', 1800000)
%
%   rx_resplice_tape_simple("bluetooth", "high_run01", 1, ...
%       'seed_k', 1800000, ...
%       'fallback_k', [6838931 7500000])
%
% Optional name/value:
%   'seed_k'           : initial approximate header location. default = 0
%   'fallback_k'       : vector of fallback approximate header locations
%   'search_radius'    : local search radius around each slip center. default = 1000
%   'seed_radius'      : local search radius around the initial seed. default = 20000
%   'fallback_radius'  : local search radius around fallback anchors. default = 1000
%   'slip_frames'      : vector of 100k-frame slip hypotheses. default = -2:2
%   'make_png'         : default false
%   'max_png_per_pa'   : default 0
%
% Output layout:
%   data/<protocol>/ota/spliced/simple/<dataset_id>/shard_###/
%   results/<protocol>/ota/rx_resplice_simple/<dataset_id>/shard_###/

    ip = inputParser;
    addParameter(ip, 'seed_k', 0, @(x) isnumeric(x) && isscalar(x) && isfinite(x));
    addParameter(ip, 'fallback_k', [], @(x) isempty(x) || (isnumeric(x) && isvector(x)));
    addParameter(ip, 'search_radius', 1000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'seed_radius', 20000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'auto_skip_records', 0, @(x) isnumeric(x) && isscalar(x) && x >= 0);
    addParameter(ip, 'auto_skip_search_radius', 500, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'fallback_radius', 1000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'slip_frames', -2:2, @(x) isempty(x) || (isnumeric(x) && isvector(x)));
    addParameter(ip, 'delete_ota_after_load', false, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'make_png', false, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'max_png_per_pa', 0, @(x) isnumeric(x) && isscalar(x) && x >= 0);
    addParameter(ip, 'hard_reacquire_enable', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'hard_reacquire_span_samp', 700000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'hard_scan_enable', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'hard_scan_span', 700000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'hard_scan_max_blocks', Inf, @(x) isnumeric(x) && isscalar(x) && (x > 0 || isinf(x)));
    parse(ip, varargin{:});

    seed_k = round(double(ip.Results.seed_k));
    fallback_k = round(double(ip.Results.fallback_k(:).'));
    search_radius = round(double(ip.Results.search_radius));
    seed_radius = round(double(ip.Results.seed_radius));
    auto_skip_records = round(double(ip.Results.auto_skip_records));
    auto_skip_search_radius = round(double(ip.Results.auto_skip_search_radius));
    fallback_radius = round(double(ip.Results.fallback_radius));
    slip_frames = round(double(ip.Results.slip_frames(:).'));
    delete_ota_after_load = logical(ip.Results.delete_ota_after_load);
    make_png = logical(ip.Results.make_png);
    max_png_per_pa = round(double(ip.Results.max_png_per_pa));
    hard_reacquire_enable = logical(ip.Results.hard_reacquire_enable);
    hard_reacquire_span_samp = round(double(ip.Results.hard_reacquire_span_samp));
    hard_scan_enable = logical(ip.Results.hard_scan_enable);
    hard_scan_span   = round(double(ip.Results.hard_scan_span));
    hard_scan_max_blocks = double(ip.Results.hard_scan_max_blocks);
    
    protocol = string(protocol);
    assert(any(protocol == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    dataset_id = string(dataset_id);
    prefix = protocol + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end

    shard_id = validate_shard_id_simple(shard_id);

    R = pa_protocol_roots(protocol);

    ota_file = fullfile(R.txrx_tapes_ota, char(dataset_full), ...
        sprintf('ota_tape_shard_%03d.mat', shard_id));
    spec_file = fullfile(R.txrx_tapes_digital, char(dataset_full), ...
        sprintf('tx_spec_shard_%03d.mat', shard_id));

    if ~isfile(ota_file)
        error("OTA tape file not found: %s", ota_file);
    end
    if ~isfile(spec_file)
        error("TX spec file not found: %s", spec_file);
    end

    out_data = fullfile(pa_root(), 'data', char(protocol), 'ota', 'spliced', ...
        'simple', char(dataset_full), sprintf('shard_%03d', shard_id));
    out_res = fullfile(pa_root(), 'results', char(protocol), 'ota', ...
        'rx_resplice_simple', char(dataset_full), sprintf('shard_%03d', shard_id));

    if ~exist(out_data, 'dir'), mkdir(out_data); end
    if ~exist(out_res, 'dir'), mkdir(out_res); end

    png_root = fullfile(out_res, 'png');
    if make_png && ~exist(png_root, 'dir'), mkdir(png_root); end

    T = load(ota_file, 'x_tape', 'rx_cfg');
    x_tape = T.x_tape(:);
    rx_cfg = T.rx_cfg;

    if delete_ota_after_load && isfile(ota_file)
        try
            delete(ota_file);
            fprintf("RESP SIMPLE | deleted OTA tape after load: %s\n", ota_file);
        catch ME
            warning("RESP SIMPLE | failed to delete OTA tape: %s | %s", ota_file, ME.message);
        end
    end

    S = load(spec_file, 'tx_spec');
    tx_spec = S.tx_spec;
    p = tx_spec.tx_params;
    sync = tx_spec.sync;
    tx_index = tx_spec.tx_index;

    tx_lut = make_tx_lut_simple(tx_index);

    fprintf("RESP SIMPLE | protocol=%s | dataset=%s | shard=%03d\n", ...
        protocol, dataset_full, shard_id);
    fprintf("RESP SIMPLE | ota=%s\n", ota_file);
    fprintf("RESP SIMPLE | spec=%s\n", spec_file);
    fprintf("RESP SIMPLE | tape=%d | Fs=%.6f MS/s | frameLen=%d | W=%d | guardN=%d | overruns=%d\n", ...
        numel(x_tape), rx_cfg.Fs/1e6, p.frameLen, p.W, p.guardN, rx_cfg.overruns);
    fprintf("RESP SIMPLE | search_radius=%d | seed_radius=%d | fallback_radius=%d | slip_frames=[", ...
        search_radius, seed_radius, fallback_radius);
    fprintf("%d ", slip_frames);
    fprintf("]\n");

    PAs = unique(string(tx_index.pa), "stable");
    PAs = PAs(:).';              % force row vector so for-loop yields scalars
    
    pa_col = string(tx_index.pa);
    pa_col = pa_col(:);          % force column vector for counting
    
    X = struct(); M = struct(); counts = struct();
    
    for ii = 1:numel(PAs)
        pa = PAs(ii);
        n_alloc = sum(pa_col == pa);
        X.(char(pa)) = complex(zeros(p.W, n_alloc, "single"), zeros(p.W, n_alloc, "single"));
        M.(char(pa)) = repmat(empty_meta_simple(), 1, n_alloc);
        counts.(char(pa)) = 0;
    end

    % transport structure
    Lrec = double(p.frameLen) + double(p.W) + double(p.guardN);
    need_gap = double(p.frameLen) + double(p.W);
    frame_step = double(p.frameLen);

    % ------------------------------------------------------------
    % Bootstrap first header
    % ------------------------------------------------------------
    h_cur = empty_hdr_simple();
    ok0 = false;
    
    if seed_k <= 0
        begin_hi = min(numel(x_tape) - (p.frameLen + p.W) + 1, 6000000);
        fprintf("BOOTSTRAP | searching beginning region [1, %d]\n", begin_hi);
    
        [h_cur, ok0] = search_first_header_in_range_simple( ...
            x_tape, 1, begin_hi, p, tx_lut, uint16(0));
    
        if ok0
            fprintf("BOOTSTRAP SUCCESS | auto beginning search\n");
        end
    else
        fprintf("BOOTSTRAP | manual seed near %d | search window [%d, %d]\n", ...
            seed_k, max(1, seed_k-seed_radius), min(numel(x_tape), seed_k+seed_radius));
    
        [h_cur, ok0] = search_header_near_simple( ...
            x_tape, seed_k, seed_radius, p, tx_lut, uint16(0), seed_k);
    
        if ok0
            fprintf("BOOTSTRAP SUCCESS | manual seed search\n");
        end
    end
    
    % ---- hard bootstrap fallback: scan repeated 700k blocks until first valid header ----
    if ~ok0 && hard_scan_enable
        [h_cur, ok0, lo_hard, hi_hard, blk_hard] = search_first_header_blocks_simple( ...
            x_tape, 1, p, tx_lut, uint16(0), hard_scan_span, hard_scan_max_blocks);
    
        if ok0
            fprintf("BOOTSTRAP HARD HIT | block=%d | scan=[%d,%d] | k=%d | seq=%d | pa=%s | wid=%d\n", ...
                blk_hard, lo_hard, hi_hard, h_cur.k, h_cur.seq, h_cur.pa, h_cur.wid);
        else
            fprintf("BOOTSTRAP HARD MISS | scanned through block=%d | last_scan=[%d,%d]\n", ...
                blk_hard, lo_hard, hi_hard);
        end
    end
    
    if ~ok0
        error("Bootstrap failed: no valid first header found (seed_k=%d).", seed_k);
    end

    h_cur.r = preamble_score_at_k_simple(x_tape, h_cur.k, p, sync);

    fprintf("FIRST HDR | seq=%d | pa=%s | wid=%d | k=%d | r=%.2f\n", ...
        h_cur.seq, h_cur.pa, h_cur.wid, h_cur.k, h_cur.r);

    % ------------------------------------------------------------
    % Forward chain
    % ------------------------------------------------------------
    H = repmat(empty_hdr_simple(), 1, tx_lut.N + numel(fallback_k) + 64);
    nH = 1;
    H(1) = h_cur;

    nFail = 0;
    stop_seen = h_cur.is_stop;
    fallback_used = 0;

    while ~stop_seen
        cur = H(nH);

        fprintf("SEARCH NEXT | after seq=%d | pa=%s | wid=%d | current_k=%d\n", ...
            cur.seq, cur.pa, cur.wid, cur.k);

        [nxt, ok, expected_k, tried_centers] = find_next_valid_header_simple( ...
            x_tape, cur, p, tx_lut, search_radius, slip_frames);

        if ~ok
            nFail = nFail + 1;
            fprintf("NEXT HDR FAIL | after seq=%d | pa=%s | wid=%d | current_k=%d\n", ...
                cur.seq, cur.pa, cur.wid, cur.k);
            fprintf("Expected next header near %d samples\n", round(expected_k));
            fprintf("Tried centers: ");
            fprintf("%d ", round(tried_centers));
            fprintf("\n");

            % ------------------------------------------------------------
            % Auto-skip recovery: allow one or more whole missed records
            % ------------------------------------------------------------
            [nxt_skip, ok_skip, skip_used, expected_k_skip] = try_auto_skip_header_simple( ...
                x_tape, cur, p, tx_lut, auto_skip_records, auto_skip_search_radius);
            
            if ok_skip
                fprintf("AUTO SKIP HIT | skipped_records=%d | expected_k=%d | seq=%d | pa=%s | wid=%d | k=%d\n", ...
                    skip_used, round(expected_k_skip), nxt_skip.seq, nxt_skip.pa, nxt_skip.wid, nxt_skip.k);
                nxt = nxt_skip;
                ok = true;
            end

            % ------------------------------------------------------------
            % HARD RE-ACQUIRE: scan repeated 700k blocks until the next valid header.
            % Use this when one or more headers/preambles were destroyed by drops.
            % ------------------------------------------------------------
            if ~ok && (hard_scan_enable || hard_reacquire_enable)
                scan_span = hard_scan_span;
                if ~hard_scan_enable && hard_reacquire_enable
                    scan_span = hard_reacquire_span_samp;
                end
            
                [nxt_hard, ok_hard, lo_hard, hi_hard, blk_hard] = hard_reacquire_next_header_blocks_simple( ...
                    x_tape, expected_k, cur, p, tx_lut, slip_frames, search_radius, scan_span, hard_scan_max_blocks);
            
                if ok_hard
                    fprintf("HARD REACQUIRE HIT | block=%d | scan=[%d,%d] | seq=%d | pa=%s | wid=%d | k=%d\n", ...
                        blk_hard, lo_hard, hi_hard, nxt_hard.seq, nxt_hard.pa, nxt_hard.wid, nxt_hard.k);
                    nxt = nxt_hard;
                    ok = true;
                else
                    fprintf("HARD REACQUIRE MISS | scanned through block=%d | last_scan=[%d,%d]\n", ...
                        blk_hard, lo_hard, hi_hard);
                end
            end

            if ~ok && fallback_used < numel(fallback_k)
                fallback_used = fallback_used + 1;
                fk = fallback_k(fallback_used);
                fprintf("Using fallback %d at sample %d\n", fallback_used, fk);

                % Manual fallback is a re-anchor: do NOT enforce seq > current seq
                [nxt_fb, ok_fb] = raw_decode_valid_header_at_k_simple( ...
                    x_tape, fk, p, tx_lut, uint16(0));
                
                if ok_fb
                    nxt_fb.r = preamble_score_at_k_simple(x_tape, nxt_fb.k, p, sync);
                    fprintf("FALLBACK EXACT HIT | seq=%d | pa=%s | wid=%d | k=%d | r=%.2f\n", ...
                        nxt_fb.seq, nxt_fb.pa, nxt_fb.wid, nxt_fb.k, nxt_fb.r);
                else
                    lo_fb = max(1, fk-fallback_radius);
                    hi_fb = min(numel(x_tape), fk+fallback_radius);
                    
                    fprintf("FALLBACK EXACT MISS | searching [%d, %d]\n", lo_fb, hi_fb);
                    debug_fallback_window_simple(x_tape, lo_fb, hi_fb, p, tx_lut);
                    
                    [nxt_fb, ok_fb] = search_header_near_simple( ...
                        x_tape, fk, fallback_radius, p, tx_lut, uint16(0), fk);
                    
                    if ok_fb
                        nxt_fb.r = preamble_score_at_k_simple(x_tape, nxt_fb.k, p, sync);
                        fprintf("FALLBACK LOCAL HIT | seq=%d | pa=%s | wid=%d | k=%d | r=%.2f\n", ...
                            nxt_fb.seq, nxt_fb.pa, nxt_fb.wid, nxt_fb.k, nxt_fb.r);
                    end
                end

                if ~ok_fb
                    fprintf("Fallback %d failed near %d\n", fallback_used, fk);
                    break;
                end

                nxt = nxt_fb;
                ok = true;
            elseif ~ok
                break;
            end
        else
            if nxt.is_stop
                fprintf("HDR FOUND | STOP | k=%d\n", nxt.k);
            else
                fprintf("HDR FOUND | seq=%d | pa=%s | wid=%d | k=%d\n", ...
                    nxt.seq, nxt.pa, nxt.wid, nxt.k);
            end
        end

        nH = nH + 1;
        H(nH) = nxt;
        stop_seen = nxt.is_stop;
    end

    H = H(1:nH);
    fprintf("HDR DONE | found=%d | stop_seen=%d | fail=%d | first_seq=%d | last_seq=%d\n", ...
        nH, stop_seen, nFail, H(1).seq, H(end).seq);

    % ------------------------------------------------------------
    % Safe payload keep/drop rule
    % ------------------------------------------------------------
    drop_log = repmat(empty_drop_simple(), 1, max(1, nH));
    nDrop = 0;
    nKeep = 0;

    for i = 1:max(0, nH-1)
        cur = H(i);
        nxt = H(i+1);

        if cur.is_stop, break; end
        pa = cur.pa;
        if pa == "", continue; end

        pay0 = double(cur.k) + double(p.frameLen);
        pay1 = pay0 + double(p.W) - 1;
        gap = double(nxt.k - cur.k);

        if pay1 > numel(x_tape) || gap < need_gap
            nDrop = nDrop + 1;
            drop_log(nDrop) = struct( ...
                "seq", uint16(cur.seq), ...
                "pa_type", char(pa), ...
                "window_id", uint16(cur.wid), ...
                "k_hdr", int64(cur.k), ...
                "k_next", int64(nxt.k), ...
                "gap", int64(gap), ...
                "reason", "truncated_or_unproven");
            fprintf("DROP | seq=%d | pa=%s | wid=%d | k=%d | next_k=%d | gap=%d\n", ...
                cur.seq, pa, cur.wid, cur.k, nxt.k, gap);
            continue;
        end

        c = counts.(char(pa)) + 1;
        counts.(char(pa)) = c;

        X.(char(pa))(:,c) = x_tape(pay0:pay1);
        M.(char(pa))(c) = struct( ...
            "schema_version", "ota_simple", ...
            "protocol", char(protocol), ...
            "session_id", 1, ...
            "tape_id", 1, ...
            "segment_id", 0, ...
            "window_id", uint16(cur.wid), ...
            "pa_type", char(pa), ...
            "fs_hz", double(rx_cfg.Fs), ...
            "window_length_s", double(p.W)/double(rx_cfg.Fs), ...
            "seq", uint16(cur.seq), ...
            "k_ph", int64(cur.k), ...
            "k_next", int64(nxt.k), ...
            "gap_to_next", int64(gap), ...
            "header_r", double(cur.r));

        nKeep = nKeep + 1;
    end

    if ~H(end).is_stop
        tail = H(end);
        if tail.pa ~= ""
            nDrop = nDrop + 1;
            drop_log(nDrop) = struct( ...
                "seq", uint16(tail.seq), ...
                "pa_type", char(tail.pa), ...
                "window_id", uint16(tail.wid), ...
                "k_hdr", int64(tail.k), ...
                "k_next", int64(-1), ...
                "gap", int64(-1), ...
                "reason", "unpaired_tail");
            fprintf("DROP | seq=%d | pa=%s | wid=%d | k=%d | reason=unpaired_tail\n", ...
                tail.seq, tail.pa, tail.wid, tail.k);
        end
    end

    drop_log = drop_log(1:nDrop);

    for pa = PAs
        c = counts.(char(pa));
        Xrx_all = X.(char(pa))(:,1:c);
        meta_rx = M.(char(pa))(1:c);

        out = fullfile(out_data, sprintf("ota_rx_%s.mat", pa));
        save(out, "Xrx_all", "meta_rx", "rx_cfg", "-v7.3");
        fprintf("Saved %s | %d windows\n", out, c);
    end

    summary = struct();
    summary.version = "simple";
    summary.protocol = char(protocol);
    summary.dataset_id = char(dataset_full);
    summary.shard_id = int32(shard_id);
    summary.seed_k = int64(seed_k);
    summary.fallback_k = int64(fallback_k);
    summary.stop_seen = logical(stop_seen);
    summary.headers_found = H;
    summary.n_headers = int32(nH);
    summary.n_keep = int32(nKeep);
    summary.n_drop = int32(nDrop);
    summary.counts = counts;
    summary.rx_cfg = rx_cfg;
    summary.need_gap = int32(need_gap);
    summary.Lrec = int32(Lrec);
    summary.frame_step = int32(frame_step);

    save(fullfile(out_res, "resplice_summary_simple.mat"), "summary", "drop_log", "-v7.3");

    if make_png
        if exist(png_root, "dir"), rmdir(png_root, "s"); end
        mkdir(png_root);

        pilot_root = pilot_root_from_protocol_simple(protocol);

        for pa = PAs
            c = counts.(char(pa));
            K = min(max_png_per_pa, c);
            for i = 1:K
                wid = double(M.(char(pa))(i).window_id);
                x_o = X.(char(pa))(:,i);
                [x_d, Fs_d, okd] = load_digital_by_window_id_simple(pilot_root, pa, wid);
                if ~okd, continue; end
                outpng = fullfile(png_root, sprintf("DIG_vs_OTA_%s_w%04d.png", pa, wid));
                plot_pair_dig_vs_ota_simple(pa, x_d, Fs_d, x_o, rx_cfg.Fs, outpng);
            end
        end
    end

    fprintf("RESP SIMPLE DONE | kept=%d | dropped=%d | stop_seen=%d | fail=%d\n", ...
        nKeep, nDrop, stop_seen, nFail);
end


function [nxt, ok, expected_k, tried_centers] = find_next_valid_header_simple( ...
    x_tape, cur, p, tx_lut, search_radius, slip_frames)

    Lrec = double(p.frameLen) + double(p.W) + double(p.guardN);
    expected_k = double(cur.k) + Lrec;

    tried_centers = expected_k + double(slip_frames) * double(p.frameLen);

    nxt = empty_hdr_simple();
    ok = false;

    best = empty_hdr_simple();
    ok_best = false;

    fprintf("  NEXT SEARCH | expected_k=%d | search_radius=%d\n", round(expected_k), search_radius);

    for i = 1:numel(tried_centers)
        center = tried_centers(i);
        lo = round(center - search_radius);
        hi = round(center + search_radius);

        fprintf("    trying center %d | window [%d, %d]\n", round(center), lo, hi);

        [cand, okc] = search_header_near_simple( ...
            x_tape, center, search_radius, p, tx_lut, uint16(cur.seq), expected_k);

        if okc
            fprintf("      candidate | seq=%d | pa=%s | wid=%d | k=%d\n", ...
                cand.seq, cand.pa, cand.wid, cand.k);
        end

        if okc && (~ok_best || cand_better_simple(cand, best, cur, expected_k))
            best = cand;
            ok_best = true;
        end
    end

    if ok_best
        nxt = best;
        ok = true;
    end
end


function [best, ok] = search_header_near_simple( ...
    x_tape, center_k, search_radius, p, tx_lut, seq_floor, expected_k)

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    lo = max(1, round(double(center_k) - double(search_radius)));
    hi = min(kmax, round(double(center_k) + double(search_radius)));

    [best, ok] = search_header_in_range_simple( ...
        x_tape, lo, hi, p, tx_lut, seq_floor, expected_k);
end


function [best, ok] = search_header_in_range_simple( ...
    x_tape, lo, hi, p, tx_lut, seq_floor, expected_k)

    best = empty_hdr_simple();
    ok = false;

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    lo = max(1, round(lo));
    hi = min(kmax, round(hi));
    if hi < lo
        return;
    end

    for k = lo:hi
        [cand, okc] = raw_decode_valid_header_at_k_simple( ...
            x_tape, k, p, tx_lut, seq_floor);

        if ~okc
            continue;
        end

        if ~ok || cand_better_given_expectation_simple(cand, best, expected_k)
            best = cand;
            ok = true;
        end
    end
end


function [hdr, ok] = raw_decode_valid_header_at_k_simple(x_tape, k, p, tx_lut, seq_floor)
    hdr = empty_hdr_simple();
    ok = false;

    k = round(double(k));
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    if k < 1 || k > kmax
        return;
    end

    hdr_samp = x_tape(k + p.Lpre + (1:p.Lhdr));
    [pa_id, wid, seq, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);
    if ~crc_ok
        return;
    end

    pa_id = uint16(pa_id);
    wid   = uint16(wid);
    seq   = uint16(seq);

    is_stop = (double(pa_id) == 15) && (double(wid) == 65535) && (double(seq) == 65535);
    if is_stop
        hdr = struct("k", int64(k), "pa_id", pa_id, "pa", "", "wid", wid, ...
            "seq", seq, "is_stop", true, "r", NaN);
        ok = true;
        return;
    end

    pa = id_to_pa_simple(pa_id);
    if pa == ""
        return;
    end

    if seq <= seq_floor
        return;
    end

    s = double(seq);
    if s < 1 || s > tx_lut.N
        return;
    end

    if tx_lut.pa_id(s) ~= pa_id || tx_lut.wid(s) ~= wid
        return;
    end

    hdr = struct("k", int64(k), "pa_id", pa_id, "pa", pa, "wid", wid, ...
        "seq", seq, "is_stop", false, "r", NaN);
    ok = true;
end


function tf = cand_better_simple(a, b, cur, expected_k)
    ka = cand_key_simple(a, double(cur.seq) + 1, expected_k);
    kb = cand_key_simple(b, double(cur.seq) + 1, expected_k);
    tf = lexicographically_better_simple(ka, kb);
end


function tf = cand_better_given_expectation_simple(a, b, expected_k)
    ka = cand_key_simple(a, inf, expected_k);
    kb = cand_key_simple(b, inf, expected_k);
    tf = lexicographically_better_simple(ka, kb);
end


function key = cand_key_simple(cand, seq_target, expected_k)
    if cand.is_stop
        grp = 3;
        seq_penalty = 0;
    elseif isfinite(seq_target) && double(cand.seq) == double(seq_target)
        grp = 1;
        seq_penalty = 0;
    else
        grp = 2;
        seq_penalty = double(cand.seq);
    end

    dist = abs(double(cand.k) - double(expected_k));
    key = [grp, seq_penalty, dist];
end


function tf = lexicographically_better_simple(a, b)
    tf = false;
    for i = 1:numel(a)
        if a(i) < b(i)
            tf = true;
            return;
        elseif a(i) > b(i)
            return;
        end
    end
end


function r = preamble_score_at_k_simple(x_tape, k, p, sync)
    k = round(double(k));
    if k < 1 || (k + p.Lpre - 1) > numel(x_tape)
        r = 0;
        return;
    end
    r = pa_corr_ratio_v03(x_tape(k:k+p.Lpre-1), sync.win_preamble);
end


function lut = make_tx_lut_simple(tx_index)
    lut = struct();
    lut.N = height(tx_index);
    lut.pa_id = uint16(tx_index.pa_id(:));
    lut.wid = uint16(tx_index.window_id(:));
end


function pa = id_to_pa_simple(pa_id)
    switch double(pa_id)
        case 1, pa = "PA1";
        case 2, pa = "PA2";
        case 3, pa = "PA3";
        case 4, pa = "PA4";
        case 5, pa = "PA5";
        case 6, pa = "PA6";
        case 7, pa = "PA7";
        case 8, pa = "PA8";
        otherwise, pa = "";
    end
end


function [x_d, Fs_d, ok] = load_digital_by_window_id_simple(data_root, pa, wid)
    f = fullfile(data_root, sprintf("pilot_S01_%s.mat", pa));
    if ~isfile(f)
        x_d = []; Fs_d = []; ok = false; return;
    end
    S = load(f, "Xsig_all", "meta");
    ids = arrayfun(@(m) double(m.window_id), S.meta);
    j = find(ids == wid, 1, "first");
    if isempty(j)
        x_d = []; Fs_d = []; ok = false; return;
    end
    x_d = S.Xsig_all(:,j);
    Fs_d = double(S.meta(j).fs_hz);
    ok = true;
end


function plot_pair_dig_vs_ota_simple(pa, x_d, Fs_d, x_o, Fs_o, out_png)
    nfft = 1024; hop = 256; win = hann(nfft, "periodic");
    td = (0:numel(x_d)-1)/Fs_d*1e3;
    to = (0:numel(x_o)-1)/Fs_o*1e3;

    f = figure("Visible","off","Color","w","Position",[100 100 1700 950]);
    tiledlayout(2,2,"Padding","compact","TileSpacing","compact");

    nexttile;
    [Sd,Fd,Td2] = spectrogram(x_d, win, nfft-hop, nfft, Fs_d, "centered");
    imagesc(Td2*1e3, Fd/1e6, 10*log10(abs(Sd).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)"); title(string(pa)+" (DIG)"); colorbar;

    nexttile;
    [So,Fo,To2] = spectrogram(x_o, win, nfft-hop, nfft, Fs_o, "centered");
    imagesc(To2*1e3, Fo/1e6, 10*log10(abs(So).^2 + 1e-12));
    axis xy; xlabel("Time (ms)"); ylabel("Freq (MHz)"); title(string(pa)+" (OTA)"); colorbar;

    nexttile;
    plot(td, real(x_d)); hold on; plot(td, imag(x_d), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q"); title("Waveform (DIG)");
    legend("I","Q","Location","northeast");

    nexttile;
    plot(to, real(x_o)); hold on; plot(to, imag(x_o), "--");
    grid on; xlabel("Time (ms)"); ylabel("I / Q"); title("Waveform (OTA)");
    legend("I","Q","Location","northeast");

    exportgraphics(f, out_png);
    close(f);
end


function h = empty_hdr_simple()
    h = struct("k", int64(0), "pa_id", uint16(0), "pa", "", ...
        "wid", uint16(0), "seq", uint16(0), "is_stop", false, "r", NaN);
end


function m = empty_meta_simple()
    m = struct( ...
        "schema_version", "", ...
        "protocol", "", ...
        "session_id", 0, ...
        "tape_id", 0, ...
        "segment_id", 0, ...
        "window_id", uint16(0), ...
        "pa_type", "", ...
        "fs_hz", 0, ...
        "window_length_s", 0, ...
        "seq", uint16(0), ...
        "k_ph", int64(0), ...
        "k_next", int64(0), ...
        "gap_to_next", int64(0), ...
        "header_r", NaN);
end


function d = empty_drop_simple()
    d = struct( ...
        "seq", uint16(0), ...
        "pa_type", "", ...
        "window_id", uint16(0), ...
        "k_hdr", int64(0), ...
        "k_next", int64(0), ...
        "gap", int64(0), ...
        "reason", "");
end


function shard_num = validate_shard_id_simple(shard_id)
    if ~(isnumeric(shard_id) || islogical(shard_id)) || numel(shard_id) ~= 1 || ~isfinite(double(shard_id))
        error("shard_id must be a finite scalar integer.");
    end
    shard_num = double(shard_id);
    if abs(shard_num - round(shard_num)) > 0 || shard_num < 1
        error("shard_id must be a positive integer.");
    end
    shard_num = round(shard_num);
end


function data_root = pilot_root_from_protocol_simple(protocol)
    root = pa_root();
    switch string(protocol)
        case "wifi"
            data_root = fullfile(root, "data", "wifi", "digital", "pilot");
        case "bluetooth"
            data_root = fullfile(root, "data", "bluetooth", "digital", "pilot");
        case "zigbee"
            data_root = fullfile(root, "data", "zigbee", "digital", "pilot");
        otherwise
            error("Unknown protocol %s", protocol);
    end
end


function debug_fallback_window_simple(x_tape, lo, hi, p, tx_lut)
    fprintf("DEBUG FALLBACK WINDOW | [%d, %d]\n", lo, hi);

    n_print = 0;
    max_print = 40;

    for k = lo:hi
        [info, ok_any] = raw_decode_header_debug_simple(x_tape, k, p, tx_lut);
        if ~ok_any
            continue;
        end

        n_print = n_print + 1;
        fprintf("  k=%d | crc_ok=%d | pa_id=%d | wid=%d | seq=%d | pa=%s | lut_ok=%d | is_stop=%d\n", ...
            k, info.crc_ok, info.pa_id, info.wid, info.seq, info.pa, info.lut_ok, info.is_stop);

        if n_print >= max_print
            fprintf("  ... truncated debug output after %d hits ...\n", max_print);
            break;
        end
    end

    if n_print == 0
        fprintf("  No decodable header-like candidates in this window.\n");
    end
end


function [info, ok_any] = raw_decode_header_debug_simple(x_tape, k, p, tx_lut)
    info = struct( ...
        "k", int64(k), ...
        "crc_ok", false, ...
        "pa_id", uint16(0), ...
        "wid", uint16(0), ...
        "seq", uint16(0), ...
        "pa", "", ...
        "lut_ok", false, ...
        "is_stop", false);

    ok_any = false;

    k = round(double(k));
    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    if k < 1 || k > kmax
        return;
    end

    hdr_samp = x_tape(k + p.Lpre + (1:p.Lhdr));
    [pa_id, wid, seq, crc_ok] = pa_dbpsk_header_decode_v03(hdr_samp, p.spsHdr);

    info.crc_ok = logical(crc_ok);
    info.pa_id = uint16(pa_id);
    info.wid   = uint16(wid);
    info.seq   = uint16(seq);

    if ~crc_ok
        return;
    end

    ok_any = true;

    is_stop = (double(pa_id) == 15) && (double(wid) == 65535) && (double(seq) == 65535);
    info.is_stop = is_stop;

    if is_stop
        info.pa = "STOP";
        info.lut_ok = true;
        return;
    end

    pa = id_to_pa_simple(uint16(pa_id));
    info.pa = pa;

    s = double(seq);
    if pa ~= "" && s >= 1 && s <= tx_lut.N
        info.lut_ok = (tx_lut.pa_id(s) == uint16(pa_id)) && (tx_lut.wid(s) == uint16(wid));
    else
        info.lut_ok = false;
    end
end

function [nxt, ok, skip_used, expected_k_skip] = try_auto_skip_header_simple( ...
    x_tape, cur, p, tx_lut, auto_skip_records, auto_skip_search_radius)

    nxt = empty_hdr_simple();
    ok = false;
    skip_used = 0;
    expected_k_skip = [];

    if auto_skip_records <= 0
        return;
    end

    Lrec = double(p.frameLen) + double(p.W) + double(p.guardN);
    base_expected_k = double(cur.k) + Lrec;

    for nskip = 1:auto_skip_records
        target_k = base_expected_k + nskip * Lrec;
        expected_k_skip = target_k;

        tried_centers = target_k + (-3:3) * double(p.frameLen);

        fprintf("  AUTO SKIP TRY | skip_records=%d | target_k=%d\n", nskip, round(target_k));

        best = empty_hdr_simple();
        ok_best = false;

        for i = 1:numel(tried_centers)
            center = tried_centers(i);
            lo = round(center - auto_skip_search_radius);
            hi = round(center + auto_skip_search_radius);

            fprintf("    auto-skip center %d | window [%d, %d]\n", round(center), lo, hi);

            [cand, okc] = search_header_near_simple( ...
                x_tape, center, auto_skip_search_radius, p, tx_lut, uint16(cur.seq), target_k);

            if okc
                fprintf("      auto-skip candidate | seq=%d | pa=%s | wid=%d | k=%d\n", ...
                    cand.seq, cand.pa, cand.wid, cand.k);
            end

            if okc && (~ok_best || cand_better_simple(cand, best, cur, target_k))
                best = cand;
                ok_best = true;
            end
        end

        if ok_best
            nxt = best;
            ok = true;
            skip_used = nskip;
            return;
        end
    end
end


function [hdr, ok, lo_hit, hi_hit, block_idx] = search_first_header_blocks_simple( ...
    x_tape, start_k, p, tx_lut, seq_floor, span_samp, max_blocks)
% Scan repeated contiguous blocks [start,start+span-1], then the next block, etc.
% Early-exit on the first valid header.

    hdr = empty_hdr_simple();
    ok = false;

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    span_samp = max(1, round(double(span_samp)));

    lo = max(1, round(double(start_k)));
    lo_hit = lo;
    hi_hit = min(kmax, lo + span_samp - 1);
    block_idx = 0;

    while lo <= kmax && block_idx < max_blocks
        block_idx = block_idx + 1;
        hi = min(kmax, lo + span_samp - 1);

        fprintf("BOOTSTRAP HARD BLOCK | block=%d | scanning [%d,%d]\n", block_idx, lo, hi);

        [cand, okc] = search_first_header_in_range_simple( ...
            x_tape, lo, hi, p, tx_lut, seq_floor);

        lo_hit = lo;
        hi_hit = hi;

        if okc
            hdr = cand;
            ok = true;
            return;
        end

        lo = hi + 1;
    end
end


function [nxt, ok, lo_hit, hi_hit, block_idx] = hard_reacquire_next_header_blocks_simple( ...
    x_tape, expected_k, cur, p, tx_lut, slip_frames, search_radius, span_samp, max_blocks)
% Scan repeated contiguous blocks starting near expected_k.
% Early-exit on the first valid header with seq > cur.seq.

    nxt = empty_hdr_simple();
    ok = false;

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    span_samp = max(1, round(double(span_samp)));

    max_slip = max(abs(double(slip_frames))) * double(p.frameLen);

    % Start at the same conservative lower edge used by the previous hard reacquire,
    % then scan forward in contiguous span_samp blocks.
    lo = max(1, round(double(expected_k) - max_slip - double(search_radius)));
    lo_hit = lo;
    hi_hit = min(kmax, lo + span_samp - 1);
    block_idx = 0;

    seq_floor = uint16(cur.seq);

    while lo <= kmax && block_idx < max_blocks
        block_idx = block_idx + 1;
        hi = min(kmax, lo + span_samp - 1);

        fprintf("HARD REACQUIRE BLOCK | block=%d | scanning [%d,%d]\n", block_idx, lo, hi);

        for k = lo:hi
            [cand, okc] = raw_decode_valid_header_at_k_simple(x_tape, k, p, tx_lut, seq_floor);
            if okc
                nxt = cand;
                ok = true;
                lo_hit = lo;
                hi_hit = hi;
                return;
            end
        end

        lo_hit = lo;
        hi_hit = hi;
        lo = hi + 1;
    end
end


function [nxt, ok, lo, hi] = hard_reacquire_next_header_simple( ...
    x_tape, expected_k, cur, p, tx_lut, slip_frames, search_radius, span_samp)

    nxt = empty_hdr_simple();
    ok = false;

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    max_slip = max(abs(double(slip_frames))) * double(p.frameLen);

    % Scan forward from near expected_k across one record span.
    lo = max(1, round(double(expected_k) - max_slip - double(search_radius)));
    hi = min(kmax, round(double(expected_k) + double(span_samp) + max_slip + double(search_radius)));

    % IMPORTANT: return the FIRST valid header hit in increasing-k order.
    % This is deterministic and avoids scanning the whole range for "best".
    seq_floor = uint16(cur.seq);

    for k = lo:hi
        [cand, okc] = raw_decode_valid_header_at_k_simple(x_tape, k, p, tx_lut, seq_floor);
        if okc
            nxt = cand;
            ok = true;
            return;
        end
    end
end

function [hdr, ok] = search_first_header_in_range_simple(x_tape, lo, hi, p, tx_lut, seq_floor)
% Return FIRST valid header in [lo,hi] (early-exit)
    hdr = empty_hdr_simple();
    ok = false;

    kmax = numel(x_tape) - (p.frameLen + p.W) + 1;
    lo = max(1, round(lo));
    hi = min(kmax, round(hi));
    if hi < lo, return; end

    for k = lo:hi
        [cand, okc] = raw_decode_valid_header_at_k_simple(x_tape, k, p, tx_lut, seq_floor);
        if okc
            hdr = cand;
            ok = true;
            return; % EARLY EXIT
        end
    end
end
