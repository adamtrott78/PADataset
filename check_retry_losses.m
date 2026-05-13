clear; clc;

root = pwd;

targets = {
    'wifi',   'wifi_high_run01', 2, {'PA2','PA3','PA4','PA8'};
    'wifi',   'wifi_high_run01', 3, {'PA2','PA3','PA4','PA8'};
    'wifi',   'wifi_pa1_run01',  1, {'PA1'};
    'wifi',   'wifi_pa1_run01',  2, {'PA1'};
    'wifi',   'wifi_pa1_run01',  3, {'PA1'};
    'wifi',   'wifi_pa1_run01',  4, {'PA1'};
    'wifi',   'wifi_pa1_run01',  5, {'PA1'};
    'zigbee', 'zigbee_pa1_run01', 2, {'PA1'};
};

core_offsets = containers.Map({'PA2','PA3','PA4','PA8'}, [0 10000 20000 30000]);

fprintf('\n%-8s %-20s %5s %-4s %10s %10s %10s %10s %10s\n', ...
    'proto','dataset','shard','PA','expected','found','lost','dup','extra');
fprintf('%s\n', repmat('-',1,100));

grand_expected = 0;
grand_found = 0;
grand_lost = 0;
grand_dup = 0;
grand_extra = 0;

for t = 1:size(targets,1)
    proto = targets{t,1};
    dataset = targets{t,2};
    shard = targets{t,3};
    pas = targets{t,4};
    sh = sprintf('%03d', shard);

    shard_expected = 0;
    shard_found = 0;
    shard_lost = 0;
    shard_dup = 0;
    shard_extra = 0;

    for p = 1:numel(pas)
        pa = pas{p};

        f = fullfile(root, 'data', proto, 'ota', 'spliced', 'simple', ...
            dataset, ['shard_' sh], ['ota_rx_' pa '.mat']);

        if strcmp(pa, 'PA1')
            exp_wids = ((shard-1)*2000 + 1):(shard*2000);
        else
            local_wids = ((shard-1)*500 + 1):(shard*500);
            exp_wids = core_offsets(pa) + local_wids;
        end

        expected = numel(exp_wids);

        if ~isfile(f)
            fprintf('%-8s %-20s %5d %-4s %10d %10s %10s %10s %10s  MISSING FILE\n', ...
                proto, dataset, shard, pa, expected, '-', '-', '-', '-');

            shard_expected = shard_expected + expected;
            shard_lost = shard_lost + expected;
            continue;
        end

        got = [];

        try
            S = load(f, 'meta_rx');
        catch ME
            fprintf('%-8s %-20s %5d %-4s %10d %10s %10s %10s %10s  LOAD meta_rx FAILED: %s\n', ...
                proto, dataset, shard, pa, expected, '-', '-', '-', '-', ME.message);
            shard_expected = shard_expected + expected;
            shard_lost = shard_lost + expected;
            continue;
        end

        if ~isfield(S, 'meta_rx')
            fprintf('%-8s %-20s %5d %-4s %10d %10s %10s %10s %10s  NO meta_rx\n', ...
                proto, dataset, shard, pa, expected, '-', '-', '-', '-');

            shard_expected = shard_expected + expected;
            shard_lost = shard_lost + expected;
            continue;
        end

        meta = S.meta_rx;

        if isstruct(meta)
            fields = string(fieldnames(meta));

            if any(fields == "window_id")
                got = double([meta.window_id]);
            elseif any(fields == "wid")
                got = double([meta.wid]);
            elseif any(fields == "win_id")
                got = double([meta.win_id]);
            elseif any(fields == "window")
                got = double([meta.window]);
            else
                fprintf('%-8s %-20s %5d %-4s %10d %10s %10s %10s %10s  NO window_id/wid FIELD. Fields: %s\n', ...
                    proto, dataset, shard, pa, expected, '-', '-', '-', '-', strjoin(fields, ','));
                shard_expected = shard_expected + expected;
                shard_lost = shard_lost + expected;
                continue;
            end

        elseif istable(meta)
            fields = string(meta.Properties.VariableNames);

            if any(fields == "window_id")
                got = double(meta.window_id);
            elseif any(fields == "wid")
                got = double(meta.wid);
            elseif any(fields == "win_id")
                got = double(meta.win_id);
            elseif any(fields == "window")
                got = double(meta.window);
            else
                fprintf('%-8s %-20s %5d %-4s %10d %10s %10s %10s %10s  NO window_id/wid TABLE VAR. Vars: %s\n', ...
                    proto, dataset, shard, pa, expected, '-', '-', '-', '-', strjoin(fields, ','));
                shard_expected = shard_expected + expected;
                shard_lost = shard_lost + expected;
                continue;
            end
        else
            fprintf('%-8s %-20s %5d %-4s %10d %10s %10s %10s %10s  meta_rx TYPE NOT STRUCT/TABLE\n', ...
                proto, dataset, shard, pa, expected, '-', '-', '-', '-');
            shard_expected = shard_expected + expected;
            shard_lost = shard_lost + expected;
            continue;
        end

        got = got(:).';
        ugot = unique(got);

        found = numel(intersect(exp_wids, ugot));
        lost = numel(setdiff(exp_wids, ugot));
        dup = numel(got) - numel(ugot);
        extra = numel(setdiff(ugot, exp_wids));

        fprintf('%-8s %-20s %5d %-4s %10d %10d %10d %10d %10d\n', ...
            proto, dataset, shard, pa, expected, found, lost, dup, extra);

        shard_expected = shard_expected + expected;
        shard_found = shard_found + found;
        shard_lost = shard_lost + lost;
        shard_dup = shard_dup + dup;
        shard_extra = shard_extra + extra;
    end

    fprintf('%-8s %-20s %5d %-4s %10d %10d %10d %10d %10d\n', ...
        proto, dataset, shard, 'ALL', shard_expected, shard_found, shard_lost, shard_dup, shard_extra);
    fprintf('%s\n', repmat('-',1,100));

    grand_expected = grand_expected + shard_expected;
    grand_found = grand_found + shard_found;
    grand_lost = grand_lost + shard_lost;
    grand_dup = grand_dup + shard_dup;
    grand_extra = grand_extra + shard_extra;
end

fprintf('%-8s %-20s %5s %-4s %10d %10d %10d %10d %10d\n\n', ...
    'TOTAL', 'retry_targets', '-', 'ALL', grand_expected, grand_found, grand_lost, grand_dup, grand_extra);

