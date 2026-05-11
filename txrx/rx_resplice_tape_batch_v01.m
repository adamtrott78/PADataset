function rx_resplice_tape_batch_v01(plan_file, varargin)
%RX_RESPLICE_TAPE_BATCH_V01 Operator-paced batch resplicer for recorded OTA shard tapes.
%
% Usage:
%   rx_resplice_tape_batch_v01(plan_file)
%   rx_resplice_tape_batch_v01(plan_file, 'step_ids', 1:5)
%   rx_resplice_tape_batch_v01(plan_file, 'step_ids', 1:5, 'make_png', true, 'max_png_per_pa', 2)
%
% Notes:
%   - Loads a saved recording session plan
%   - For each selected RECORD/CANARY step:
%       * reads step.rx_file
%       * reads step.tx_spec_file
%       * writes respliced PA files under:
%           data/<protocol>/ota/spliced/v05/<dataset_id>/step_###/
%       * writes resplice summary under:
%           results/recording_sessions/<session_tag>/resplice/<protocol>/<dataset_id>/step_###/
%   - Defaults to NO PNG generation

    p = inputParser;
    addParameter(p, 'step_ids', []);
    addParameter(p, 'make_png', false);
    addParameter(p, 'max_png_per_pa', 0);
    addParameter(p, 'skip_missing_rx', true);
    parse(p, varargin{:});

    step_ids = p.Results.step_ids;
    make_png = logical(p.Results.make_png);
    max_png_per_pa = double(p.Results.max_png_per_pa);
    skip_missing_rx = logical(p.Results.skip_missing_rx);

    S = load(plan_file, 'plan');
    plan = S.plan;
    steps = plan.steps;

    idx = select_step_ids(steps, step_ids);

    fprintf('RX RESPLICE BATCH\n');
    fprintf('  plan_file      : %s\n', plan_file);
    fprintf('  steps          : %s\n', mat2str(idx));
    fprintf('  make_png       : %s\n', tf(make_png));
    fprintf('  max_png_per_pa : %d\n\n', max_png_per_pa);

    for ii = 1:numel(idx)
        s = steps(idx(ii));

        fprintf('--------------------------------------------------\n');
        fprintf('STEP %03d | %s | %s | %s | shard=%03d\n', ...
            s.step_id, s.step_type, s.protocol, s.dataset_id, s.shard_id);
        fprintf('RX file : %s\n', s.rx_file);
        fprintf('TX spec : %s\n', s.tx_file);
        fprintf('Note    : %s\n', s.note);

        if ~isfile(s.rx_file)
            fprintf('RX file missing.\n');
            if skip_missing_rx
                fprintf('Skipping step %03d.\n\n', s.step_id);
                continue;
            else
                error('Missing RX file: %s', s.rx_file);
            end
        end

        if ~isfile(s.tx_spec_file)
            error('Missing TX spec for resplice step %03d: %s', s.step_id, s.tx_file);
        end

        [out_data_root, results_root, log_file] = local_paths_from_step(plan, s);

        fprintf('OUT data : %s\n', out_data_root);
        fprintf('OUT res  : %s\n', results_root);
        fprintf('LOG file : %s\n', log_file);

        resp = lower(strtrim(input('Press ENTER to resplice, [s]kip, [q]uit: ', 's')));
        if strcmp(resp, 'q')
            fprintf('Quitting resplice batch.\n');
            return;
        elseif strcmp(resp, 's')
            fprintf('Skipping step %03d.\n\n', s.step_id);
            continue;
        end

        log = struct();
        log.step = s;
        log.plan_file = string(plan_file);
        log.host_role = "resplice";
        log.started_at = datetime("now");
        log.status = "started";
        log.error_message = "";
        log.make_png = make_png;
        log.max_png_per_pa = max_png_per_pa;
        save(log_file, 'log', '-v7');

        try
            rx_resplice_tape(s.protocol, s.rx_file, ...
                s.tx_spec_file, ...
                out_data_root, ...
                results_root, ...
                make_png, ...
                max_png_per_pa);

            log.finished_at = datetime("now");
            log.status = "ok";
            save(log_file, 'log', '-v7');

            fprintf('Resplice step %03d complete.\n\n', s.step_id);

        catch ME
            log.finished_at = datetime("now");
            log.status = "error";
            log.error_message = string(getReport(ME, 'extended', 'hyperlinks', 'off'));
            save(log_file, 'log', '-v7');

            fprintf('Resplice step %03d FAILED.\n', s.step_id);
            fprintf('%s\n', log.error_message);

            resp2 = lower(strtrim(input('Continue? [y]/[n]: ', 's')));
            if strcmp(resp2, 'n')
                rethrow(ME);
            end
        end
    end

    fprintf('Resplice batch finished.\n');
end

function idx = select_step_ids(steps, step_ids)
    n = numel(steps);
    if isempty(step_ids)
        idx = 1:n;
    else
        idx = unique(step_ids(:).');
        idx = idx(idx >= 1 & idx <= n);
    end
end

function [out_data_root, results_root, log_file] = local_paths_from_step(plan, s)
    P = pa_paths();

    % shard-specific respliced data root
    out_data_root = fullfile(P.data_root, char(s.protocol), 'ota', 'spliced', 'v05', ...
        char(s.dataset_id), sprintf('step_%03d', s.step_id));

    % shard-specific results root under session
    results_root = fullfile(P.results, 'recording_sessions', char(plan.session_tag), ...
        'resplice', char(s.protocol), char(s.dataset_id), sprintf('step_%03d', s.step_id));

    if ~exist(out_data_root, 'dir'), mkdir(out_data_root); end
    if ~exist(results_root, 'dir'), mkdir(results_root); end

    log_dir = fullfile(P.results, 'recording_sessions', char(plan.session_tag), ...
        'logs', char(s.protocol), char(s.dataset_id));
    if ~exist(log_dir, 'dir'), mkdir(log_dir); end

    log_file = fullfile(log_dir, sprintf('step_%03d_resplice.mat', s.step_id));
end

function s = tf(ok)
    if ok
        s = 'YES';
    else
        s = 'NO';
    end
end