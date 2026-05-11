function [T, summary] = validate(input_spec, cfg)
%OTA_VALIDATE_WINDOWS
% Notebook-facing OTA validator for respliced OTA windows.
%
% Philosophy:
%   - Negative-evidence validator for OTA, not a strict exemplar generator.
%   - Decide among {main_usable, stress_only, reject}.
%   - Use generic OTA integrity QC + label-consistency checks.
%   - Does NOT try to infer the true PA; only checks whether the labeled PA
%     is clearly contradicted.
%
% Expected resplice layout (from rx_resplice_tape_simple):
%   data/<protocol>/ota/spliced/simple/<dataset_id>/shard_###/ota_rx_<PA>.mat
%
% Each OTA file should contain:
%   Xrx_all  [W x N] complex
%   meta_rx  [1 x N] struct array
%   rx_cfg   struct with Fs
%
% ------------------------------------------------------------
% NOTEBOOK USAGE MODES
% ------------------------------------------------------------
% 1) Filtered enumeration:
%    input_spec.protocols  = "wifi";
%    input_spec.dataset_ids = "wifi_high_run01";
%    input_spec.shard_ids   = [1 2 3];
%    input_spec.pas         = ["PA2","PA3"];
%    input_spec.sample_mode = "random_n";   % {"all","first_n","random_n"}
%    input_spec.n_per_file  = 100;
%    input_spec.random_seed = 0;
%
% 2) Exact sample selection:
%    input_spec.records = table(protocol, dataset_id, shard_id, pa_type, column_idx)
%
% 3) Optional window-ID filtering:
%    input_spec.window_ids = [10 12 14 99];
%
% ------------------------------------------------------------
% OUTPUT
% ------------------------------------------------------------
% T: table with one row per validated OTA sample
% summary: struct with simple count summaries
%
% ------------------------------------------------------------
% FINAL BINNING
% ------------------------------------------------------------
% generic integrity: {main_usable, stress_only, reject}
% semantic label:    {consistent, borderline, contradictory}
% final_bin:         {main_usable, stress_only, reject}

    if nargin < 1 || isempty(input_spec), input_spec = struct(); end
    if nargin < 2 || isempty(cfg), cfg = struct(); end

    root = pa_root();
    input_spec = normalize_input_spec_(input_spec, root);
    cfg = merge_structs_(default_cfg_(), cfg);

    records = resolve_records_(input_spec);
    n = numel(records);

    if n == 0
        T = struct2table(repmat(empty_row_(), 0, 1));
        summary = empty_summary_();
        return;
    end

    rows = repmat(empty_row_(), n, 1);

    for i = 1:n
        rec = records(i);

        [x, meta_i, rx_cfg] = load_one_selected_window_(rec);
        Fs = double(rx_cfg.Fs);

        gen = ota_generic_qc_(x, Fs, cfg);
        sem = ota_semantic_check_(x, Fs, string(rec.pa_type), cfg);
        final = merge_generic_semantic_(gen, sem, cfg);

        rows(i) = build_row_(rec, meta_i, Fs, gen, sem, final);

        if cfg.runtime.verbose && mod(i, max(1, cfg.runtime.print_every)) == 0
            fprintf([ ...
                'OTA VALIDATE | %d / %d | %s | %s | shard_%03d | %s | col=%d' ...
                ' | integrity=%s(%.2f) | semantic=%s(%.2f) | final=%s' ...
                ' | gen=[%s] | sem=[%s]\n'], ...
                i, n, safe_char_(rec.protocol), safe_char_(rec.dataset_id), rec.shard_id, safe_char_(rec.pa_type), rec.column_idx, ...
                safe_char_(gen.label), gen.score, ...
                safe_char_(sem.label), sem.score, ...
                safe_char_(final.final_bin), ...
                safe_char_(gen.reasons), safe_char_(sem.reasons));
            drawnow;
        end
    end

    T = struct2table(rows);
    summary = make_summary_(T, input_spec, cfg);

    if cfg.output.save_csv || cfg.output.save_mat
        out_dir = string(cfg.output.out_dir);
        if strlength(out_dir) == 0
            out_dir = fullfile(root, "results", "ota", "validation");
        end
        if ~exist(out_dir, "dir"), mkdir(out_dir); end

        if strlength(string(cfg.output.base_name)) == 0
            base_name = "ota_validation";
        else
            base_name = string(cfg.output.base_name);
        end

        if cfg.output.save_csv
            writetable(T, fullfile(out_dir, base_name + ".csv"));
        end
        if cfg.output.save_mat
            save(fullfile(out_dir, base_name + ".mat"), "T", "summary", "input_spec", "cfg", "-v7.3");
        end
    end
end


% ============================================================
% input normalization / defaults
% ============================================================

function s = normalize_input_spec_(s, root)
    if ~isfield(s, "root") || isempty(s.root), s.root = root; end
    if ~isfield(s, "protocols") || isempty(s.protocols), s.protocols = ["wifi","bluetooth","zigbee"]; end
    if ~isfield(s, "dataset_ids"), s.dataset_ids = []; end
    if ~isfield(s, "shard_ids"), s.shard_ids = []; end
    if ~isfield(s, "pas") || isempty(s.pas), s.pas = ["PA2","PA3","PA4","PA8"]; end
    if ~isfield(s, "sample_mode") || isempty(s.sample_mode), s.sample_mode = "all"; end
    if ~isfield(s, "n_per_file"), s.n_per_file = []; end
    if ~isfield(s, "random_seed"), s.random_seed = 0; end
    if ~isfield(s, "window_ids"), s.window_ids = []; end
    if ~isfield(s, "records"), s.records = []; end

    s.root = string(s.root);
    s.protocols = string(s.protocols(:).');
    s.pas = string(s.pas(:).');
    s.sample_mode = string(s.sample_mode);
    s.dataset_ids = normalize_string_or_empty_(s.dataset_ids);
end

function x = normalize_string_or_empty_(x)
    if isempty(x)
        x = [];
    else
        x = string(x(:).');
    end
end

function cfg = default_cfg_()
    cfg = struct();

    cfg.runtime.verbose = true;
    cfg.runtime.print_every = 1;

    cfg.output.save_csv = false;
    cfg.output.save_mat = false;
    cfg.output.out_dir = "";
    cfg.output.base_name = "";

    % generic OTA integrity QC
    cfg.generic.nfft = 1024;
    cfg.generic.noverlap = 768;
    cfg.generic.dc_mask_bins = 2;
    cfg.generic.active_db = 6.0;
    cfg.generic.wideband_freq_frac_hi = 0.35;

    cfg.generic.reject_wideband_time_frac = 0.20;
    cfg.generic.main_wideband_time_frac = 0.06;

    cfg.generic.reject_max_wideband_run_frac = 0.12;
    cfg.generic.main_max_wideband_run_frac = 0.04;

    cfg.generic.reject_event_contrast_db = 4.5;
    cfg.generic.main_event_contrast_db = 6.0;

    cfg.generic.reject_active_time_frac = 0.03;
    cfg.generic.main_active_time_frac = 0.05;

    cfg.generic.discontinuity_r_threshold = 25.0;

    % shared semantic detector params (OTA-safe)
    cfg.semantic.occ.smooth_s = 2e-5;
    cfg.semantic.occ.close_s = 2e-4;
    cfg.semantic.occ.q_floor = 0.20;
    cfg.semantic.occ.k_mad = 6.0;
    cfg.semantic.occ.min_comp_s = 2e-4;

    cfg.semantic.edges.smooth_s = 2e-5;
    cfg.semantic.edges.refractory_s = 2e-4;
    cfg.semantic.edges.k_hi = 6.0;
    cfg.semantic.edges.k_lo = 3.0;

    cfg.semantic.stft.nfft = 1024;
    cfg.semantic.stft.hop = 256;
    cfg.semantic.stft.nbins = 32;

    cfg.semantic.freq.persistence_frames = 2;
    cfg.semantic.freq.smooth_frames = 3;
    cfg.semantic.freq.min_delta_bins = 2;

    cfg.semantic.repeat.ds = 4;
    cfg.semantic.repeat.maxlag_s = 2e-4;
    cfg.semantic.repeat.cap_len_s = 8e-3;

    % PA2 contradiction thresholds
    cfg.pa2.span_reject = 0.03;
    cfg.pa2.span_warn = 0.06;
    cfg.pa2.edge_min_reject = 1;
    cfg.pa2.edge_min_warn = 2;
    cfg.pa2.burst_len_max_s = 8e-3;
    cfg.pa2.ibi_max_s = 8e-3;
    cfg.pa2.freq_jump_reject = 1;
    cfg.pa2.energy_stationary_warn = 0.85;

    % PA3 contradiction thresholds
    cfg.pa3.span_reject = 0.05;
    cfg.pa3.span_warn = 0.08;
    cfg.pa3.edge_max_reject = 8;
    cfg.pa3.edge_max_warn = 4;
    cfg.pa3.shape_min_reject = 0.75;
    cfg.pa3.shape_min_warn = 0.88;
    cfg.pa3.energy_min_reject = 0.55;
    cfg.pa3.energy_min_warn = 0.72;
    cfg.pa3.freq_jump_reject = 1;

    % PA4 contradiction thresholds
    cfg.pa4.span_reject = 0.05;
    cfg.pa4.span_warn = 0.08;
    cfg.pa4.jump_min_reject = 1;
    cfg.pa4.jump_min_warn = 2;
    cfg.pa4.revisit_missing_is_soft = true;

    % PA8 contradiction thresholds
    cfg.pa8.train_span_reject = 0.05;
    cfg.pa8.train_span_warn = 0.08;
    cfg.pa8.repeat_min_reject = 2;
    cfg.pa8.repeat_min_warn = 3;
    cfg.pa8.sim_min_reject = 0.40;
    cfg.pa8.sim_min_warn = 0.55;

    % merge policy
    cfg.merge.reject_if_semantic_score_ge = 0.85;
end

function out = merge_structs_(a, b)
    out = a;
    if isempty(b), return; end
    fn = fieldnames(b);
    for i = 1:numel(fn)
        f = fn{i};
        if isstruct(b.(f)) && isfield(out, f) && isstruct(out.(f))
            out.(f) = merge_structs_(out.(f), b.(f));
        else
            out.(f) = b.(f);
        end
    end
end


% ============================================================
% record resolution
% ============================================================

function records = resolve_records_(input_spec)
    if ~isempty(input_spec.records)
        records = resolve_explicit_records_(input_spec.records, input_spec.root);
        return;
    end

    records = struct( ...
        "protocol", {}, ...
        "dataset_id", {}, ...
        "shard_id", {}, ...
        "pa_type", {}, ...
        "file_path", {}, ...
        "column_idx", {});

    root = input_spec.root;
    sample_mode = string(input_spec.sample_mode);
    rng(double(input_spec.random_seed));

    for protocol = string(input_spec.protocols)
        dataset_dirs = resolve_dataset_dirs_(root, protocol, input_spec.dataset_ids);

        for d = 1:numel(dataset_dirs)
            dataset_id = string(dataset_dirs(d).name);
            dataset_path = string(fullfile(dataset_dirs(d).folder, dataset_dirs(d).name));

            shard_dirs = resolve_shard_dirs_(dataset_path, input_spec.shard_ids);

            for s = 1:numel(shard_dirs)
                shard_name = string(shard_dirs(s).name);
                shard_id = parse_shard_id_(shard_name);

                for pa = string(input_spec.pas)
                    f = fullfile(shard_dirs(s).folder, shard_dirs(s).name, sprintf("ota_rx_%s.mat", pa));
                    if ~isfile(f), continue; end

                    S = load(f, "meta_rx");
                    meta_rx = S.meta_rx;
                    n_cols = numel(meta_rx);
                    if n_cols == 0, continue; end

                    idx = 1:n_cols;

                    if ~isempty(input_spec.window_ids)
                        ids = arrayfun(@(m) double(m.window_id), meta_rx);
                        idx = idx(ismember(ids, double(input_spec.window_ids)));
                    end

                    if isempty(idx), continue; end

                    switch sample_mode
                        case "all"
                            % keep idx
                        case "first_n"
                            if isempty(input_spec.n_per_file)
                                error("input_spec.n_per_file required for sample_mode='first_n'");
                            end
                            idx = idx(1:min(numel(idx), double(input_spec.n_per_file)));
                        case "random_n"
                            if isempty(input_spec.n_per_file)
                                error("input_spec.n_per_file required for sample_mode='random_n'");
                            end
                            K = min(numel(idx), double(input_spec.n_per_file));
                            p = randperm(numel(idx), K);
                            idx = sort(idx(p));
                        otherwise
                            error("Unknown sample_mode: %s", sample_mode);
                    end

                    for j = 1:numel(idx)
                        records(end+1,1) = struct( ... %#ok<AGROW>
                            "protocol", char(protocol), ...
                            "dataset_id", char(dataset_id), ...
                            "shard_id", shard_id, ...
                            "pa_type", char(pa), ...
                            "file_path", char(f), ...
                            "column_idx", idx(j));
                    end
                end
            end
        end
    end
end

function records = resolve_explicit_records_(R, root)
    if istable(R)
        R = table2struct(R);
    end
    if ~isstruct(R)
        error("input_spec.records must be a table or struct array");
    end

    records = struct( ...
        "protocol", {}, ...
        "dataset_id", {}, ...
        "shard_id", {}, ...
        "pa_type", {}, ...
        "file_path", {}, ...
        "column_idx", {});

    for i = 1:numel(R)
        rec = R(i);

        if isfield(rec, "file_path") && ~isempty(rec.file_path)
            f = string(rec.file_path);
            protocol = string(rec.protocol);
            dataset_id = string(rec.dataset_id);
            shard_id = double(rec.shard_id);
            pa_type = string(rec.pa_type);
        else
            protocol = string(rec.protocol);
            dataset_id = normalize_dataset_id_(protocol, string(rec.dataset_id));
            shard_id = double(rec.shard_id);
            pa_type = string(rec.pa_type);

            f = fullfile(root, "data", char(protocol), "ota", "spliced", ...
                "simple", char(dataset_id), sprintf("shard_%03d", shard_id), ...
                sprintf("ota_rx_%s.mat", pa_type));
        end

        if ~isfile(f)
            error("Explicit record file not found: %s", f);
        end

        records(end+1,1) = struct( ... %#ok<AGROW>
            "protocol", char(protocol), ...
            "dataset_id", char(normalize_dataset_id_(protocol, dataset_id)), ...
            "shard_id", shard_id, ...
            "pa_type", char(pa_type), ...
            "file_path", char(f), ...
            "column_idx", double(rec.column_idx));
    end
end

function dataset_dirs = resolve_dataset_dirs_(root, protocol, dataset_ids)
    base = fullfile(root, "data", char(protocol), "ota", "spliced", "simple");
    if ~exist(base, "dir")
        dataset_dirs = dir.empty(0,1);
        return;
    end

    dd = dir(base);
    dd = dd([dd.isdir]);

    names = string({dd.name});
    keep = names ~= "." & names ~= "..";
    dd = dd(keep);

    if isempty(dataset_ids)
        dataset_dirs = dd;
        return;
    end

    want = strings(1, numel(dataset_ids));
    for i = 1:numel(dataset_ids)
        want(i) = normalize_dataset_id_(protocol, dataset_ids(i));
    end

    keep = ismember(string({dd.name}), want);
    dataset_dirs = dd(keep);
end

function shard_dirs = resolve_shard_dirs_(dataset_path, shard_ids)
    dd = dir(dataset_path);
    dd = dd([dd.isdir]);
    dd = dd(startsWith(string({dd.name}), "shard_"));

    if isempty(shard_ids)
        shard_dirs = dd;
        return;
    end

    keep = false(1, numel(dd));
    for i = 1:numel(dd)
        sid = parse_shard_id_(string(dd(i).name));
        keep(i) = ismember(sid, double(shard_ids));
    end
    shard_dirs = dd(keep);
end

function dataset_id = normalize_dataset_id_(protocol, dataset_id)
    dataset_id = string(dataset_id);
    prefix = protocol + "_";
    if ~startsWith(dataset_id, prefix)
        dataset_id = prefix + dataset_id;
    end
end

function sid = parse_shard_id_(shard_name)
    tok = regexp(char(shard_name), 'shard_(\d+)', 'tokens', 'once');
    if isempty(tok)
        error("Could not parse shard id from %s", shard_name);
    end
    sid = str2double(tok{1});
end


% ============================================================
% loading
% ============================================================

function [x, meta_i, rx_cfg] = load_one_selected_window_(rec)
    S = load(rec.file_path, "meta_rx", "rx_cfg");
    meta_i = S.meta_rx(rec.column_idx);
    rx_cfg = S.rx_cfg;

    M = matfile(rec.file_path);
    x = M.Xrx_all(:, rec.column_idx);
    x = x(:);
end


% ============================================================
% generic OTA QC
% ============================================================

function gen = ota_generic_qc_(x, Fs, cfg)
    x = x(:);

    p = abs(x).^2;
    med_rms = pa_rms(x);

    if med_rms <= 0 || ~isfinite(med_rms)
        gen = struct( ...
            "label", "reject", ...
            "score", 1.0, ...
            "reasons", "invalid_rms", ...
            "wideband_time_frac", NaN, ...
            "max_wideband_run_frac", NaN, ...
            "event_contrast_db", NaN, ...
            "active_time_frac", NaN, ...
            "discontinuity", true);
        return;
    end

    rdiff = abs(diff(x)) / max(1e-12, med_rms);
    disc = any(~isfinite(x)) || any(rdiff > cfg.generic.discontinuity_r_threshold);

    [S, ~, ~] = spectrogram(x, hamming(cfg.generic.nfft), cfg.generic.noverlap, cfg.generic.nfft, Fs, "centered");
    P = 10*log10(abs(S).^2 + 1e-12);

    nF = size(P,1);
    dc0 = floor(nF/2) + 1;
    keep = true(nF,1);
    keep(max(1,dc0-cfg.generic.dc_mask_bins):min(nF,dc0+cfg.generic.dc_mask_bins)) = false;

    Pk = P(keep,:);
    floor_db = median(Pk(:));
    active_mask = Pk > (floor_db + cfg.generic.active_db);

    frac_active_per_t = mean(active_mask, 1);
    wideband_t = frac_active_per_t > cfg.generic.wideband_freq_frac_hi;

    wideband_time_frac = mean(wideband_t);
    max_wideband_run_frac = longest_run_frac_(wideband_t);
    event_contrast_db = prctile(Pk(:), 99.5) - median(Pk(:));
    active_time_frac = mean(any(active_mask, 1));

    hard = 0;
    soft = 0;
    reasons = strings(0,1);

    if disc
        hard = hard + 1;
        reasons(end+1,1) = "discontinuity";
    end
    if wideband_time_frac >= cfg.generic.reject_wideband_time_frac
        hard = hard + 1;
        reasons(end+1,1) = "wideband_time_high";
    elseif wideband_time_frac > cfg.generic.main_wideband_time_frac
        soft = soft + 1;
        reasons(end+1,1) = "wideband_time_warn";
    end

    if max_wideband_run_frac >= cfg.generic.reject_max_wideband_run_frac
        hard = hard + 1;
        reasons(end+1,1) = "wideband_run_high";
    elseif max_wideband_run_frac > cfg.generic.main_max_wideband_run_frac
        soft = soft + 1;
        reasons(end+1,1) = "wideband_run_warn";
    end

    if event_contrast_db < cfg.generic.reject_event_contrast_db
        hard = hard + 1;
        reasons(end+1,1) = "contrast_low";
    elseif event_contrast_db < cfg.generic.main_event_contrast_db
        soft = soft + 1;
        reasons(end+1,1) = "contrast_warn";
    end

    if active_time_frac < cfg.generic.reject_active_time_frac
        hard = hard + 1;
        reasons(end+1,1) = "active_time_low";
    elseif active_time_frac < cfg.generic.main_active_time_frac
        soft = soft + 1;
        reasons(end+1,1) = "active_time_warn";
    end

    score = min(1.0, 0.40*hard + 0.15*soft);

    if hard > 0
        label = "reject";
    elseif soft > 0
        label = "stress_only";
    else
        label = "main_usable";
    end

    gen = struct();
    gen.label = label;
    gen.score = score;
    gen.reasons = join(reasons, ";");
    gen.wideband_time_frac = wideband_time_frac;
    gen.max_wideband_run_frac = max_wideband_run_frac;
    gen.event_contrast_db = event_contrast_db;
    gen.active_time_frac = active_time_frac;
    gen.discontinuity = logical(disc);
end

function frac = longest_run_frac_(mask)
    mask = logical(mask(:).');
    if isempty(mask)
        frac = 0;
        return;
    end
    d = diff([false mask false]);
    s = find(d == 1);
    e = find(d == -1) - 1;
    if isempty(s)
        frac = 0;
    else
        frac = max(e - s + 1) / numel(mask);
    end
end


% ============================================================
% semantic checks
% ============================================================

function sem = ota_semantic_check_(x, Fs, pa_label, cfg)
    common = ota_common_features_(x, Fs, cfg);

    switch string(pa_label)
        case "PA2"
            sem = ota_semantic_pa2_(common, Fs, cfg);
        case "PA3"
            sem = ota_semantic_pa3_(common, cfg);
        case "PA4"
            sem = ota_semantic_pa4_(common, cfg);
        case "PA8"
            sem = ota_semantic_pa8_(x, Fs, common, cfg);
        otherwise
            error("Unknown PA label: %s", pa_label);
    end
end

function common = ota_common_features_(x, Fs, cfg)
    occ = pa_detect_occupancy_ota_v01( ...
        x, Fs, ...
        cfg.semantic.occ.smooth_s, ...
        cfg.semantic.occ.close_s, ...
        cfg.semantic.occ.q_floor, ...
        cfg.semantic.occ.k_mad, ...
        cfg.semantic.occ.min_comp_s);

    e23 = pa_detect_E2E3( ...
        x, Fs, ...
        cfg.semantic.edges.smooth_s, ...
        cfg.semantic.edges.refractory_s, ...
        cfg.semantic.edges.k_hi, ...
        cfg.semantic.edges.k_lo);

    B = pa_stft_bins32(x, cfg.semantic.stft.nfft, cfg.semantic.stft.hop, cfg.semantic.stft.nbins);

    epsv = 1e-12;
    N = sqrt(sum(B.^2, 1)) + epsv;
    Bh = B ./ N;
    c = sum(Bh(:,1:end-1) .* Bh(:,2:end), 1);
    st_shape = mean(c);

    E = sum(B, 1) + epsv;
    energy_cv = std(E) / (mean(E) + epsv);
    st_energy = 1 / (1 + energy_cv);

    fj = pa_detect_freq_jump( ...
        B, ...
        cfg.semantic.freq.persistence_frames, ...
        cfg.semantic.freq.smooth_frames, ...
        cfg.semantic.freq.min_delta_bins);

    rv = pa_detect_freq_revisit(fj.bin_trace);

    common = struct();
    common.occ = occ;
    common.e23 = e23;
    common.st_shape = st_shape;
    common.st_energy = st_energy;
    common.energy_cv = energy_cv;
    common.fj = fj;
    common.rv = rv;
end

function sem = ota_semantic_pa2_(common, Fs, cfg)
    rise = common.e23.rise_idx(:);
    fall = common.e23.fall_idx(:);
    K = min(numel(rise), numel(fall));
    rise = rise(1:K);
    fall = fall(1:K);
    good = (fall >= rise);
    rise = rise(good);
    fall = fall(good);

    burst_len_s = double(fall - rise + 1) / double(Fs);
    ibi_s = double(rise(2:end) - fall(1:end-1) - 1) / double(Fs);

    hard = 0;
    soft = 0;
    reasons = strings(0,1);

    span_frac = common.occ.train_frac;
    edge_count = min(common.e23.E2_count, common.e23.E3_count);

    if span_frac < cfg.pa2.span_reject
        hard = hard + 1; reasons(end+1,1) = "span_low";
    elseif span_frac < cfg.pa2.span_warn
        soft = soft + 1; reasons(end+1,1) = "span_warn";
    end

    if edge_count < cfg.pa2.edge_min_reject
        hard = hard + 1; reasons(end+1,1) = "edge_count_low";
    elseif edge_count < cfg.pa2.edge_min_warn
        soft = soft + 1; reasons(end+1,1) = "edge_count_warn";
    end

    if common.fj.count >= cfg.pa2.freq_jump_reject
        hard = hard + 1; reasons(end+1,1) = "freq_jump_present";
    end

    if ~isempty(burst_len_s) && max(burst_len_s) > cfg.pa2.burst_len_max_s
        soft = soft + 1; reasons(end+1,1) = "burst_len_long";
    end

    if ~isempty(ibi_s) && max(ibi_s) > cfg.pa2.ibi_max_s
        soft = soft + 1; reasons(end+1,1) = "ibi_long";
    end

    if common.st_energy >= cfg.pa2.energy_stationary_warn
        soft = soft + 1; reasons(end+1,1) = "too_energy_stationary";
    end

    score = min(1.0, 0.35*hard + 0.15*soft);
    label = semantic_label_from_score_(score);

    sem = struct();
    sem.label = label;
    sem.score = score;
    sem.reasons = join(reasons, ";");
    sem.span_frac = span_frac;
    sem.edge_start_count = common.e23.E2_count;
    sem.edge_end_count = common.e23.E3_count;
    sem.freq_jump_count = common.fj.count;
    sem.freq_revisit_present = common.rv.present;
    sem.stationarity_shape = common.st_shape;
    sem.stationarity_energy = common.st_energy;
    sem.repeat_count = NaN;
    sem.repeat_similarity = NaN;
end

function sem = ota_semantic_pa3_(common, cfg)
    hard = 0;
    soft = 0;
    reasons = strings(0,1);

    span_frac = common.occ.duty_frac;
    edge_count = max(common.e23.E2_count, common.e23.E3_count);

    if span_frac < cfg.pa3.span_reject
        hard = hard + 1; reasons(end+1,1) = "span_low";
    elseif span_frac < cfg.pa3.span_warn
        soft = soft + 1; reasons(end+1,1) = "span_warn";
    end

    if edge_count > cfg.pa3.edge_max_reject
        hard = hard + 1; reasons(end+1,1) = "edge_density_high";
    elseif edge_count > cfg.pa3.edge_max_warn
        soft = soft + 1; reasons(end+1,1) = "edge_density_warn";
    end

    if common.st_shape < cfg.pa3.shape_min_reject || common.st_energy < cfg.pa3.energy_min_reject
        hard = hard + 1; reasons(end+1,1) = "stationarity_low";
    elseif common.st_shape < cfg.pa3.shape_min_warn || common.st_energy < cfg.pa3.energy_min_warn
        soft = soft + 1; reasons(end+1,1) = "stationarity_warn";
    end

    if common.fj.count >= cfg.pa3.freq_jump_reject
        hard = hard + 1; reasons(end+1,1) = "freq_jump_present";
    end

    score = min(1.0, 0.35*hard + 0.15*soft);
    label = semantic_label_from_score_(score);

    sem = struct();
    sem.label = label;
    sem.score = score;
    sem.reasons = join(reasons, ";");
    sem.span_frac = span_frac;
    sem.edge_start_count = common.e23.E2_count;
    sem.edge_end_count = common.e23.E3_count;
    sem.freq_jump_count = common.fj.count;
    sem.freq_revisit_present = common.rv.present;
    sem.stationarity_shape = common.st_shape;
    sem.stationarity_energy = common.st_energy;
    sem.repeat_count = NaN;
    sem.repeat_similarity = NaN;
end

function sem = ota_semantic_pa4_(common, cfg)
    hard = 0;
    soft = 0;
    reasons = strings(0,1);

    span_frac = common.occ.duty_frac;

    if span_frac < cfg.pa4.span_reject
        hard = hard + 1; reasons(end+1,1) = "span_low";
    elseif span_frac < cfg.pa4.span_warn
        soft = soft + 1; reasons(end+1,1) = "span_warn";
    end

    if common.fj.count < cfg.pa4.jump_min_reject
        hard = hard + 1; reasons(end+1,1) = "jump_count_low";
    elseif common.fj.count < cfg.pa4.jump_min_warn
        soft = soft + 1; reasons(end+1,1) = "jump_count_warn";
    end

    if ~common.rv.present
        if cfg.pa4.revisit_missing_is_soft
            soft = soft + 1; reasons(end+1,1) = "revisit_missing";
        else
            hard = hard + 1; reasons(end+1,1) = "revisit_missing";
        end
    end

    score = min(1.0, 0.35*hard + 0.15*soft);
    label = semantic_label_from_score_(score);

    sem = struct();
    sem.label = label;
    sem.score = score;
    sem.reasons = join(reasons, ";");
    sem.span_frac = span_frac;
    sem.edge_start_count = common.e23.E2_count;
    sem.edge_end_count = common.e23.E3_count;
    sem.freq_jump_count = common.fj.count;
    sem.freq_revisit_present = common.rv.present;
    sem.stationarity_shape = common.st_shape;
    sem.stationarity_energy = common.st_energy;
    sem.repeat_count = NaN;
    sem.repeat_similarity = NaN;
end

function sem = ota_semantic_pa8_(x, Fs, common, cfg)
    intervals = [common.occ.starts(:) common.occ.ends(:)];
    sim = pa_detect_repeat_similarity_iqxcorr( ...
        x, Fs, intervals, ...
        cfg.semantic.repeat.ds, ...
        cfg.semantic.repeat.maxlag_s, ...
        cfg.semantic.repeat.cap_len_s);

    hard = 0;
    soft = 0;
    reasons = strings(0,1);

    train_frac = common.occ.train_frac;

    if train_frac < cfg.pa8.train_span_reject
        hard = hard + 1; reasons(end+1,1) = "train_span_low";
    elseif train_frac < cfg.pa8.train_span_warn
        soft = soft + 1; reasons(end+1,1) = "train_span_warn";
    end

    if sim.used_repeats < cfg.pa8.repeat_min_reject
        hard = hard + 1; reasons(end+1,1) = "repeat_count_low";
    elseif sim.used_repeats < cfg.pa8.repeat_min_warn
        soft = soft + 1; reasons(end+1,1) = "repeat_count_warn";
    end

    if sim.used_repeats >= cfg.pa8.repeat_min_reject
        if sim.score < cfg.pa8.sim_min_reject
            hard = hard + 1; reasons(end+1,1) = "repeat_similarity_low";
        elseif sim.score < cfg.pa8.sim_min_warn
            soft = soft + 1; reasons(end+1,1) = "repeat_similarity_warn";
        end
    end

    score = min(1.0, 0.35*hard + 0.15*soft);
    label = semantic_label_from_score_(score);

    sem = struct();
    sem.label = label;
    sem.score = score;
    sem.reasons = join(reasons, ";");
    sem.span_frac = train_frac;
    sem.edge_start_count = common.e23.E2_count;
    sem.edge_end_count = common.e23.E3_count;
    sem.freq_jump_count = common.fj.count;
    sem.freq_revisit_present = common.rv.present;
    sem.stationarity_shape = common.st_shape;
    sem.stationarity_energy = common.st_energy;
    sem.repeat_count = sim.used_repeats;
    sem.repeat_similarity = sim.score;
end

function label = semantic_label_from_score_(score)
    if score >= 0.60
        label = "contradictory";
    elseif score >= 0.25
        label = "borderline";
    else
        label = "consistent";
    end
end


% ============================================================
% merge policy
% ============================================================

function final = merge_generic_semantic_(gen, sem, cfg)
    if gen.label == "reject"
        final_bin = "reject";
        reason = "generic_reject";
    elseif sem.label == "contradictory"
        if sem.score >= cfg.merge.reject_if_semantic_score_ge
            final_bin = "reject";
            reason = "semantic_contradiction_reject";
        else
            final_bin = "stress_only";
            reason = "semantic_contradiction_stress";
        end
    elseif gen.label == "stress_only" || sem.label == "borderline"
        final_bin = "stress_only";
        reason = "borderline_or_generic_stress";
    else
        final_bin = "main_usable";
        reason = "usable_and_consistent";
    end

    final = struct();
    final.final_bin = final_bin;
    final.reason = reason;
end


% ============================================================
% row / summary builders
% ============================================================

function row = build_row_(rec, meta_i, Fs, gen, sem, final)
    row = empty_row_();

    row.protocol = string(rec.protocol);
    row.dataset_id = string(rec.dataset_id);
    row.shard_id = double(rec.shard_id);
    row.pa_label = string(rec.pa_type);
    row.file_path = string(rec.file_path);
    row.column_idx = double(rec.column_idx);

    if isfield(meta_i, "window_id"), row.window_id = double(meta_i.window_id); end
    if isfield(meta_i, "seq"), row.seq = double(meta_i.seq); end
    if isfield(meta_i, "k_ph"), row.k_ph = double(meta_i.k_ph); end
    if isfield(meta_i, "header_r"), row.header_r = double(meta_i.header_r); end

    row.fs_hz = Fs;

    row.integrity_label = string(gen.label);
    row.integrity_score = double(gen.score);
    row.integrity_reasons = string(gen.reasons);

    row.semantic_label = string(sem.label);
    row.semantic_score = double(sem.score);
    row.semantic_reasons = string(sem.reasons);

    row.final_bin = string(final.final_bin);
    row.final_reason = string(final.reason);

    row.wideband_time_frac = gen.wideband_time_frac;
    row.max_wideband_run_frac = gen.max_wideband_run_frac;
    row.event_contrast_db = gen.event_contrast_db;
    row.active_time_frac = gen.active_time_frac;
    row.discontinuity = logical(gen.discontinuity);

    row.span_frac = sem.span_frac;
    row.edge_start_count = sem.edge_start_count;
    row.edge_end_count = sem.edge_end_count;
    row.freq_jump_count = sem.freq_jump_count;
    row.freq_revisit_present = logical(sem.freq_revisit_present);
    row.stationarity_shape = sem.stationarity_shape;
    row.stationarity_energy = sem.stationarity_energy;
    row.repeat_count = sem.repeat_count;
    row.repeat_similarity = sem.repeat_similarity;
end

function row = empty_row_()
    row = struct( ...
        "protocol", "", ...
        "dataset_id", "", ...
        "shard_id", NaN, ...
        "pa_label", "", ...
        "file_path", "", ...
        "column_idx", NaN, ...
        "window_id", NaN, ...
        "seq", NaN, ...
        "k_ph", NaN, ...
        "header_r", NaN, ...
        "fs_hz", NaN, ...
        "integrity_label", "", ...
        "integrity_score", NaN, ...
        "integrity_reasons", "", ...
        "semantic_label", "", ...
        "semantic_score", NaN, ...
        "semantic_reasons", "", ...
        "final_bin", "", ...
        "final_reason", "", ...
        "wideband_time_frac", NaN, ...
        "max_wideband_run_frac", NaN, ...
        "event_contrast_db", NaN, ...
        "active_time_frac", NaN, ...
        "discontinuity", false, ...
        "span_frac", NaN, ...
        "edge_start_count", NaN, ...
        "edge_end_count", NaN, ...
        "freq_jump_count", NaN, ...
        "freq_revisit_present", false, ...
        "stationarity_shape", NaN, ...
        "stationarity_energy", NaN, ...
        "repeat_count", NaN, ...
        "repeat_similarity", NaN);
end

function summary = make_summary_(T, input_spec, cfg)
    summary = struct();
    summary.n_total = height(T);
    summary.input_spec = input_spec;
    summary.cfg = cfg;

    summary.overall_final = simple_count_table_(T.final_bin, "final_bin");
    summary.overall_integrity = simple_count_table_(T.integrity_label, "integrity_label");
    summary.overall_semantic = simple_count_table_(T.semantic_label, "semantic_label");

    summary.by_pa_final = two_key_count_table_(T.pa_label, T.final_bin, "pa_label", "final_bin");
    summary.by_protocol_final = two_key_count_table_(T.protocol, T.final_bin, "protocol", "final_bin");
    summary.by_dataset_final = two_key_count_table_(T.dataset_id, T.final_bin, "dataset_id", "final_bin");
end

function Tcnt = simple_count_table_(x, name1)
    x = string(x(:));
    [g, vals] = findgroups(x);
    n = splitapply(@numel, x, g);

    var_names = {char(name1), 'count'};
    Tcnt = table(vals, n, 'VariableNames', var_names);
    Tcnt = sortrows(Tcnt, 'count', 'descend');
end

function Tcnt = two_key_count_table_(a, b, name1, name2)
    a = string(a(:));
    b = string(b(:));
    [g, va, vb] = findgroups(a, b);
    n = splitapply(@numel, a, g);

    var_names = {char(name1), char(name2), 'count'};
    Tcnt = table(va, vb, n, 'VariableNames', var_names);
    Tcnt = sortrows(Tcnt, 'count', 'descend');
end

function summary = empty_summary_()
    summary = struct();
    summary.n_total = 0;
    summary.overall_final = table();
    summary.overall_integrity = table();
    summary.overall_semantic = table();
    summary.by_pa_final = table();
    summary.by_protocol_final = table();
    summary.by_dataset_final = table();
end

function s = safe_char_(x)
    if ismissing(x)
        s = '';
    else
        s = char(string(x));
    end
end