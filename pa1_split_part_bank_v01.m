function pa1_split_part_bank_v01(protocol, dataset_suffix, shard_id, part_id, n_parts, out_bank, chunk_n)
%PA1_SPLIT_PART_BANK_V01
% Build one temporary PA1 bank part from one spliced PA1 file.
%
% Safe parallelism rule:
%   each worker writes a different part file.
%
% Source:
%   data/<proto>/ota/spliced/simple/<proto>_<dataset_suffix>/shard_###/ota_rx_PA1.mat
%
% Part output:
%   data/<proto>/ota/<out_bank>/_parts/<out_bank>__shard_###__PA1__part_XX_of_NN.mat

    if nargin < 7 || isempty(chunk_n), chunk_n = 8; end

    protocol = string(protocol);
    dataset_suffix = string(dataset_suffix);
    shard_id = double(shard_id);
    part_id = double(part_id);
    n_parts = double(n_parts);
    out_bank = string(out_bank);
    chunk_n = double(chunk_n);

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

    proto_map = containers.Map({'wifi','bluetooth','zigbee'}, {0,1,2});
    proto_code = int32(proto_map(char(protocol)));

    pa_code = int32(0); % PA1-only bank uses label 0

    dataset_id = protocol + "_" + dataset_suffix;
    sh = sprintf('%03d', shard_id);

    src_file = fullfile(root, 'data', char(protocol), 'ota', 'spliced', 'simple', ...
        char(dataset_id), ['shard_' sh], 'ota_rx_PA1.mat');

    if ~isfile(src_file)
        error("Missing spliced source: %s", src_file);
    end

    M = matfile(src_file);
    info = whos(M, 'Xrx_all');
    W = info.size(1);
    Ntotal = info.size(2);

    S = load(src_file, 'meta_rx');
    meta = S.meta_rx;

    edges = round(linspace(0, Ntotal, n_parts + 1));
    c0 = edges(part_id) + 1;
    c1 = edges(part_id + 1);

    if c1 < c0
        error("Empty part: protocol=%s shard=%03d part=%d/%d", protocol, shard_id, part_id, n_parts);
    end

    cols = c0:c1;
    N = numel(cols);

    out_dir = fullfile(root, 'data', char(protocol), 'ota', char(out_bank), '_parts');
    if ~exist(out_dir, 'dir'), mkdir(out_dir); end

    out_path = fullfile(out_dir, sprintf('%s__shard_%s__PA1__part_%02d_of_%02d.mat', ...
        char(out_bank), sh, part_id, n_parts));

    if exist(out_path, 'file'), delete(out_path); end

    fprintf("PA1 SPLIT PART START | proto=%s | dataset=%s | shard=%s | part=%02d/%02d | cols=[%d,%d] | N=%d | W=%d\n", ...
        protocol, dataset_id, sh, part_id, n_parts, c0, c1, N, W);

    window_id = zeros(N, 1, 'int32');

    if isstruct(meta)
        for ii = 1:N
            mi = meta(cols(ii));
            if isfield(mi, 'window_id')
                window_id(ii) = int32(mi.window_id);
            elseif isfield(mi, 'wid')
                window_id(ii) = int32(mi.wid);
            else
                window_id(ii) = int32(cols(ii));
            end
        end
    elseif istable(meta)
        if any(strcmp(meta.Properties.VariableNames, 'window_id'))
            window_id = int32(meta.window_id(cols));
        elseif any(strcmp(meta.Properties.VariableNames, 'wid'))
            window_id = int32(meta.wid(cols));
        else
            window_id = int32(cols(:));
        end
    else
        window_id = int32(cols(:));
    end

    OUT = matfile(out_path, 'Writable', true);

    % Pre-extend variables without allocating full bank in RAM.
    OUT.X(N, 2, W) = single(0);
    OUT.y(N, 1) = int32(0);
    OUT.proto(N, 1) = int32(0);
    OUT.window_id(N, 1) = int32(0);
    OUT.shard_id(N, 1) = int32(0);
    OUT.record_id(N, 1) = int32(0);
    OUT.source_id(N, 1) = int32(0);
    OUT.source_col(N, 1) = int32(0);

    OUT.y = pa_code * ones(N, 1, 'int32');
    OUT.proto = proto_code * ones(N, 1, 'int32');
    OUT.window_id = window_id(:);
    OUT.shard_id = int32(shard_id) * ones(N, 1, 'int32');
    OUT.record_id = int32((1:N).');
    OUT.source_id = int32(shard_id) * ones(N, 1, 'int32');
    OUT.source_col = int32(cols(:));
    OUT.part_id = int32(part_id);
    OUT.n_parts = int32(n_parts);

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

    fprintf("PA1 SPLIT PART DONE | proto=%s | dataset=%s | shard=%s | part=%02d/%02d | N=%d | file=%s\n", ...
        protocol, dataset_id, sh, part_id, n_parts, N, out_path);
end
