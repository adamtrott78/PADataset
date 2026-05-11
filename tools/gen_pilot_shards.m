function gen_pilot_shards(protocol, plan, varargin)
%GEN_PILOT_SHARDS Generate deterministic pilot shard files for one protocol combo.
%
% This function is the first large-dataset building block.
% It emits shard-sized digital pilot files while preserving a canonical seed
% identity that does NOT depend on transport sharding.
%
% Usage:
%   plan = pa_make_dataset_plan("wifi", "high", "wifi_high_v1");
%   gen_pilot_shards("wifi", plan)
%
%   gen_pilot_shards("bluetooth", plan, 'shards', 1:3)
%
% Output tree:
%   data/<protocol>/digital/pilot_shards/<dataset_id>/
%       dataset_plan.mat
%       shard_001/pilot_S01_PA2.mat
%       shard_001/pilot_S01_PA3.mat
%       ...
%
% Each shard file mirrors your existing pilot format:
%   Xsig_all, meta, optional sched
%
% Notes:
%   - PA2/PA3/PA4 use canonical seed_segment_id values from the plan.
%   - PA8 uses canonical global_window_ids from the plan.
%   - Metadata window_id is overwritten to the canonical global window IDs.
%   - protocol-specific waveform generators are dispatched internally.

    ip = inputParser();
    ip.addParameter('shards', [], @(x) isnumeric(x) || isempty(x));
    ip.addParameter('overwrite', false, @(x) islogical(x) && isscalar(x));
    ip.addParameter('stage_root', "", @(x) isstring(x) || ischar(x));
    ip.parse(varargin{:});

    protocol = string(protocol);
    assert(strcmpi(protocol, string(plan.protocol)), ...
        'protocol argument must match plan.protocol');

    if isempty(ip.Results.shards)
        shard_ids = 1:numel(plan.shards);
    else
        shard_ids = unique(double(ip.Results.shards(:))).';
    end
    overwrite = ip.Results.overwrite;
    stage_root = string(ip.Results.stage_root);
    
    R = pa_protocol_roots(protocol);
    cfg = pa_load_cfg(fullfile(pa_root(), 'config', 'starter.json'));

    switch protocol
        case "wifi"
            wf_cfg = pa_make_wlan_cfg(cfg);
        case "bluetooth"
            wf_cfg = bt_make_ble_cfg(cfg);
        case "zigbee"
            wf_cfg = zb_make_zigbee_cfg(cfg);
        otherwise
            error('Unsupported protocol %s', protocol);
    end

    if strlength(stage_root) == 0
        base_root = fullfile(R.data_pilot_shards, plan.dataset_id);
    else
        base_root = fullfile(char(stage_root), 'data', char(protocol), 'digital', 'pilot_shards', char(plan.dataset_id));
    end
    
    if ~exist(base_root, 'dir'), mkdir(base_root); end
    save(fullfile(base_root, 'dataset_plan.mat'), 'plan', '-v7');

    Fs = round(double(pa_get_nested(cfg, 'rates.fs_hz')));
    W  = round(double(pa_get_nested(cfg, 'windowing.window_length_s')) * Fs);

    for s = shard_ids
        shard = plan.shards(s);
        shard_root = fullfile(base_root, sprintf('shard_%03d', s));
        if ~exist(shard_root, 'dir'), mkdir(shard_root); end

        fprintf('\n=== GEN SHARD %03d | protocol=%s | dataset=%s ===\n', s, protocol, plan.dataset_id);

        PAs = string(plan.pa_order);
        for pa = PAs
            outfile = fullfile(shard_root, sprintf('pilot_S%02d_%s.mat', plan.seed_session_id, pa));
            if exist(outfile, 'file') && ~overwrite
                fprintf('Skip existing: %s\n', outfile);
                continue;
            end

            tasks = shard.tasks(strcmp({shard.tasks.pa}, char(pa)));
            n_out = sum([tasks.n_windows]);
            Xsig_all = complex(zeros(W, n_out, 'single'), zeros(W, n_out, 'single'));
            meta = [];
            sched = [];
            write_cursor = 0;

            for t = 1:numel(tasks)
                task = tasks(t);
                M = task.n_windows;
                starts = int64(1 + (0:M-1) * W).';
                plan_local = struct('Fs', Fs, 'W', W, 'starts', starts);

                switch protocol
                    case "wifi"
                        [Xi, meta_i, sched_i] = gen_wifi_task(cfg, wf_cfg, plan, pa, task, plan_local);
                    case "bluetooth"
                        [Xi, meta_i, sched_i] = gen_bt_task(cfg, plan, pa, task, plan_local);
                    case "zigbee"
                        [Xi, meta_i, sched_i] = gen_zb_task(cfg, plan, pa, task, plan_local);
                    otherwise
                        error('Unsupported protocol %s', protocol);
                end

                idx = write_cursor + (1:M);
                Xsig_all(:, idx) = Xi;
                for k = 1:M
                    meta_i(k).window_id = double(task.global_window_ids(k));
                    meta_i(k).protocol = char(protocol);
                    meta_i(k).dataset_id = char(plan.dataset_id);
                    meta_i(k).snr_regime = char(plan.snr_regime);
                    meta_i(k).seed_session_id = double(plan.seed_session_id);
                    meta_i(k).seed_tape_id = double(plan.seed_tape_id);
                    meta_i(k).transport_shard_id = double(task.transport_shard_id);
                    if isfield(task, 'seed_segment_id')
                        meta_i(k).seed_segment_id = double(task.seed_segment_id);
                    end
                end
                
                if isempty(meta)
                    meta = repmat(meta_i(1), 1, n_out);
                end
                
                meta(idx) = meta_i;
                if ~isempty(sched_i)
                    if isempty(sched)
                        sched = repmat(sched_i(1), 1, n_out);
                    end
                    sched(idx) = sched_i;
                end

                write_cursor = write_cursor + M;
            end

            if isempty(sched)
                save(outfile, 'Xsig_all', 'meta', '-v7.3');
            else
                save(outfile, 'Xsig_all', 'meta', 'sched', '-v7.3');
            end
            fprintf('Saved: %s | %d windows\n', outfile, n_out);
        end
    end
end


function [Xsig, meta, sched] = gen_wifi_task(cfg, wlanCfg, plan, pa, task, plan_local)
    session_id = plan.seed_session_id;
    tape_id = plan.seed_tape_id;

    switch pa
        case "PA1"
            plan_seg = pa_plan_segment_windows(cfg, session_id, tape_id, task.seed_segment_id, task.n_windows);
            [Xsig, sched] = pa_gen_windows_pa1_stream(cfg, wlanCfg, session_id, tape_id, task.seed_segment_id, plan_seg);
            meta = make_segment_meta(cfg, 'wifi', pa, session_id, tape_id, task.seed_segment_id, plan_seg, task.global_window_ids);
        case "PA2"
            plan_seg = pa_plan_segment_windows(cfg, session_id, tape_id, task.seed_segment_id, task.n_windows);
            [Xsig, sched] = pa_gen_windows_pa2_stream(cfg, wlanCfg, session_id, tape_id, task.seed_segment_id, plan_seg);
            meta = make_segment_meta(cfg, 'wifi', pa, session_id, tape_id, task.seed_segment_id, plan_seg, task.global_window_ids);
        case "PA3"
            plan_seg = pa_plan_segment_windows(cfg, session_id, tape_id, task.seed_segment_id, task.n_windows);
            [Xsig, sched] = pa_gen_windows_pa3_stream(cfg, wlanCfg, session_id, tape_id, task.seed_segment_id, plan_seg);
            meta = make_segment_meta(cfg, 'wifi', pa, session_id, tape_id, task.seed_segment_id, plan_seg, task.global_window_ids);
        case "PA4"
            plan_seg = pa_plan_segment_windows(cfg, session_id, tape_id, task.seed_segment_id, task.n_windows);
            [Xsig, sched] = pa_gen_windows_pa4_stream(cfg, wlanCfg, session_id, tape_id, task.seed_segment_id, plan_seg);
            meta = make_segment_meta(cfg, 'wifi', pa, session_id, tape_id, task.seed_segment_id, plan_seg, task.global_window_ids);
        case "PA8"
            [Xsig, sched] = pa_gen_windows_pa8_stream(cfg, wlanCfg, session_id, tape_id, plan_local, task.global_window_ids(:));
            meta = make_pa8_meta_generic(cfg, 'wifi', session_id, tape_id, plan_local, task.global_window_ids, sched);
        otherwise
            error('Unsupported PA %s', pa);
    end
end


function [Xsig, meta, sched] = gen_bt_task(cfg, plan, pa, task, plan_local)
    session_id = plan.seed_session_id;
    tape_id = plan.seed_tape_id;

    switch pa
        case "PA1"
            [Xsig, meta, sched] = bt_gen_windows_pa1_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
        case "PA2"
            [Xsig, meta, sched] = bt_gen_windows_pa2_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
        case "PA3"
            [Xsig, meta] = bt_gen_windows_pa3_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
            sched = [];
        case "PA4"
            [Xsig, meta, sched] = bt_gen_windows_pa4_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
        case "PA8"
            [Xsig, sched] = bt_gen_windows_pa8_stream(cfg, session_id, tape_id, plan_local, task.global_window_ids(:));
            meta = make_pa8_meta_generic(cfg, 'bluetooth', session_id, tape_id, plan_local, task.global_window_ids, sched);
        otherwise
            error('Unsupported PA %s', pa);
    end
end


function [Xsig, meta, sched] = gen_zb_task(cfg, plan, pa, task, plan_local)
    session_id = plan.seed_session_id;
    tape_id = plan.seed_tape_id;

    switch pa
        case "PA1"
            [Xsig, meta, sched] = zb_gen_windows_pa1_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
        case "PA2"
            [Xsig, meta, sched] = zb_gen_windows_pa2_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
        case "PA3"
            [Xsig, meta] = zb_gen_windows_pa3_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
            sched = [];
        case "PA4"
            [Xsig, meta, sched] = zb_gen_windows_pa4_stream(cfg, session_id, tape_id, task.seed_segment_id, plan_local);
        case "PA8"
            [Xsig, sched] = zb_gen_windows_pa8_stream(cfg, session_id, tape_id, plan_local, task.global_window_ids(:));
            meta = make_pa8_meta_generic(cfg, 'zigbee', session_id, tape_id, plan_local, task.global_window_ids, sched);
        otherwise
            error('Unsupported PA %s', pa);
    end
end


function meta = make_segment_meta(cfg, protocol, pa, session_id, tape_id, segment_id, plan_seg, global_window_ids)
    M = numel(global_window_ids);
    meta = repmat(struct(), 1, M);
    for i = 1:M
        meta(i).schema_version = pa_get_nested(cfg, 'schema_version');
        meta(i).session_id = session_id;
        meta(i).tape_id = tape_id;
        meta(i).segment_id = segment_id;
        meta(i).window_id = double(global_window_ids(i));
        meta(i).pa_type = char(pa);
        meta(i).protocol = char(protocol);
        meta(i).fs_hz = double(plan_seg.Fs);
        meta(i).window_length_s = double(pa_get_nested(cfg, 'windowing.window_length_s'));
        meta(i).window_start_sample = double(plan_seg.starts(i));
    end
end


function meta = make_pa8_meta_generic(cfg, protocol, session_id, tape_id, plan_local, window_ids, sched)
    M = numel(window_ids);
    meta = repmat(struct(), 1, M);
    for i = 1:M
        meta(i).schema_version      = pa_get_nested(cfg, 'schema_version');
        meta(i).session_id          = session_id;
        meta(i).tape_id             = tape_id;
        meta(i).segment_id          = 0;
        meta(i).window_id           = double(window_ids(i));
        meta(i).pa_type             = 'PA8';
        meta(i).protocol            = char(protocol);
        meta(i).fs_hz               = double(plan_local.Fs);
        meta(i).window_length_s     = double(pa_get_nested(cfg, 'windowing.window_length_s'));
        meta(i).window_start_sample = double(plan_local.starts(i));
        if nargin >= 6 && ~isempty(sched)
            if isfield(sched, 'mode'),                meta(i).repeat_mode = sched(i).mode; end
            if isfield(sched, 'repeat_count'),        meta(i).repeat_count = sched(i).repeat_count; end
            if isfield(sched, 'template_len_samp'),   meta(i).template_len_samp = sched(i).template_len_samp; end
            if isfield(sched, 'repeat_spacing_samp'), meta(i).repeat_spacing_samp = sched(i).repeat_spacing_samp; end
            if isfield(sched, 't0_samp'),             meta(i).t0_samp = sched(i).t0_samp; end
            if isfield(sched, 'intervals'),           meta(i).intervals = sched(i).intervals; end
            if isfield(sched, 'train_span_samp'),     meta(i).train_span_samp = sched(i).train_span_samp; end
            if isfield(sched, 'train_span_frac'),     meta(i).train_span_frac = sched(i).train_span_frac; end
            if isfield(sched, 'duty_frac'),           meta(i).duty_frac = sched(i).duty_frac; end
            if isfield(sched, 'near_exact_params'),   meta(i).near_exact_params = sched(i).near_exact_params; end
        end
    end
end
