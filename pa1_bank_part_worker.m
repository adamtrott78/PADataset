function pa1_bank_part_worker(protocol, dataset_id, shard_id, part_id, n_parts)
%PA1_BANK_PART_WORKER
% Build one temporary PA1 bank part for one shard.
% Safe for parallelism because each part writes a different file.

    protocol = string(protocol);
    dataset_id = string(dataset_id);
    shard_id = double(shard_id);
    part_id = double(part_id);
    n_parts = double(n_parts);

    addpath(fullfile(pa_root(),'core'));
    addpath(fullfile(pa_root(),'txrx'));

    root = string(pa_root());
    pa = "PA1";
    bank_name = "ota_pa1_run01";

    proto_map = containers.Map({'wifi','bluetooth','zigbee'}, {0,1,2});
    proto_code = int32(proto_map(char(protocol)));
    pa_code = int32(0);   % build_ota_bank with pas=["PA1"] gives PA1 label 0

    sh = sprintf('%03d', shard_id);

    src_file = fullfile(root, "data", char(protocol), "ota", "spliced", "simple", ...
        char(dataset_id), "shard_" + sh, "ota_rx_PA1.mat");

    if ~isfile(src_file)
        error("Missing spliced PA1 source: %s", src_file);
    end

    M = matfile(src_file);
    info = whos(M, 'Xrx_all');
    W = info.size(1);
    Ntotal = info.size(2);

    S = load(src_file, 'meta_rx');
    meta = S.meta_rx;

    edges = round(linspace(0, Ntotal, n_parts + 1));
    idx0 = edges(part_id) + 1;
    idx1 = edges(part_id + 1);

    if idx1 < idx0
        error("Empty part: part=%d/%d", part_id, n_parts);
    end

    cols = idx0:idx1;
    N = numel(cols);

    out_dir = fullfile(root, "data", char(protocol), "ota", char(bank_name), "_parts");
    if ~exist(out_dir, "dir")
        mkdir(out_dir);
    end

    out_name = sprintf('%s__shard_%s__PA1__part_%02d_of_%02d.mat', ...
        char(bank_name), sh, part_id, n_parts);
    out_path = fullfile(out_dir, out_name);

    if exist(out_path, 'file')
        delete(out_path);
    end

    fprintf("PA1 PART BANK START | %s | %s | shard=%s | part=%02d/%02d | cols=[%d,%d] | N=%d\n", ...
        protocol, dataset_id, sh, part_id, n_parts, idx0, idx1, N);

    window_id = zeros(N,1,'int32');
    source_col = zeros(N,1,'int32');

    for i = 1:N
        mi = meta(cols(i));
        if isfield(mi, 'window_id')
            window_id(i) = int32(mi.window_id);
        elseif isfield(mi, 'wid')
            window_id(i) = int32(mi.wid);
        else
            window_id(i) = int32(cols(i));
        end
        source_col(i) = int32(cols(i));
    end

    OUT = matfile(out_path, 'Writable', true);

    OUT.X(N, 2, W) = single(0);
    OUT.y(N, 1) = int32(0);
    OUT.proto(N, 1) = int32(0);
    OUT.window_id(N, 1) = int32(0);
    OUT.shard_id(N, 1) = int32(0);
    OUT.record_id(N, 1) = int32(0);
    OUT.source_id(N, 1) = int32(0);
    OUT.source_col(N, 1) = int32(0);
    OUT.part_id = int32(part_id);
    OUT.n_parts = int32(n_parts);

    OUT.y = pa_code * ones(N,1,'int32');
    OUT.proto = proto_code * ones(N,1,'int32');
    OUT.window_id = window_id;
    OUT.shard_id = int32(shard_id) * ones(N,1,'int32');
    OUT.record_id = int32((1:N).');
    OUT.source_id = int32(shard_id) * ones(N,1,'int32');
    OUT.source_col = source_col;

    chunk_n = 8;

    for i0 = 1:chunk_n:N
        i1 = min(N, i0 + chunk_n - 1);
        cols_c = cols(i0:i1);

        Xc = M.Xrx_all(:, cols_c);
        nch = size(Xc, 2);

        xr = permute(reshape(single(real(Xc)), [W, nch, 1]), [2 3 1]);
        xi = permute(reshape(single(imag(Xc)), [W, nch, 1]), [2 3 1]);

        Xchunk = zeros(nch, 2, W, 'single');
        Xchunk(:,1,:) = xr;
        Xchunk(:,2,:) = xi;

        OUT.X(i0:i1,:,:) = Xchunk;

        clear Xc xr xi Xchunk
    end

    fprintf("PA1 PART BANK DONE | %s | %s | shard=%s | part=%02d/%02d | N=%d | file=%s\n", ...
        protocol, dataset_id, sh, part_id, n_parts, N, out_path);
end
