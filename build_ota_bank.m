function summary = build_ota_bank(bank_name, wifi_shards, varargin)
%BUILD_OTA_BANK
% Convert respliced OTA windows into prepData-native source files.
%
% Output layout:
%   data/<protocol>/ota/<bank_name>/<bank_name>__shard_###__<PA>.mat
%
% Each output .mat contains:
%   X         [N x 2 x W] single
%   y         [N x 1] int32
%   proto     [N x 1] int32
%   window_id [N x 1] int32
%   shard_id  [N x 1] int32
%   record_id [N x 1] int32
%   source_id [N x 1] int32
%
% Protocol index convention:
%   wifi=0, bluetooth=1, zigbee=2
%
% PA index convention:
%   PA2=0, PA3=1, PA4=2, PA8=3
%
% Example:
%   summary = build_ota_bank("ota_core_high_run01", 8:10, ...
%       'bt_shards', 1:10, 'zb_shards', 1:10);

    ip = inputParser;
    addParameter(ip, 'root', pa_root(), @(x) ischar(x) || isstring(x));
    addParameter(ip, 'run_suffix', "high_run01", @(x) ischar(x) || isstring(x));
    addParameter(ip, 'protocols', ["wifi","bluetooth","zigbee"], @(x) ischar(x) || isstring(x) || iscellstr(x));
    addParameter(ip, 'bt_shards', [], @(x) isempty(x) || isnumeric(x));
    addParameter(ip, 'zb_shards', [], @(x) isempty(x) || isnumeric(x));
    addParameter(ip, 'seed', 0, @(x) isnumeric(x) && isscalar(x));
    addParameter(ip, 'verbose', true, @(x) islogical(x) || isnumeric(x));
    addParameter(ip, 'pas', ["PA2","PA3","PA4","PA8"], @(x) isstring(x) || ischar(x) || iscellstr(x));
    addParameter(ip, 'mode', "balanced", @(x) isstring(x) || ischar(x)); % "balanced" or "all"
    addParameter(ip, 'chunk_n', 16, @(x) isnumeric(x) && isscalar(x) && x > 0); % records per write chunk
    addParameter(ip, 'delete_spliced_after_write', false, @(x) islogical(x) || isnumeric(x));
    parse(ip, varargin{:});

    PROTOS_ALL = ["wifi","bluetooth","zigbee"];
    PROTOS = string(ip.Results.protocols);
    PROTOS = PROTOS(:).';
    PROTOS = intersect(PROTOS_ALL, PROTOS, 'stable');
    
    if isempty(PROTOS)
        error('No valid protocols selected.');
    end

    root = string(ip.Results.root);
    run_suffix = string(ip.Results.run_suffix);
    bt_shards = ip.Results.bt_shards;
    zb_shards = ip.Results.zb_shards;
    seed = double(ip.Results.seed);
    verbose = logical(ip.Results.verbose);

    rng(seed);

    PAS = string(ip.Results.pas);
    PAS = PAS(:).';
    
    PA_TO_IDX = containers.Map('KeyType','char','ValueType','double');
    for i = 1:numel(PAS)
        PA_TO_IDX(char(PAS(i))) = i-1; % 0..K-1 in the order provided
    end
    
    mode = string(ip.Results.mode);
    chunk_n = round(double(ip.Results.chunk_n));
    delete_spliced_after_write = logical(ip.Results.delete_spliced_after_write);
    PROTO_TO_IDX = containers.Map({'wifi','bluetooth','zigbee'}, {0,1,2});

    shard_map = struct();
    shard_map.wifi = sort(unique(double(wifi_shards(:).')));
    shard_map.bluetooth = [];
    shard_map.zigbee = [];

    if ~isempty(bt_shards)
        shard_map.bluetooth = sort(unique(double(bt_shards(:).')));
    end
    if ~isempty(zb_shards)
        shard_map.zigbee = sort(unique(double(zb_shards(:).')));
    end

    % ------------------------------------------------------------
    % Discover respliced source files
    % ------------------------------------------------------------
    src = struct();
    counts = struct();

    for p = 1:numel(PROTOS)
        proto_name = PROTOS(p);
        dataset_id = proto_name + "_" + run_suffix;
        base = fullfile(root, "data", char(proto_name), "ota", "spliced", "simple", char(dataset_id));

        if ~exist(base, "dir")
            error("Respliced OTA directory not found: %s", base);
        end

        if isempty(shard_map.(char(proto_name)))
            dd = dir(fullfile(base, "shard_*"));
            dd = dd([dd.isdir]);
            shard_ids = [];
            for i = 1:numel(dd)
                tok = regexp(dd(i).name, 'shard_(\d+)', 'tokens', 'once');
                if ~isempty(tok)
                    shard_ids(end+1) = str2double(tok{1}); %#ok<AGROW>
                end
            end
            shard_ids = sort(unique(shard_ids));
        else
            shard_ids = shard_map.(char(proto_name));
        end

        for pa = PAS
            key = sprintf('%s__%s', char(proto_name), char(pa));
            src.(key) = struct( ...
                'proto', char(proto_name), ...
                'pa', char(pa), ...
                'dataset_id', char(dataset_id), ...
                'items', [] ...
            );

            total_n = 0;

            for sid = shard_ids
                f = fullfile(base, sprintf('shard_%03d', sid), sprintf('ota_rx_%s.mat', char(pa)));
                if ~isfile(f), continue; end

                S = load(f, 'meta_rx');
                n_cols = numel(S.meta_rx);
                if n_cols == 0, continue; end

                item = struct();
                item.file_path = f;
                item.shard_id = sid;
                item.n_cols = n_cols;
                item.window_ids = arrayfun(@(m) double(m.window_id), S.meta_rx(:));

                src.(key).items = [src.(key).items; item]; %#ok<AGROW>
                total_n = total_n + n_cols;
            end

            counts.(key) = total_n;

            if verbose
                fprintf('BANK DISCOVER | %-10s | %-3s | total=%d\n', char(proto_name), char(pa), total_n);
            end
        end
    end

    % ------------------------------------------------------------
    % Compute balanced target per PA across protocols
    % ------------------------------------------------------------
    target_per_pa = struct();
    for pa = PAS
        c = zeros(1, numel(PROTOS));
        for p = 1:numel(PROTOS)
            proto_name = PROTOS(p);
            key = sprintf('%s__%s', char(proto_name), char(pa));
            c(p) = counts.(key);
        end
    
        target = min(c);
        target_per_pa.(char(pa)) = target;
    
        if verbose
            parts = strings(1, numel(PROTOS));
            for q = 1:numel(PROTOS)
                parts(q) = sprintf('%s=%d', char(PROTOS(q)), c(q));
            end
            fprintf('BANK TARGET | %-3s | %s | target=%d\n', ...
                char(pa), strjoin(parts, ' | '), target);
        end
    end

    % ------------------------------------------------------------
    % Select balanced samples globally per protocol/PA
    % ------------------------------------------------------------
    selected = struct();

    for p = 1:numel(PROTOS)
        proto_name = PROTOS(p);

        for pa = PAS
            key = sprintf('%s__%s', char(proto_name), char(pa));
            items = src.(key).items;
            target = target_per_pa.(char(pa));

            pool = struct( ...
                'file_path', {}, ...
                'shard_id', {}, ...
                'col_idx', {}, ...
                'window_id', {} ...
            );

            for i = 1:numel(items)
                n_cols = items(i).n_cols;
                for c = 1:n_cols
                    rec = struct();
                    rec.file_path = items(i).file_path;
                    rec.shard_id = items(i).shard_id;
                    rec.col_idx = c;
                    rec.window_id = items(i).window_ids(c);
                    pool(end+1,1) = rec; %#ok<AGROW>
                end
            end

            if numel(pool) < target
                error('Not enough samples for %s %s: have %d, need %d', ...
                    char(proto_name), char(pa), numel(pool), target);
            end

            if mode == "all"
                target = numel(pool);
                perm = 1:target;
            else
                perm = randperm(numel(pool), target);
            end
            selected.(key) = pool(perm);
        end
    end

    % ------------------------------------------------------------
    % Group selected samples by source file and write prepData-native bank files
    % ------------------------------------------------------------
    summary = struct();
    summary.bank_name = char(bank_name);
    summary.run_suffix = char(run_suffix);
    summary.target_per_pa = target_per_pa;
    summary.files_written = {};

    for p = 1:numel(PROTOS)
        proto_name = PROTOS(p);
        out_dir = fullfile(root, "data", char(proto_name), "ota", char(bank_name));
        if ~exist(out_dir, "dir")
            mkdir(out_dir);
        end

        for pa = PAS
            key = sprintf('%s__%s', char(proto_name), char(pa));
            sel = selected.(key);

            if isempty(sel)
                continue;
            end

            by_file = containers.Map('KeyType', 'char', 'ValueType', 'any');
            for i = 1:numel(sel)
                fp = sel(i).file_path;
                if ~isKey(by_file, fp)
                    by_file(fp) = [];
                end
                by_file(fp) = [by_file(fp), i];
            end

            file_keys = by_file.keys;
            for k = 1:numel(file_keys)
                src_file = file_keys{k};
                idx_into_sel = by_file(src_file);
                sub = sel(idx_into_sel);

                M = matfile(src_file);

                % vectorized load for all selected columns from this source file
                cols = [sub.col_idx];
                cols_sorted = sort(cols);
                
                if verbose
                    fprintf('BANK ASSEMBLE | %s | shard=%03d | %s | N=%d | span=[%d,%d]\n', ...
                        char(proto_name), sub(1).shard_id, char(pa), numel(cols), ...
                        cols_sorted(1), cols_sorted(end));
                end
                
                c0 = cols_sorted(1);
                c1 = cols_sorted(end);
                
                % matfile requires increasing equally spaced intervals, so load a contiguous span
                % --- open source ---
                M = matfile(src_file);
                
                cols = [sub.col_idx];
                N = numel(cols);
                
                % infer W from Xrx_all without loading full matrix
                info = whos(M, 'Xrx_all');
                W = info.size(1);
                
                pa_code = int32(PA_TO_IDX(char(pa)));
                proto_code = int32(PROTO_TO_IDX(char(proto_name)));
                
                y = pa_code * ones(N, 1, 'int32');
                proto = proto_code * ones(N, 1, 'int32');
                window_id = int32([sub.window_id].');
                shard_id_v = int32([sub.shard_id].');
                record_id = int32((1:N).');
                source_id = shard_id_v;
                
                out_name = sprintf('%s__shard_%03d__%s.mat', char(bank_name), sub(1).shard_id, char(pa));
                out_path = fullfile(out_dir, out_name);
                
                if exist(out_path, 'file'), delete(out_path); end
                
                % --- writable matfile output (v7.3 by construction) ---
                OUT = matfile(out_path, 'Writable', true);
                
                % pre-extend variables WITHOUT allocating huge arrays in RAM
                OUT.X(N, 2, W) = single(0);
                OUT.y(N, 1) = int32(0);
                OUT.proto(N, 1) = int32(0);
                OUT.window_id(N, 1) = int32(0);
                OUT.shard_id(N, 1) = int32(0);
                OUT.record_id(N, 1) = int32(0);
                OUT.source_id(N, 1) = int32(0);
                
                % write 1D vars once
                OUT.y = y;
                OUT.proto = proto;
                OUT.window_id = window_id;
                OUT.shard_id = shard_id_v;
                OUT.record_id = record_id;
                OUT.source_id = source_id;
                
                % chunk-write X
                for i0 = 1:chunk_n:N
                    i1 = min(N, i0 + chunk_n - 1);
                    subc = sub(i0:i1);
                
                    cols_c = [subc.col_idx];
                    c0 = min(cols_c);
                    c1 = max(cols_c);
                
                    % contiguous load then pick requested columns (same idea as your current code)
                    Xblock = M.Xrx_all(:, c0:c1);
                    take_idx = cols_c - c0 + 1;
                    Xc = Xblock(:, take_idx); % [W x nchunk]
                
                    nch = size(Xc, 2);
                
                    xr = permute(reshape(single(real(Xc)), [W, nch, 1]), [2 3 1]); % [nch x 1 x W]
                    xi = permute(reshape(single(imag(Xc)), [W, nch, 1]), [2 3 1]); % [nch x 1 x W]
                
                    Xchunk = zeros(nch, 2, W, 'single');
                    Xchunk(:,1,:) = xr;
                    Xchunk(:,2,:) = xi;
                
                    OUT.X(i0:i1,:,:) = Xchunk;
                
                    clear Xblock Xc xr xi Xchunk
                end
                
                summary.files_written{end+1,1} = out_path;
                
                if verbose
                    fprintf('BANK WRITE | %s | N=%d | chunk_n=%d\n', out_path, N, chunk_n);
                end
                
                % optional: delete the spliced source now that bank file exists
                if delete_spliced_after_write
                    try
                        delete(src_file);
                        if verbose
                            fprintf('BANK CLEAN | deleted spliced source: %s\n', src_file);
                        end
                    catch ME
                        warning('BANK CLEAN | failed delete: %s | %s', src_file, ME.message);
                    end
                end
                
                summary.files_written{end+1,1} = out_path; %#ok<AGROW>
                
                if verbose
                    fprintf('BANK WRITE | %s | N=%d\n', out_path, N);
                end
                
                clear X Xc Xblock xr xi y proto window_id shard_id record_id source_id cols cols_sorted take_idx c0 c1
            end
        end
    end

    if verbose
        fprintf('BANK DONE | %s | files=%d\n', char(bank_name), numel(summary.files_written));
    end
end