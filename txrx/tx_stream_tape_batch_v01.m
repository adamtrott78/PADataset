function tx_stream_tape_batch_v01(plan_file, ip, fc_hz, gain_db, tx_ant, varargin)
%TX_STREAM_TAPE_BATCH_V01 Operator-paced TX batch runner.
%
% Usage:
%   tx_stream_tape_batch_v01(plan_file, ip, fc_hz, gain_db, tx_ant)
%   tx_stream_tape_batch_v01(plan_file, ip, fc_hz, gain_db, tx_ant, 'step_ids', 1:5)
%
% Notes:
%   - Loads a saved recording session plan
%   - Runs selected steps one at a time
%   - Prompts operator before each step
%   - Calls tx_stream_tape(...) using step.tx_file
%   - Saves per-step TX log next to step.log_file as *_tx.mat

    p = inputParser;
    addParameter(p, 'step_ids', []);
    parse(p, varargin{:});
    step_ids = p.Results.step_ids;

    if nargin < 5
        error('Usage: tx_stream_tape_batch_v01(plan_file, ip, fc_hz, gain_db, tx_ant, ...)');
    end

    S = load(plan_file, 'plan');
    plan = S.plan;

    steps = plan.steps;
    idx = select_step_ids(steps, step_ids);

    fprintf('TX BATCH\n');
    fprintf('  plan_file : %s\n', plan_file);
    fprintf('  steps     : %s\n\n', mat2str(idx));

    for ii = 1:numel(idx)
        s = steps(idx(ii));

        fprintf('--------------------------------------------------\n');
        fprintf('STEP %03d | %s | %s | %s | shard=%03d\n', ...
            s.step_id, s.step_type, s.protocol, s.dataset_id, s.shard_id);
        fprintf('TX file : %s\n', s.tx_file);
        fprintf('Log file: %s\n', tx_log_path(s.log_file));
        fprintf('Note    : %s\n', s.note);

        if ~isfile(s.tx_file)
            fprintf('TX file missing.\n');
            resp = lower(strtrim(input('Action? [s]kip / [q]uit : ', 's')));
            if strcmp(resp, 'q')
                fprintf('Quitting TX batch.\n');
                return;
            end
            fprintf('Skipping step %03d.\n\n', s.step_id);
            continue;
        end

        resp = lower(strtrim(input('Press ENTER to run, [s]kip, [q]uit: ', 's')));
        if strcmp(resp, 'q')
            fprintf('Quitting TX batch.\n');
            return;
        elseif strcmp(resp, 's')
            fprintf('Skipping step %03d.\n\n', s.step_id);
            continue;
        end

        log = struct();
        log.step = s;
        log.plan_file = string(plan_file);
        log.host_role = "tx";
        log.started_at = datetime("now");
        log.status = "started";
        log.error_message = "";

        try
            save_tx_log(log, s.log_file);

            % Operator still presses SPACE in tx_stream_tape UI when ready.
            tx_stream_tape(s.protocol, ip, fc_hz, gain_db, tx_ant, s.tx_file);

            log.finished_at = datetime("now");
            log.status = "ok";
            save_tx_log(log, s.log_file);

            fprintf('TX step %03d complete.\n\n', s.step_id);

        catch ME
            log.finished_at = datetime("now");
            log.status = "error";
            log.error_message = string(getReport(ME, 'extended', 'hyperlinks', 'off'));
            save_tx_log(log, s.log_file);

            fprintf('TX step %03d FAILED.\n', s.step_id);
            fprintf('%s\n', log.error_message);

            resp = lower(strtrim(input('Continue? [y]/[n]: ', 's')));
            if strcmp(resp, 'n')
                rethrow(ME);
            end
        end
    end

    fprintf('TX batch finished.\n');
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

function out = tx_log_path(base_log_file)
    [d, n, ~] = fileparts(char(base_log_file));
    if ~exist(d, 'dir')
        mkdir(d);
    end
    out = fullfile(d, [n '_tx.mat']);
end

function save_tx_log(log, base_log_file)
    out = tx_log_path(base_log_file);
    save(out, 'log', '-v7');
end