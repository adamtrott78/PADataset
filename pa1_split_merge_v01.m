function pa1_split_merge_v01(protocol, dataset_suffix, shard_id, n_parts, out_bank, chunk_n, replace_existing)
%PA1_SPLIT_MERGE_V01
% Merge temporary PA1 part bank files into the normal final PA1 bank file.
%
% Final output:
%   data/<proto>/ota/<out_bank>/<out_bank>__shard_###__PA1.mat

    if nargin < 6 || isempty(chunk_n), chunk_n = 8; end
    if nargin < 7 || isempty(replace_existing), replace_existing = true; end

    protocol = string(protocol);
    dataset_suffix = string(dataset_suffix); %#ok<NASGU>
    shard_id = double(shard_id);
    n_parts = double(n_parts);
    out_bank = string(out_bank);
    chunk_n = double(chunk_n);
    replace_existing = logical(replace_existing);

    repo = pwd;
    if exist(fullfile(repo, 'core', 'pa_root.m'), 'file')
        addpath(fullfile(repo, 'core'));
    end
    if exist(fullfile(repo, 'txrx'), 'dir')
        addpath(fullfile(repo, 'txrx'));
    end

    if exist('pa_root', 'file')
        root = string(pa_root());
    else
        root = string(repo);
    end

    sh = sprintf('%03d', shard_id);

    part_dir = fullfile(root, 'data', char(protocol), 'ota', char(out_bank), '_parts');
    out_dir  = fullfile(root, 'data', char(protocol), 'ota', char(out_bank));

    if ~exist(out_dir, 'dir'), mkdir(out_dir); end

    part_files = strings(n_parts, 1);
    Ns = zeros(n_parts, 1);
    W = [];

    for p = 1:n_parts
        part_files(p) = string(fullfile(part_dir, sprintf('%s__shard_%s__PA1__part_%02d_of_%02d.mat', ...
            char(out_bank), sh, p, n_parts)));

        if ~isfile(part_files(p))
            error("Missing part file: %s", part_files(p));
        end

        info = whos('-file', part_files(p), 'X');
        Ns(p) = info.size(1);

        if isempty(W)
            W = info.size(3);
        elseif W ~= info.size(3)
            error("W mismatch in part %d: got %d expected %d", p, info.size(3), W);
        end
    end

    Ntotal = sum(Ns);

    out_path = fullfile(out_dir, sprintf('%s__shard_%s__PA1.mat', char(out_bank), sh));
    tmp_path = fullfile(out_dir, sprintf('%s__shard_%s__PA1.tmp.mat', char(out_bank), sh));

    if exist(tmp_path, 'file'), delete(tmp_path); end

    fprintf("PA1 SPLIT MERGE START | proto=%s | shard=%s | parts=%d | N=%d | W=%d | out=%s\n", ...
        protocol, sh, n_parts, Ntotal, W, out_path);

    OUT = matfile(tmp_path, 'Writable', true);

    OUT.X(Ntotal, 2, W) = single(0);
    OUT.y(Ntotal, 1) = int32(0);
    OUT.proto(Ntotal, 1) = int32(0);
    OUT.window_id(Ntotal, 1) = int32(0);
    OUT.shard_id(Ntotal, 1) = int32(0);
    OUT.record_id(Ntotal, 1) = int32(0);
    OUT.source_id(Ntotal, 1) = int32(0);

    cursor = 1;

    for p = 1:n_parts
        M = matfile(part_files(p));
        Np = Ns(p);
        dst = cursor:(cursor + Np - 1);

        fprintf("PA1 SPLIT MERGE PART | shard=%s | part=%02d/%02d | N=%d | dst=[%d,%d]\n", ...
            sh, p, n_parts, Np, dst(1), dst(end));

        OUT.y(dst,1) = M.y(:,1);
        OUT.proto(dst,1) = M.proto(:,1);
        OUT.window_id(dst,1) = M.window_id(:,1);
        OUT.shard_id(dst,1) = M.shard_id(:,1);
        OUT.source_id(dst,1) = M.source_id(:,1);

        for i0 = 1:chunk_n:Np
            i1 = min(Np, i0 + chunk_n - 1);
            OUT.X(cursor+i0-1:cursor+i1-1,:,:) = M.X(i0:i1,:,:);
        end

        cursor = cursor + Np;
    end

    OUT.record_id = int32((1:Ntotal).');

    if exist(out_path, 'file')
        if replace_existing
            backup = fullfile(out_dir, sprintf('%s__shard_%s__PA1.bak_%s.mat', ...
                char(out_bank), sh, datestr(now, 'yyyymmdd_HHMMSS')));
            movefile(out_path, backup);
            fprintf("PA1 SPLIT MERGE BACKUP | %s\n", backup);
        else
            error("Final output already exists and replace_existing=false: %s", out_path);
        end
    end

    movefile(tmp_path, out_path);

    fprintf("PA1 SPLIT MERGE DONE | proto=%s | shard=%s | N=%d | file=%s\n", ...
        protocol, sh, Ntotal, out_path);
end
