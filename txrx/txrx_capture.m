function txrx_cfg = txrx_capture(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id_or_tape_file, shard_id, varargin)
%TXRX_CAPTURE Same-host coordinated TX/RX capture for one shard.
%
% NEW: optional quality gate that can abort BEFORE saving.
%   Name/Value options:
%     'quality_enable'        (default false)
%     'quality_max_events'    (default inf)   % capture_overruns + capture_underruns
%     'quality_min_fill_frac' (default 0.0)   % filled/Ncap
%     'quality_save_meta_on_fail' (default false) % if true, saves ONLY txrx_cfg/rx_cfg on failure
%
% If quality_enable=true and gate fails, the function errors and does NOT save x_tape.

    % --------- argument handling ---------
    if nargin < 6
        error("Usage: txrx_capture(protocol, tx_ip, rx_ip, fc_hz, tx_gain_db, rx_gain_db, ant, dataset_id, shard_id)");
    end
    if nargin < 7 || isempty(ant)
        ant = "TX/RX";
    end
    if nargin < 8
        dataset_id_or_tape_file = [];
    end
    if nargin < 9
        shard_id = [];
    end

    % --------- options ---------
    ip = inputParser;
    ip.addParameter("quality_enable", false, @(x) islogical(x) || isnumeric(x));
    ip.addParameter("quality_max_events", inf, @(x) isnumeric(x) && isscalar(x) && isfinite(x));
    ip.addParameter("quality_min_fill_frac", 0.0, @(x) isnumeric(x) && isscalar(x) && x >= 0 && x <= 1);
    ip.addParameter("quality_save_meta_on_fail", false, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'save_chunk_samples', 5e6, @(x) isnumeric(x) && isscalar(x) && x >= 1);
    ip.parse(varargin{:});

    quality_enable = logical(ip.Results.quality_enable);
    quality_max_events = double(ip.Results.quality_max_events);
    quality_min_fill_frac = double(ip.Results.quality_min_fill_frac);
    quality_save_meta_on_fail = logical(ip.Results.quality_save_meta_on_fail);
    save_chunk_samples = round(double(ip.Results.save_chunk_samples));

    protocol_s = string(protocol);
    assert(any(protocol_s == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    % --------- robust repo root resolution ---------
    if exist('pa_root', 'file') == 2
        root = pa_root();
    else
        this_file = mfilename('fullpath');
        this_dir = fileparts(this_file);
        if strcmp(string(fileparts(this_dir)), "txrx")
            root = fileparts(this_dir);
        else
            root = this_dir;
        end
    end

    addpath(fullfile(root, 'core'));
    addpath(fullfile(root, 'txrx'));
    addpath(fullfile(root, 'tools'));
    if isfolder(fullfile(root, 'protocol'))
        addpath(genpath(fullfile(root, 'protocol')));
    end

    R = pa_protocol_roots(protocol_s);

    [tape_file, spec_file, out_file, dataset_full, shard_num] = ...
        resolve_txrx_files(protocol_s, R, dataset_id_or_tape_file, shard_id);

    % --------- load TX artifacts before any radio work ---------
    St = load(tape_file, "tx_tape", "tx_params", "sync");
    Ss = load(spec_file, "tx_spec");

    tx_tape = St.tx_tape(:);
    tx_tape = complex(single(real(tx_tape)), single(imag(tx_tape)));

    p = St.tx_params;
    sync = St.sync;
    tx_spec = Ss.tx_spec; %#ok<NASGU>

    % Frame view once up front so main loop does not keep slicing tx_tape
    frameLen = double(p.frameLen);
    assert(mod(numel(tx_tape), frameLen) == 0, "tx_tape must be a multiple of frameLen");
    tx_frames = reshape(tx_tape, frameLen, []);

    % Dense pre-touch of tx_tape to reduce first-touch stalls
    fprintf("TXRX PRETOUCH | touching tx_tape pages...\n");
    page_elems = 512; % ~4 KiB per page for complex single
    tx_touch_idx = 1:page_elems:numel(tx_tape);
    tx_tape(tx_touch_idx) = tx_tape(tx_touch_idx);
    tx_tape(end) = tx_tape(end);
    fprintf("TXRX PRETOUCH DONE | tx_tape pages touched.\n");

    out_dir = fileparts(out_file);
    if ~exist(out_dir, 'dir')
        mkdir(out_dir);
    end

    % --------- radio settings ---------
    mcr = 100e6;
    interp = round(mcr / 12e6);
    decim  = round(mcr / 12e6);
    Fs = mcr / decim;

    fprintf("TXRX | protocol=%s | dataset=%s | shard=%03d\n", protocol_s, dataset_full, shard_num);
    fprintf("TXRX | tape=%s\n", tape_file);
    fprintf("TXRX | spec=%s\n", spec_file);
    fprintf("TXRX | out =%s\n", out_file);
    fprintf("TXRX | TX ip=%s | RX ip=%s | Fc=%.6f GHz | TX gain=%.1f dB | RX gain=%.1f dB | Fs=%.6f MS/s\n", ...
        tx_ip, rx_ip, fc_hz/1e9, tx_gain_db, rx_gain_db, Fs/1e6);

    % --------- timing knobs ---------
    auto_go_after_s = 10.0;
    settle_pause_s  = 10.0;

    % --------- capture plan ---------
    n_guard_pre_frames  = 1;
    n_guard_post_frames = 20.75;

    trim_front_samples = 2100000;

    Nmain = numel(tx_tape);
    assert(mod(Nmain, frameLen) == 0, "tx_tape must be a multiple of frameLen");

    n_main_frames = Nmain / frameLen;
    Npre_guard  = n_guard_pre_frames  * frameLen;
    Npost_guard = n_guard_post_frames * frameLen;
    Ncap = Npre_guard + Nmain + Npost_guard;

    cap_gib = double(Ncap) * 8 / (1024^3);
    fprintf("TXRX PLAN | beacon_warmup=%.2f s | preroll=%d frames | main=%d frames | postroll=%d frames | Ncap=%d samples | est_mem=%.2f GiB\n", ...
        auto_go_after_s, n_guard_pre_frames, n_main_frames, n_guard_post_frames, Ncap, cap_gib);

    % --------- preallocate capture RAM before beacon/monitor ---------
    x_tape = complex(zeros(Ncap,1,'single'), zeros(Ncap,1,'single'));
    fprintf("TXRX PREALLOC DONE | x_tape ready before beacon phase.\n");

    % --------- pre-touch x_tape pages ---------
    fprintf("TXRX PRETOUCH | touching capture buffer pages...\n");
    idx = 1:page_elems:Ncap;
    x_tape(idx) = complex(single(0), single(0));
    x_tape(end) = complex(single(0), single(0));
    fprintf("TXRX PRETOUCH DONE | capture buffer pages touched.\n");

    % --------- TX beacon frame ---------
    beacon = complex(zeros(p.frameLen,1,"single"), zeros(p.frameLen,1,"single"));
    bp = single(sync.beacon_preamble(:));
    bp = bp(1:p.Lpre);
    bp_c = bp .* complex(single(1/sqrt(2)), single(1/sqrt(2)));
    beacon(1:p.Lpre) = bp_c;

    % --------- create radios ---------
    tx = comm.SDRuTransmitter( ...
        "Platform","N200/N210/USRP2", ...
        "IPAddress", tx_ip, ...
        "CenterFrequency", fc_hz, ...
        "Gain", tx_gain_db, ...
        "MasterClockRate", mcr, ...
        "InterpolationFactor", interp, ...
        "ChannelMapping", 1);

    rx = comm.SDRuReceiver( ...
        "Platform","N200/N210/USRP2", ...
        "IPAddress", rx_ip, ...
        "CenterFrequency", fc_hz, ...
        "Gain", rx_gain_db, ...
        "MasterClockRate", mcr, ...
        "DecimationFactor", decim, ...
        "SamplesPerFrame", p.frameLen, ...
        "OutputDataType","single", ...
        "ChannelMapping", 1);

    if ~isempty(ant)
        if isprop(tx, "Antenna"), tx.Antenna = ant; end
        if isprop(rx, "Antenna"), rx.Antenna = ant; end
    end

    overruns = 0;
    underruns = 0;
    filled = 0;

    report_every = max(1, ceil(n_main_frames / 10));

    % pre-init for catch path
    capture_overruns = 0;
    capture_underruns = 0;
    expected_main_start_sample = NaN;
    detected_start_sample = NaN;

    try
        % --------- RX warmup ---------
        fprintf("TXRX | RX warmup...\n");
        for w = 1:50
            [~,~,ov] = rx();
            if ov, overruns = overruns + 1; end
        end
        fprintf("TXRX | RX warmup done.\n");

        % --------- beacon warmup phase (not stored) ---------
        fprintf("TXRX | beacon warmup for %.2f s before main tape...\n", auto_go_after_s);
        t_beacon = tic;
        beacon_frames = 0;
        t_beacon_log = tic;

        while toc(t_beacon) < auto_go_after_s
            underruns = underruns + double(tx(beacon));
            beacon_frames = beacon_frames + 1;

            [~,~,ov] = rx();
            if ov, overruns = overruns + 1; end

            if toc(t_beacon_log) > 1.0
                fprintf("TXRX BEACON | elapsed=%.1fs | frames=%d | underruns=%d | overruns=%d\n", ...
                    toc(t_beacon), beacon_frames, underruns, overruns);
                t_beacon_log = tic;
            end
        end

        fprintf("TXRX | settle pause %.2f s before captured preroll/main/postroll...\n", settle_pause_s);
        pause(settle_pause_s);

        % Flush after settle
        fprintf("TXRX | RX flush after settle...\n");
        for w = 1:20
            [~,~,ov] = rx();
            if ov, overruns = overruns + 1; end
        end
        fprintf("TXRX | RX flush done.\n");

        % Reset captured-phase counters
        capture_overruns = 0;
        capture_underruns = 0;

        t_all = tic;

        % --------- captured preroll ----------
        fprintf("TXRX | captured preroll beacon frames...\n");
        for k = 1:n_guard_pre_frames
            u = double(tx(beacon));
            underruns = underruns + u;
            capture_underruns = capture_underruns + u;

            [y, len, ov] = rx();
            if ov
                overruns = overruns + 1;
                capture_overruns = capture_overruns + 1;
            end

            if len > 0
                take = min(double(len), Ncap - filled);
                x_tape(filled + (1:take)) = y(1:take);
                filled = filled + take;
            end
        end

        expected_main_start_sample = filled + 1;
        fprintf("TXRX | expected main start sample = %d\n", expected_main_start_sample);

        % --------- main tape ----------
        fprintf("TXRX | streaming main tape...\n");
        for k = 1:n_main_frames
            u = double(tx(tx_frames(:,k)));
            underruns = underruns + u;
            capture_underruns = capture_underruns + u;

            [y, len, ov] = rx();
            if ov
                overruns = overruns + 1;
                capture_overruns = capture_overruns + 1;
            end

            if len > 0
                take = min(double(len), Ncap - filled);
                x_tape(filled + (1:take)) = y(1:take);
                filled = filled + take;
            end

            if mod(k, report_every) == 0 || k == n_main_frames
                fprintf("TXRX MAIN | %d/%d frames | filled=%d/%d samples | capture_underruns=%d | capture_overruns=%d | elapsed=%.1fs\n", ...
                    k, n_main_frames, filled, Ncap, capture_underruns, capture_overruns, toc(t_all));
            end
        end

        % --------- captured postroll ----------
        fprintf("TXRX | captured postroll beacon frames...\n");
        for k = 1:n_guard_post_frames
            u = double(tx(beacon));
            underruns = underruns + u;
            capture_underruns = capture_underruns + u;

            [y, len, ov] = rx();
            if ov
                overruns = overruns + 1;
                capture_overruns = capture_overruns + 1;
            end

            if len > 0
                take = min(double(len), Ncap - filled);
                x_tape(filled + (1:take)) = y(1:take);
                filled = filled + take;
            end
        end

        if filled < Ncap
            fprintf("TXRX WARN | filled only %d/%d samples; trailing region remains zero.\n", filled, Ncap);
        end

        % --------- QUALITY GATE (BEFORE ALIGN/TRIM/SAVE) ----------
        gate_events = double(capture_overruns + capture_underruns);
        gate_fill_frac = double(filled) / double(Ncap);

        fprintf("TXRX GATE | events=%d (max=%g) | fill_frac=%.6f (min=%.6f)\n", ...
            gate_events, quality_max_events, gate_fill_frac, quality_min_fill_frac);

        if quality_enable && (gate_events > quality_max_events || gate_fill_frac < quality_min_fill_frac)
            % build minimal cfg for optional meta save
            txrx_cfg = struct();
            txrx_cfg.protocol = char(protocol_s);
            txrx_cfg.dataset_full = char(dataset_full);
            txrx_cfg.shard_num = shard_num;
            txrx_cfg.fc_hz = fc_hz;
            txrx_cfg.tx_gain_db = tx_gain_db;
            txrx_cfg.rx_gain_db = rx_gain_db;
            txrx_cfg.Fs = Fs;
            txrx_cfg.frameLen = p.frameLen;
            txrx_cfg.n_guard_pre_frames = n_guard_pre_frames;
            txrx_cfg.n_main_frames = n_main_frames;
            txrx_cfg.n_guard_post_frames = n_guard_post_frames;
            txrx_cfg.Ncap_expected = Ncap;
            txrx_cfg.capture_len_raw = filled;
            txrx_cfg.capture_overruns = capture_overruns;
            txrx_cfg.capture_underruns = capture_underruns;
            txrx_cfg.gate_events = gate_events;
            txrx_cfg.gate_fill_frac = gate_fill_frac;
            txrx_cfg.gate_ok = false;
            txrx_cfg.capture_time = datetime("now");

            rx_cfg = txrx_cfg; %#ok<NASGU>

            release(tx);
            release(rx);

            if quality_save_meta_on_fail
                fprintf("TXRX GATE FAIL | saving META ONLY (no x_tape): %s\n", out_file);
                save(out_file, "rx_cfg", "txrx_cfg", "-v7");
            else
                fprintf("TXRX GATE FAIL | NOT saving tape (no x_tape).\n");
            end

            error("TXRX_GATED_FAIL | events=%d (max=%g) | fill_frac=%.6f (min=%.6f)", ...
                gate_events, quality_max_events, gate_fill_frac, quality_min_fill_frac);
        end

        % --------- local fine alignment near expected start ----------
        search_left  = max(1, expected_main_start_sample - 2*p.frameLen);
        search_right = min(Ncap, expected_main_start_sample + 4*p.frameLen);
        local_buf = x_tape(search_left:search_right);

        [k_local, ratio] = find_preamble_in_buffer(local_buf, sync.start_preamble);
        if isempty(k_local)
            detected_start_sample = NaN;
            fprintf("TXRX ALIGN | local fine-align failed near expected start.\n");
        else
            detected_start_sample = search_left + k_local - 1;
            fprintf("TXRX ALIGN | expected=%d | detected=%d | delta=%d samples | ratio=%.1f\n", ...
                expected_main_start_sample, detected_start_sample, ...
                detected_start_sample - expected_main_start_sample, ratio);
        end
        
        % --------- fixed front trim + save (ATOMIC CHUNKED) ----------
        trim_front_samples = min(trim_front_samples, filled - 1);
        save_start = trim_front_samples + 1;
        save_len = filled - trim_front_samples;
        
        txrx_cfg = struct();
        txrx_cfg.protocol = char(protocol_s);
        txrx_cfg.dataset_full = char(dataset_full);
        txrx_cfg.shard_num = shard_num;
        txrx_cfg.tx_ip = tx_ip;
        txrx_cfg.rx_ip = rx_ip;
        txrx_cfg.fc_hz = fc_hz;
        txrx_cfg.tx_gain_db = tx_gain_db;
        txrx_cfg.rx_gain_db = rx_gain_db;
        txrx_cfg.ant = char(string(ant));
        txrx_cfg.Fs = Fs;
        txrx_cfg.frameLen = p.frameLen;
        txrx_cfg.auto_go_after_s = auto_go_after_s;
        txrx_cfg.settle_pause_s  = settle_pause_s;
        txrx_cfg.n_guard_pre_frames  = n_guard_pre_frames;
        txrx_cfg.n_main_frames       = n_main_frames;
        txrx_cfg.n_guard_post_frames = n_guard_post_frames;
        txrx_cfg.expected_main_start_sample = expected_main_start_sample;
        txrx_cfg.detected_start_sample      = detected_start_sample;
        
        txrx_cfg.capture_overruns  = capture_overruns;
        txrx_cfg.capture_underruns = capture_underruns;
        txrx_cfg.overruns  = overruns;
        txrx_cfg.underruns = underruns;
        
        txrx_cfg.capture_len_raw   = filled;
        txrx_cfg.trim_front_samples = trim_front_samples;
        txrx_cfg.capture_len_saved  = save_len;
        txrx_cfg.gate_ok = true;
        txrx_cfg.capture_time = datetime("now");
        
        rx_cfg = txrx_cfg; %#ok<NASGU> for compatibility with existing loaders
        
        fprintf("TXRX TRIM | dropped first %d samples | saving %d samples\n", ...
            trim_front_samples, save_len);
        
        % Release radios BEFORE disk IO
        release(tx);
        release(rx);
        
        % Free big TX buffers before disk write (reduce peak RAM)
        clear tx_frames tx_tape
        
        % --------- atomic chunked save (prevents partial .mat on OOM/crash) ----------
        tmp_file = out_file + ".tmp";
        if isfile(tmp_file), delete(tmp_file); end
        
        fprintf("TXRX SAVE | chunked write to tmp: %s\n", tmp_file);
        
        OUT = matfile(tmp_file, "Writable", true);
        
        % pre-extend x_tape on disk (v7.3 by construction)
        OUT.x_tape(save_len, 1) = complex(single(0), single(0));
        OUT.rx_cfg = rx_cfg;
        OUT.txrx_cfg = txrx_cfg;
        
        chunk = save_chunk_samples;
        i0 = 1;
        t_save = tic;
        last_print = 0;
        
        while i0 <= save_len
            i1 = min(save_len, i0 + chunk - 1);
            src0 = save_start + (i0 - 1);
            src1 = save_start + (i1 - 1);
            OUT.x_tape(i0:i1, 1) = x_tape(src0:src1);
            i0 = i1 + 1;
        
            % progress print every ~30s
            if toc(t_save) - last_print > 30
                frac = (i0-1) / save_len;
                fprintf("TXRX SAVE | progress=%.1f%% | i=%d/%d\n", 100*frac, i0-1, save_len);
                last_print = toc(t_save);
                drawnow(); % flush stdout in -batch
            end
        end
        
        clear OUT
        
        % promote tmp -> final atomically
        if isfile(out_file), delete(out_file); end
        movefile(tmp_file, out_file, "f");
        
        fprintf("TXRX DONE | saved tape: %s\n", out_file);
        fprintf("TXRX DONE | total_underruns=%d | total_overruns=%d | capture_underruns=%d | capture_overruns=%d | raw_filled=%d | saved=%d\n", ...
    underruns, overruns, capture_underruns, capture_overruns, filled, save_len);
        
    catch ME
        try, release(tx); end %#ok<TRYNC>
        try, release(rx); end %#ok<TRYNC>
        rethrow(ME);
    end
end


function [tape_file, spec_file, out_file, dataset_full, shard_num] = resolve_txrx_files(protocol_s, R, dataset_id_or_tape_file, shard_id)
    dataset_full = "";
    shard_num = [];

    if isempty(dataset_id_or_tape_file)
        tape_file = fullfile(R.txrx_tapes_digital, "tx_tape.mat");
        spec_file = fullfile(R.txrx_tapes_digital, "tx_spec.mat");
        out_file  = fullfile(R.txrx_tapes_ota, "ota_tape_S01.mat");
        return;
    end

    arg6 = string(dataset_id_or_tape_file);
    if strlength(arg6) == 0
        tape_file = fullfile(R.txrx_tapes_digital, "tx_tape.mat");
        spec_file = fullfile(R.txrx_tapes_digital, "tx_spec.mat");
        out_file  = fullfile(R.txrx_tapes_ota, "ota_tape_S01.mat");
        return;
    end

    if endsWith(lower(arg6), ".mat")
        error("Override .mat mode is not implemented in txrx_capture; use dataset_id + shard_id.");
    end

    if isempty(shard_id)
        error("When dataset_id is provided, shard_id is also required.");
    end

    shard_num = validate_shard_id(shard_id);
    dataset_full = normalize_dataset_id(protocol_s, arg6);

    tape_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_tape_shard_%03d.mat", shard_num));
    spec_file = fullfile(R.txrx_tapes_digital, char(dataset_full), sprintf("tx_spec_shard_%03d.mat", shard_num));
    out_file  = fullfile(R.txrx_tapes_ota,    char(dataset_full), sprintf("ota_tape_shard_%03d.mat", shard_num));

    if ~isfile(tape_file)
        error("TX tape file not found: %s", tape_file);
    end
    if ~isfile(spec_file)
        error("TX spec file not found: %s", spec_file);
    end
end


function [k0, best_ratio] = find_preamble_in_buffer(buf, pre)
    buf = double(buf(:));
    pre = double(pre(:));

    nfft = 2^nextpow2(numel(buf) + numel(pre) - 1);
    C = ifft(fft(buf, nfft) .* fft(conj(flipud(pre)), nfft));
    c = abs(C(numel(pre):numel(pre) + numel(buf) - 1));

    [pk, idx] = max(c);
    med = median(c) + 1e-12;
    best_ratio = pk / med;

    if best_ratio < 20
        k0 = [];
    else
        k0 = idx;
    end
end


function dataset_full = normalize_dataset_id(protocol_s, dataset_id)
    dataset_id = string(dataset_id);
    prefix = protocol_s + "_";
    if startsWith(dataset_id, prefix)
        dataset_full = dataset_id;
    else
        dataset_full = prefix + dataset_id;
    end
end


function shard_num = validate_shard_id(shard_id)
    if ~(isnumeric(shard_id) || islogical(shard_id)) || numel(shard_id) ~= 1 || ~isfinite(double(shard_id))
        error("shard_id must be a finite scalar integer.");
    end
    shard_num = double(shard_id);
    if abs(shard_num - round(shard_num)) > 0 || shard_num < 1
        error("shard_id must be a positive integer.");
    end
    shard_num = round(shard_num);
end