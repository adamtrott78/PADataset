function pa1_merge_part_banks(protocol, dataset_id, shard_id, n_parts)
%PA1_MERGE_PART_BANKS
% Merge PA1 temporary part banks into the normal final PA1 bank file.

    protocol = string(protocol);
    dataset_id = string(dataset_id);
    shard_id = double(shard_id);
    n_parts = double(n_parts);

    addpath(fullfile(pa_root(),'core'));
    addpath(fullfile(pa_root(),'txrx'));

    root = string(pa_root());
    bank_name = "ota_pa1_run01";
    sh = sprintf('%03d', shard_id);

    part_dir = fullfile(root, "data", char(protocol), "ota", char(bank_name), "_parts");
    out_dir = fullfile(root, "data", char(protocol), "ota", char(bank_name));

    if ~exist(out_dir, "dir")
        mkdir(out_dir);
    end

    part_files = strings(n_parts,1);
    Ns = zeros(n_parts,1);

    for p = 1:n_parts
        part_files(p) = string(fullfile(part_dir, sprintf('%s__shard_%s__PA1__part_%02d_of_%02d.mat', ...
            char(bank_name), sh, p, n_parts)));

        if ~isfile(part_files(p))
            error("Missing part file: %s", part_files(p));
        end

        info = whos('-file', part_files(p), 'X');
        Ns(p) = info.size(1);
        W = info.size(3);
    end

    Ntotal = sum(Ns);

    out_path = fullfile(out_dir, sprintf('%s__shard_%s__PA1.mat', char(bank_name), sh));
    tmp_path = out_path + ".tmp";

    if exist(tmp_path, 'file')
        delete(tmp_path);
    end

    fprintf("PA1 MERGE START | %s | %s | shard=%s | parts=%d | N=%d\n", ...
        protocol, dataset_id, sh, n_parts, Ntotal);

    OUT = matfile(tmp_path, 'Writable', true);

    OUT.X(Ntotal, 2, W) = single(0);
    OUT.y(Ntotal, 1) = int32(0);
    OUT.proto(Ntotal, 1) = int32(0);
    OUT.window_id(Ntotal, 1) = int32(0);
    OUT.shard_id(Ntotal, 1) = int32(0);
    OUT.record_id(Ntotal, 1) = int32(0);
    OUT.source_id(Ntotal, 1) = int32(0);

    cursor = 1;
    chunk_n = 8;

    for p = 1:n_parts
        M = matfile(part_files(p));
        Np = Ns(p);
        dst = cursor:(cursor + Np - 1);

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

    % Preserve normal record_id convention after merge.
    OUT.record_id = int32((1:Ntotal).');

    % Atomic-ish replace after complete tmp is written.
    if exist(out_path, 'file')
        backup = out_path + ".bak_" + datestr(now, 'yyyymmdd_HHMMSS');
        movefile(out_path, backup);
        fprintf("PA1 MERGE BACKUP | %s\n", backup);
    end

    movefile(tmp_path, out_path);

    fprintf("PA1 MERGE DONE | %s | N=%d | file=%s\n", out_path, Ntotal, out_path);
end
