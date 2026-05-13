function pa1_core_split_part_bank_v01(protocol, dataset_suffix, pa1_shard_id, core_shard_id, part_id, parts_per_core, core_bank, chunk_n)
%PA1_CORE_SPLIT_PART_BANK_V01
% Build one PA1 split-part bank file directly in the core bank namespace.
%
% Source:
%   data/<proto>/ota/spliced/simple/<proto>_pa1_run01/shard_<pa1_shard>/ota_rx_PA1.mat
%
% Output:
%   data/<proto>/ota/<core_bank>/<core_bank>__shard_<core_shard>__PA1__part_XX_of_NN.mat
%
% Mapping:
%   core shard 001 expects PA1 window_id 1:500
%   core shard 002 expects PA1 window_id 501:1000
%   ...
%   core shard 020 expects PA1 window_id 9501:10000

    if nargin < 8 || isempty(chunk_n), chunk_n = 8; end

    protocol = string(protocol);
    dataset_suffix = string(dataset_suffix);
    pa1_shard_id = double(pa1_shard_id);
    core_shard_id = double(core_shard_id);
    part_id = double(part_id);
    parts_per_core = double(parts_per_core);
    core_bank = string(core_bank);
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

    expected_pa1_shard = floor((core_shard_id - 1) / 4) + 1;
    if expected_pa1_shard ~= pa1_shard_id
        error("PA1 shard/core shard mismatch: pa1_shard=%d but core_shard=%d expects pa1_shard=%d", ...
            pa1_shard_id, core_shard_id, expected_pa1_shard);
    end

    proto_map = containers.Map({'wifi','bluetooth','zigbee'}, {0,1,2});
    proto_code = int32(proto_map(char(protocol)));
    pa_code = int32(0);  % final label order: PA1=0, PA2=1, PA3=2, PA4=3, PA8=4

    dataset_id = protocol + "_" + dataset_suffix;
    pa1_sh = sprintf('%03d', pa1_shard_id);
    core_sh = sprintf('%03d', core_shard_id);

    src_file = fullfile(root, 'data', char(protocol), 'ota', 'spliced', 'simple', ...
        char(dataset_id), ['shard_' pa1_sh], 'ota_rx_PA1.mat');

    if ~isfile(src_file)
        error("Missing source spliced PA1 file: %s", src_file);
    end

    M = matfile(src_file);
    info = whos(M, 'Xrx_all');
    W = info.size(1);
    Nsrc = info.size(2);

    S = load(src_file, 'meta_rx');
    meta = S.meta_rx;

    if isstruct(meta)
        if isfield(meta, 'window_id')
            all_wids = double([meta.window_id]);
        elseif isfield(meta, 'wid')
            all_wids = double([meta.wid]);
        else
            all_wids = ((pa1_shard_id - 1) * 2000 + 1):((pa1_shard_id - 1) * 2000 + Nsrc);
        end
    elseif istable(meta)
        if any(strcmp(meta.Properties.VariableNames, 'window_id'))
            all_wids = double(meta.window_id(:)).';
        elseif any(strcmp(meta.Properties.VariableNames, 'wid'))
            all_wids = double(meta.wid(:)).';
        else
            all_wids = ((pa1_shard_id - 1) * 2000 + 1):((pa1_shard_id - 1) * 2000 + Nsrc);
        end
    else
        all_wids = ((pa1_shard_id - 1) * 2000 + 1):((pa1_shard_id - 1) * 2000 + Nsrc);
    end

    wid0 = (core_shard_id - 1) * 500 + 1;
    wid1 = core_shard_id * 500;

    selected = find(all_wids >= wid0 & all_wids <= wid1);
    [~, ord] = sort(all_wids(selected));
    selected = selected(ord);

    Ncore = numel(selected);
    if Ncore == 0
        error("No PA1 records found for core shard %03d, expected window_id range [%d,%d]", ...
            core_shard_id, wid0, wid1);
    end

    edges = round(linspace(0, Ncore, parts_per_core + 1));
    i0 = edges(part_id) + 1;
    i1 = edges(part_id + 1);

    if i1 < i0
        error("Empty part for core shard %03d part %d/%d", core_shard_id, part_id, parts_per_core);
    end

    src_cols = selected(i0:i1);
    N = numel(src_cols);

    out_dir = fullfile(root, 'data', char(protocol), 'ota', char(core_bank));
    if ~exist(out_dir, 'dir'), mkdir(out_dir); end

    out_path = fullfile(out_dir, sprintf('%s__shard_%s__PA1__part_%02d_of_%02d.mat', ...
        char(core_bank), core_sh, part_id, parts_per_core));

    if exist(out_path, 'file'), delete(out_path); end

    fprintf("PA1 CORE SPLIT START | proto=%s | pa1_shard=%s | core_shard=%s | wid=[%d,%d] | part=%02d/%02d | Ncore=%d | Npart=%d | W=%d\n", ...
        protocol, pa1_sh, core_sh, wid0, wid1, part_id, parts_per_core, Ncore, N, W);

    window_id = int32(all_wids(src_cols).');

    OUT = matfile(out_path, 'Writable', true);

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
    OUT.shard_id = int32(core_shard_id) * ones(N, 1, 'int32');
    OUT.record_id = int32((1:N).');
    OUT.source_id = int32(pa1_shard_id) * ones(N, 1, 'int32');
    OUT.source_col = int32(src_cols(:));
    OUT.pa1_source_shard_id = int32(pa1_shard_id);
    OUT.core_shard_id = int32(core_shard_id);
    OUT.part_id = int32(part_id);
    OUT.parts_per_core = int32(parts_per_core);

    for j0 = 1:chunk_n:N
        j1 = min(N, j0 + chunk_n - 1);
        cols_c = src_cols(j0:j1);

        Xc = M.Xrx_all(:, cols_c);
        nch = size(Xc, 2);

        xr = permute(reshape(single(real(Xc)), [W, nch, 1]), [2 3 1]);
        xi = permute(reshape(single(imag(Xc)), [W, nch, 1]), [2 3 1]);

        Xchunk = zeros(nch, 2, W, 'single');
        Xchunk(:,1,:) = xr;
        Xchunk(:,2,:) = xi;

        OUT.X(j0:j1,:,:) = Xchunk;

        clear Xc xr xi Xchunk
    end

    fprintf("PA1 CORE SPLIT DONE | proto=%s | core_shard=%s | part=%02d/%02d | N=%d | file=%s\n", ...
        protocol, core_sh, part_id, parts_per_core, N, out_path);
end
