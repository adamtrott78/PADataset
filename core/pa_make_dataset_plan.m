function plan = pa_make_dataset_plan(protocol, snr_regime, dataset_id, varargin)
%PA_MAKE_DATASET_PLAN Deterministic shard/seed plan for one protocol x SNR combo.
%
% This planner decouples dataset identity from transport sharding.
% A fixed seed_session_id and seed_tape_id define the whole combo. Segment IDs
% and global window IDs are canonical and DO NOT depend on how many tape shards
% you later build.
%
% Usage:
%   plan = pa_make_dataset_plan("wifi", "high", "wifi_high_v1")
%   plan = pa_make_dataset_plan("bluetooth", "mid", "bt_mid_v1", ...
%           'n_per_pa', 10000, 'n_shards', 10, 'windows_per_segment', 10)
%
% Key outputs:
%   plan.shards(s).tasks(k)
%       .pa
%       .seed_segment_id
%       .global_window_ids
%       .n_windows
%
% The intended flow is:
%   1) make one plan for protocol+regime
%   2) generate pilot shard files from this plan
%   3) build tx_tape shards from those pilot shard files
%
% Defaults are chosen for your large acquisition target:
%   n_per_pa = 10000
%   n_shards = 10
%   windows_per_segment = 10
%
% That yields, per protocol+regime:
%   4 PAs x 10000 windows = 40000 windows total
%   10 shards x 4000 windows/shard
%   each shard has 1000 windows/PA

    ip = inputParser();
    ip.addParameter('n_per_pa', 10000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('n_shards', 10, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('windows_per_segment', 10, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('seed_session_id', 1, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('seed_tape_id', 1, @(x) isnumeric(x) && isscalar(x) && x > 0);
    ip.addParameter('pa_order', ["PA2","PA3","PA4","PA8"], @(x) isstring(x) || ischar(x) || iscellstr(x));
    ip.parse(varargin{:});

    protocol = string(protocol);
    snr_regime = string(snr_regime);
    dataset_id = string(dataset_id);

    assert(any(protocol == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    n_per_pa = double(ip.Results.n_per_pa);
    n_shards = double(ip.Results.n_shards);
    windows_per_segment = double(ip.Results.windows_per_segment);
    seed_session_id = double(ip.Results.seed_session_id);
    seed_tape_id = double(ip.Results.seed_tape_id);
    pa_order = string(ip.Results.pa_order);

    assert(mod(n_per_pa, n_shards) == 0, 'n_per_pa must be divisible by n_shards');
    assert(mod(n_per_pa / n_shards, windows_per_segment) == 0, ...
        'windows_per_shard_per_pa must be divisible by windows_per_segment');

    windows_per_shard_per_pa = n_per_pa / n_shards;
    segments_per_pa = n_per_pa / windows_per_segment;
    segments_per_shard_per_pa = windows_per_shard_per_pa / windows_per_segment;

    plan = struct();
    plan.protocol = char(protocol);
    plan.snr_regime = char(snr_regime);
    plan.dataset_id = char(dataset_id);
    plan.pa_order = pa_order;
    plan.n_per_pa = n_per_pa;
    plan.n_shards = n_shards;
    plan.windows_per_segment = windows_per_segment;
    plan.windows_per_shard_per_pa = windows_per_shard_per_pa;
    plan.segments_per_pa = segments_per_pa;
    plan.segments_per_shard_per_pa = segments_per_shard_per_pa;
    plan.seed_session_id = seed_session_id;
    plan.seed_tape_id = seed_tape_id;  % IMPORTANT: fixed for whole combo

    % Canonical global window numbering: blocked by PA.
    % PA2: 1..N, PA3: N+1..2N, PA4: 2N+1..3N, PA8: 3N+1..4N.
    pa_base = containers.Map('KeyType','char','ValueType','double');
    for p = 1:numel(pa_order)
        pa_base(char(pa_order(p))) = (p-1) * n_per_pa;
    end

    % Canonical segment numbering for segment-based PAs.
    % Keep PA2/PA3/PA4 segment_id namespaces disjoint so seeds never depend on
    % shard grouping and never collide across PAs.
    seg_base = containers.Map('KeyType','char','ValueType','double');
    intrinsic_pas = ["PA8"];  % window-intrinsic PAs
    seg_cands = setdiff(pa_order, intrinsic_pas, "stable");  % everything else is segment-based
    for p = 1:numel(seg_cands)
        seg_base(char(seg_cands(p))) = (p-1) * segments_per_pa;
    end

    shards = repmat(struct('shard_id',0,'tasks',[]), 1, n_shards);

    for s = 1:n_shards
        tasks = struct('pa', {}, 'seed_segment_id', {}, 'global_window_ids', {}, ...
            'global_pa_local_idx', {}, 'n_windows', {}, 'transport_shard_id', {});

        task_idx = 0;
        for p = 1:numel(pa_order)
            pa = string(pa_order(p));
            pa0 = pa_base(char(pa));

            first_local = (s-1)*windows_per_shard_per_pa + 1;
            last_local  = s*windows_per_shard_per_pa;
            
            switch pa
                case "PA8"
                    % window-intrinsic
                    for j = first_local:windows_per_segment:last_local
                        task_idx = task_idx + 1;
                        gw_local = j:(j + windows_per_segment - 1);
                        tasks(task_idx).pa = char(pa);
                        tasks(task_idx).seed_segment_id = 0;
                        tasks(task_idx).global_pa_local_idx = gw_local;
                        tasks(task_idx).global_window_ids = pa0 + gw_local;
                        tasks(task_idx).n_windows = windows_per_segment;
                        tasks(task_idx).transport_shard_id = s;
                    end
            
                otherwise
                    % segment-based (PA1, PA5, PA6, PA7, PA2, PA3, PA4, etc.)
                    if ~isKey(seg_base, char(pa))
                        error('Unsupported PA %s', pa);
                    end
            
                    seg0 = seg_base(char(pa));
                    first_seg_local = (s-1)*segments_per_shard_per_pa + 1;
                    last_seg_local  = s*segments_per_shard_per_pa;
            
                    for j = first_seg_local:last_seg_local
                        task_idx = task_idx + 1;
                        gw_local = ((j-1)*windows_per_segment + 1) : (j*windows_per_segment);
                        tasks(task_idx).pa = char(pa);
                        tasks(task_idx).seed_segment_id = seg0 + j;
                        tasks(task_idx).global_pa_local_idx = gw_local;
                        tasks(task_idx).global_window_ids = pa0 + gw_local;
                        tasks(task_idx).n_windows = windows_per_segment;
                        tasks(task_idx).transport_shard_id = s;
                    end
            end

        shards(s).shard_id = s;
        shards(s).tasks = tasks;
    end

    plan.shards = shards;
    plan.created_utc = char(datetime('now','TimeZone','UTC','Format','yyyy-MM-dd''T''HH:mm:ss''Z'''));
end
