function refactor_file_paths_v01(do_write, root_override)
%REFACTOR_FILE_PATHS_V01 Semi-automated path migration for active PADataset code.
% Usage:
%   refactor_file_paths_v01()                  % dry run
%   refactor_file_paths_v01(true)              % write changes + .bak backups
%   refactor_file_paths_v01(false, root_path)  % dry run against specific repo root
%
% What it patches:
%   - core/pa_paths.m convenience fields
%   - protocol/wifi active scripts
%   - tools active scripts
%   - txrx active scripts
%
% Notes:
%   - Only active code is touched. archive/ is ignored.
%   - Backups are written as <file>.bak on first write.
%   - Dry-run is the default.

if nargin < 1 || isempty(do_write)
    do_write = false;
end

if nargin < 2 || isempty(root_override)
    % Resolve PADataset root relative to this script:
    % PADataset/tools/refactor_file_paths_v01.m -> PADataset/
    this_file = mfilename('fullpath');
    this_dir  = fileparts(this_file);   % .../PADataset/tools
    root      = fileparts(this_dir);    % .../PADataset
else
    root = char(root_override);
end

if ~isfolder(root)
    error('Repo root not found: %s', root);
end

% Ensure shared helpers are available regardless of current folder
addpath(fullfile(root,'core'));
addpath(fullfile(root,'tools'));
if isfolder(fullfile(root,'txrx'))
    addpath(fullfile(root,'txrx'));
end
if isfolder(fullfile(root,'protocol','wifi'))
    addpath(fullfile(root,'protocol','wifi'));
end

fprintf('refactor_file_paths_v01 | root=%s | mode=%s\n', root, ternary(do_write,'WRITE','DRY-RUN'));

files = {
    fullfile(root,'core','pa_paths.m')
    fullfile(root,'protocol','wifi','gen_pilot_v01.m')
    fullfile(root,'protocol','wifi','eval_pilot_v01.m')
    fullfile(root,'protocol','wifi','run_pilot_v01.m')
    fullfile(root,'tools','eval_ota_quick_v01.m')
    fullfile(root,'tools','make_digital_as_tx12p5_v01.m')
    fullfile(root,'tools','make_pa_slide_png_pipeline_v01.m')
    fullfile(root,'tools','make_png_pairs_from_spliced_v01.m')
    fullfile(root,'tools','plot_pilot_confmat_v01.m')
    fullfile(root,'txrx','build_tx_tape_v03.m')
    fullfile(root,'txrx','rx_capture_tape_v03.m')
    fullfile(root,'txrx','rx_reslice_tape_v05_guided.m')
    fullfile(root,'txrx','rx_resplice_tape_v05.m')
    fullfile(root,'txrx','tx_stream_tape_v03.m')
};

n_seen = 0;
n_changed = 0;

for i = 1:numel(files)
    f = files{i};
    if ~isfile(f)
        fprintf('SKIP missing: %s\n', f);
        continue;
    end
    n_seen = n_seen + 1;

    txt0 = fileread(f);
    txt = txt0;
    [~, name, ext] = fileparts(f);
    base = [name ext];
    log = {};

    switch base
        case 'pa_paths.m'
            [txt, log] = patch_pa_paths(txt, log);
        case 'gen_pilot_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_gen_pilot(txt, log);
        case 'eval_pilot_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_eval_pilot(txt, log);
        case 'run_pilot_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_run_pilot(txt, log);
        case 'eval_ota_quick_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_eval_ota_quick(txt, log);
        case 'make_digital_as_tx12p5_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_make_digital_as_tx12p5(txt, log);
        case 'make_pa_slide_png_pipeline_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_make_pa_slide_png(txt, log);
        case 'make_png_pairs_from_spliced_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_make_png_pairs(txt, log);
        case 'plot_pilot_confmat_v01.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_plot_pilot_confmat(txt, log);
        case 'build_tx_tape_v03.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_build_tx_tape(txt, log);
        case 'rx_capture_tape_v03.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_rx_capture(txt, log);
        case 'rx_reslice_tape_v05_guided.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_rx_reslice_guided(txt, log);
        case 'rx_resplice_tape_v05.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_rx_resplice_v05(txt, log);
        case 'tx_stream_tape_v03.m'
            txt = ensure_pa_paths(txt);
            [txt, log] = patch_tx_stream(txt, log);
        otherwise
            % no-op
    end

    if ~strcmp(txt, txt0)
        n_changed = n_changed + 1;
        fprintf('\n%s: CHANGED\n', relpath_safe(f, root));
        for j = 1:numel(log)
            fprintf('  - %s\n', log{j});
        end

        if do_write
            backup = [f '.bak'];
            if ~isfile(backup)
                write_text(backup, txt0);
            end
            write_text(f, txt);
        end
    else
        fprintf('%s: no changes\n', relpath_safe(f, root));
    end
end

fprintf('\nDone | files_seen=%d | files_changed=%d | mode=%s\n', ...
    n_seen, n_changed, ternary(do_write,'WRITE','DRY-RUN'));

end

% =====================================================================
% Patchers
% =====================================================================

function [txt, log] = patch_pa_paths(txt, log)
block = [ ...
    newline '    P.protocol = fullfile(root, ''protocol'');' newline ...
    '    P.protocol_wifi = fullfile(P.protocol, ''wifi'');' newline ...
    '    P.tools = fullfile(root, ''tools'');' newline ...
    newline ...
    '    P.data_wifi_digital_as_tx12p5 = fullfile(P.data_wifi_digital, ''as_tx12p5'');' newline ...
    newline ...
    '    P.results_wifi_digital_eval_pilot = fullfile(P.results_wifi_digital, ''eval_pilot_v01'');' newline ...
    '    P.results_wifi_digital_eval_pilot_evidence = fullfile(P.results_wifi_digital_eval_pilot, ''evidence_pack'');' newline ...
    '    P.results_wifi_digital_run_pilot = fullfile(P.results_wifi_digital, ''run_pilot_v01'');' newline ...
    '    P.results_wifi_digital_run_pilot_viz = fullfile(P.results_wifi_digital_run_pilot, ''viz'');' newline ...
    '    P.results_wifi_digital_make_pa_slide = fullfile(P.results_wifi_digital, ''make_pa_slide_png_pipeline_v01'');' newline ...
    '    P.results_wifi_ota_eval_quick = fullfile(P.results_wifi_ota, ''eval_ota_quick_v01'');' newline ...
    '    P.results_wifi_ota_eval_quick_png = fullfile(P.results_wifi_ota_eval_quick, ''png'');' newline ...
    '    P.results_rx_resplice_v03_png_pairs = fullfile(P.results_rx_resplice_v03, ''png_pairs'');' newline ...
    '    P.results_rx_resplice_v05_png = fullfile(P.results_rx_resplice_v05, ''png'');' newline ...
    '    P.results_rx_resplice_v05_png_pairs = fullfile(P.results_rx_resplice_v05, ''png_pairs'');' ];

if ~contains(txt, 'P.results_rx_resplice_v05_png_pairs')
    txt = regexprep(txt, '\nend\s*$', [block newline 'end']);
    log{end+1} = 'Added convenience fields to core/pa_paths.m'; %#ok<AGROW>
end
end

function [txt, log] = patch_gen_pilot(txt, log)
[txt, n] = replace_regex(txt, 'cfg\s*=\s*pa_load_cfg\("starter\.json"\);', 'cfg = pa_load_cfg(fullfile(P.config,"starter.json"));');
if n, log{end+1} = 'starter.json -> P.config'; end %#ok<AGROW>

old = [ ...
'    out_root  = fullfile("pilot_out_v01");' newline ...
'    data_root = fullfile(out_root, "data");' newline ...
'    if ~exist(data_root,"dir"), mkdir(data_root); end'];
new = [ ...
'    data_root = P.data_wifi_pilot;' newline ...
'    if ~exist(data_root,"dir"), mkdir(data_root); end'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'pilot_out_v01/data -> P.data_wifi_pilot'; end %#ok<AGROW>
end

function [txt, log] = patch_eval_pilot(txt, log)
[txt, n] = replace_regex(txt, 'cfg\s*=\s*pa_load_cfg\("starter\.json"\);', 'cfg = pa_load_cfg(fullfile(P.config,"starter.json"));');
if n, log{end+1} = 'starter.json -> P.config'; end %#ok<AGROW>

old = [ ...
'    out_root  = fullfile("pilot_out_v01");' newline ...
'    data_root = fullfile(out_root, "data");' newline ...
'    ev_root   = fullfile(out_root, "evidence_pack");' newline ...
'    if ~exist(ev_root,"dir"), mkdir(ev_root); end'];
new = [ ...
'    out_root  = P.results_wifi_digital_eval_pilot;' newline ...
'    data_root = P.data_wifi_pilot;' newline ...
'    ev_root   = P.results_wifi_digital_eval_pilot_evidence;' newline ...
'    if ~exist(out_root,"dir"), mkdir(out_root); end' newline ...
'    if ~exist(ev_root,"dir"), mkdir(ev_root); end'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'eval_pilot outputs -> results/wifi/digital/eval_pilot_v01'; end %#ok<AGROW>
end

function [txt, log] = patch_run_pilot(txt, log)
[txt, n] = replace_regex(txt, 'cfg\s*=\s*pa_load_cfg\("starter\.json"\);', 'cfg = pa_load_cfg(fullfile(P.config,"starter.json"));');
if n, log{end+1} = 'starter.json -> P.config'; end %#ok<AGROW>

old = [ ...
'    out_root = fullfile("pilot_out_v01");' newline ...
'    viz_root = fullfile(out_root, "viz");' newline ...
'    if ~exist(out_root, "dir"), mkdir(out_root); end' newline ...
'    if ~exist(viz_root, "dir"), mkdir(viz_root); end'];
new = [ ...
'    out_root = P.results_wifi_digital_run_pilot;' newline ...
'    viz_root = P.results_wifi_digital_run_pilot_viz;' newline ...
'    if ~exist(out_root, "dir"), mkdir(out_root); end' newline ...
'    if ~exist(viz_root, "dir"), mkdir(viz_root); end'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'run_pilot outputs -> results/wifi/digital/run_pilot_v01'; end %#ok<AGROW>
end

function [txt, log] = patch_eval_ota_quick(txt, log)
old = [ ...
'    % ---------- locate WIFI root (script lives in WIFI/) ----------' newline ...
'    this = fileparts(mfilename("fullpath"));' newline ...
'    wifi_root = this;' newline ...
'    data_ota = fullfile(wifi_root, "pilot_out_v01", "data_ota");' newline ...
'    assert(isfolder(data_ota), "Missing data_ota: %s", data_ota);' newline ...
'' newline ...
'    out_root = fullfile(wifi_root, "pilot_out_v01", "evidence_pack_ota_quick");' newline ...
'    out_png  = fullfile(out_root, "png");' newline ...
'    if exist(out_root,"dir")==0, mkdir(out_root); end' newline ...
'    if exist(out_png,"dir")~=0, rmdir(out_png,"s"); end' newline ...
'    mkdir(out_png);' newline ...
'' newline ...
'    fprintf("OTA QUICK EVAL | data_ota=%s\n", data_ota);'];
new = [ ...
'    data_ota = P.data_wifi_spliced_v05;' newline ...
'    assert(isfolder(data_ota), "Missing data_ota: %s", data_ota);' newline ...
'' newline ...
'    out_root = P.results_wifi_ota_eval_quick;' newline ...
'    out_png  = P.results_wifi_ota_eval_quick_png;' newline ...
'    if exist(out_root,"dir")==0, mkdir(out_root); end' newline ...
'    if exist(out_png,"dir")~=0, rmdir(out_png,"s"); end' newline ...
'    mkdir(out_png);' newline ...
'' newline ...
'    fprintf("OTA QUICK EVAL | data_ota=%s\n", data_ota);'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'eval_ota_quick inputs/outputs redirected to current data/results tree'; end %#ok<AGROW>

[txt, n] = replace_regex(txt, 'cfg\s*=\s*pa_load_cfg\("starter_ota12\.json"\);', 'cfg = pa_load_cfg(fullfile(P.config,"starter_ota12.json"));');
if n, log{end+1} = 'starter_ota12.json -> P.config'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '[xd, Fs_d, ok] = load_digital_match(wifi_root, pa, b.window_id, Fs_force);', ...
    '[xd, Fs_d, ok] = load_digital_match(P.data_wifi_pilot, pa, b.window_id, Fs_force);');
if n, log{end+1} = 'load_digital_match call -> P.data_wifi_pilot'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, 'function [x_dig, Fs_dig, found] = load_digital_match(wifi_root, pa, window_id, Fs_force)', ...
    'function [x_dig, Fs_dig, found] = load_digital_match(data_root, pa, window_id, Fs_force)');
if n, log{end+1} = 'load_digital_match signature updated'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    f = fullfile(wifi_root, "pilot_out_v01", "data", sprintf("pilot_S01_%s.mat", pa)); % TX source', ...
    '    f = fullfile(data_root, sprintf("pilot_S01_%s.mat", pa)); % TX source');
if n, log{end+1} = 'digital pilot lookup -> P.data_wifi_pilot'; end %#ok<AGROW>
end

function [txt, log] = patch_make_digital_as_tx12p5(txt, log)
old = [ ...
'    wifi_root = fileparts(mfilename("fullpath"));' newline ...
'    in_root = fullfile(wifi_root,"pilot_out_v01","data");' newline ...
'    out_root = fullfile(wifi_root,"pilot_out_v01","data_dig_as_tx12p5");' newline ...
'    if ~exist(out_root,"dir"), mkdir(out_root); end'];
new = [ ...
'    in_root = P.data_wifi_pilot;' newline ...
'    out_root = P.data_wifi_digital_as_tx12p5;' newline ...
'    if ~exist(out_root,"dir"), mkdir(out_root); end'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'digital-as-tx12p5 paths -> data/wifi/digital/as_tx12p5'; end %#ok<AGROW>
end

function [txt, log] = patch_make_pa_slide_png(txt, log)
[txt, n] = replace_exact(txt, '    if nargin < 1 || isempty(cfg_file), cfg_file = "starter.json"; end', ...
    '    if nargin < 1 || isempty(cfg_file), cfg_file = fullfile(P.config,"starter.json"); end');
if n, log{end+1} = 'default cfg_file -> P.config/starter.json'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    if nargin < 3 || isempty(out_dir), out_dir = fullfile("pa_slide_png"); end', ...
    '    if nargin < 3 || isempty(out_dir), out_dir = P.results_wifi_digital_make_pa_slide; end');
if n, log{end+1} = 'default out_dir -> results/wifi/digital/make_pa_slide_png_pipeline_v01'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    cfg = pa_load_cfg(cfg_file);', [ ...
'    if ~(contains(string(cfg_file), filesep) || isfile(cfg_file))' newline ...
'        cfg_file = fullfile(P.config, string(cfg_file));' newline ...
'    end' newline ...
'    cfg = pa_load_cfg(cfg_file);']);
if n, log{end+1} = 'cfg_file normalized through P.config when given as bare filename'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    data_root = fullfile("pilot_out_v01","data");', '    data_root = P.data_wifi_pilot;');
if n, log{end+1} = 'pilot data root -> P.data_wifi_pilot'; end %#ok<AGROW>
end

function [txt, log] = patch_make_png_pairs(txt, log)
old = [ ...
'    this = fileparts(mfilename("fullpath"));' newline ...
'    addpath(fullfile(this,"common"));' newline ...
'' newline ...
'    in_ota = fullfile(this,"pilot_out_v01","data_ota_v05_resplice");' newline ...
'    in_dig = fullfile(this,"pilot_out_v01","data");' newline ...
'    out_png = fullfile(this,"pilot_out_v01","evidence_pack_ota_v05","png_pairs");' newline ...
'    if exist(out_png,"dir"), rmdir(out_png,"s"); end' newline ...
'    mkdir(out_png);'];
new = [ ...
'    addpath(P.txrx);' newline ...
'' newline ...
'    in_ota = P.data_wifi_spliced_v05;' newline ...
'    in_dig = P.data_wifi_pilot;' newline ...
'    out_png = P.results_rx_resplice_v05_png_pairs;' newline ...
'    if exist(out_png,"dir"), rmdir(out_png,"s"); end' newline ...
'    mkdir(out_png);'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'png pair paths -> current data/results tree'; end %#ok<AGROW>

[txt, n] = replace_regex(txt, 'cfg\s*=\s*pa_load_cfg\("starter_ota12\.json"\);', 'cfg = pa_load_cfg(fullfile(P.config,"starter_ota12.json"));');
if n, log{end+1} = 'starter_ota12.json -> P.config'; end %#ok<AGROW>
end

function [txt, log] = patch_plot_pilot_confmat(txt, log)
[txt, n] = replace_exact(txt, '        mat_path = fullfile("pilot_out_v01","pilot_summary_v01.mat");', ...
    '        mat_path = fullfile(P.results_wifi_digital_eval_pilot,"pilot_summary_v01.mat");');
if n, log{end+1} = 'default pilot_summary path -> results/wifi/digital/eval_pilot_v01'; end %#ok<AGROW>
end

function [txt, log] = patch_build_tx_tape(txt, log)
old = [ ...
'    this = fileparts(mfilename("fullpath"));' newline ...
'    addpath(fullfile(this,"common"));'];
new = [ ...
'    addpath(P.txrx);'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'txrx self-addpath -> addpath(P.txrx)'; end %#ok<AGROW>

old = [ ...
'    wifi_root = this;' newline ...
'    data_root = fullfile(wifi_root,"pilot_out_v01","data");' newline ...
'    out_root  = fullfile(wifi_root,"pilot_out_v01","tx_tape_v03");' newline ...
'    if ~exist(out_root,"dir"), mkdir(out_root); end'];
new = [ ...
'    data_root = P.data_wifi_pilot;' newline ...
'    out_root  = P.txrx_tapes_digital;' newline ...
'    if ~exist(out_root,"dir"), mkdir(out_root); end'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'build_tx_tape inputs/outputs -> pilot data + txrx/tapes/digital'; end %#ok<AGROW>
end

function [txt, log] = patch_rx_capture(txt, log)
old = [ ...
'    this = fileparts(mfilename("fullpath"));' newline ...
'    addpath(fullfile(this,"common"));' newline ...
'' newline ...
'    tape_file = fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat");'];
new = [ ...
'    addpath(P.txrx);' newline ...
'' newline ...
'    tape_file = fullfile(P.txrx_tapes_digital,"tx_tape_v03.mat");'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'rx_capture digital tape input -> txrx/tapes/digital'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    out_root = fullfile(this,"pilot_out_v01","ota_rx_tape_v03");', ...
    '    out_root = P.txrx_tapes_ota;');
if n, log{end+1} = 'rx_capture output -> txrx/tapes/ota'; end %#ok<AGROW>
end

function [txt, log] = patch_rx_reslice_guided(txt, log)
old = [ ...
'    this = fileparts(mfilename("fullpath"));' newline ...
'    addpath(fullfile(this,"common"));' newline ...
'' newline ...
'    tape_file = fullfile(this,"pilot_out_v01","ota_rx_tape_v03","ota_tape_S01_v03.mat");'];
new = [ ...
'    addpath(P.txrx);' newline ...
'' newline ...
'    tape_file = fullfile(P.txrx_tapes_ota,"ota_tape_S01_v03.mat");'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'guided reslice OTA tape input -> txrx/tapes/ota'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    spec_file = fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat");', ...
    '    spec_file = fullfile(P.txrx_tapes_digital,"tx_tape_v03.mat");');
if n, log{end+1} = 'guided reslice TX tape input -> txrx/tapes/digital'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    out_data = fullfile(this,"pilot_out_v01","data_ota_v03_spliced");', ...
    '    out_data = P.data_wifi_spliced_v03;');
if n, log{end+1} = 'guided reslice output -> data/wifi/ota/spliced/v03'; end %#ok<AGROW>
end

function [txt, log] = patch_rx_resplice_v05(txt, log)
old = [ ...
'    this = fileparts(mfilename("fullpath"));' newline ...
'    addpath(fullfile(this,"common"));' newline ...
'' newline ...
'    T = load(fullfile(this,"pilot_out_v01","ota_rx_tape_v03","ota_tape_S01_v03.mat"), "x_tape", "rx_cfg");'];
new = [ ...
'    addpath(P.txrx);' newline ...
'' newline ...
'    T = load(fullfile(P.txrx_tapes_ota,"ota_tape_S01_v03.mat"), "x_tape", "rx_cfg");'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'rx_resplice OTA tape input -> txrx/tapes/ota'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    S = load(fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat"), "tx_params", "sync", "tx_index");', ...
    '    S = load(fullfile(P.txrx_tapes_digital,"tx_tape_v03.mat"), "tx_params", "sync", "tx_index");');
if n, log{end+1} = 'rx_resplice TX tape input -> txrx/tapes/digital'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    out_data = fullfile(this,"pilot_out_v01","data_ota_v05_resplice");', ...
    '    out_data = P.data_wifi_spliced_v05;');
if n, log{end+1} = 'rx_resplice OTA output -> data/wifi/ota/spliced/v05'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    save(fullfile(out_data, "resplice_summary_v05.mat"), "summary", "drop_log", "-v7.3");', ...
    '    save(fullfile(P.results_rx_resplice_v05, "resplice_summary_v05.mat"), "summary", "drop_log", "-v7.3");');
if n, log{end+1} = 'resplice summary -> results/wifi/ota/rx_resplice_tape_v05'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    png_root = fullfile(this,"pilot_out_v01","evidence_pack_ota_v05","png");', ...
    '    png_root = P.results_rx_resplice_v05_png;');
if n, log{end+1} = 'resplice PNG root -> results/wifi/ota/rx_resplice_tape_v05/png'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '            [x_d, Fs_d, ok] = load_digital_by_window_id_v05(this, pa, wid);', ...
    '            [x_d, Fs_d, ok] = load_digital_by_window_id_v05(P.data_wifi_pilot, pa, wid);');
if n, log{end+1} = 'digital pair lookup call -> P.data_wifi_pilot'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, 'function [x_d, Fs_d, ok] = load_digital_by_window_id_v05(wifi_root, pa, wid)', ...
    'function [x_d, Fs_d, ok] = load_digital_by_window_id_v05(data_root, pa, wid)');
if n, log{end+1} = 'load_digital_by_window_id_v05 signature updated'; end %#ok<AGROW>

[txt, n] = replace_exact(txt, '    f = fullfile(wifi_root, "pilot_out_v01", "data", sprintf("pilot_S01_%s.mat", pa));', ...
    '    f = fullfile(data_root, sprintf("pilot_S01_%s.mat", pa));');
if n, log{end+1} = 'digital pair lookup path -> P.data_wifi_pilot'; end %#ok<AGROW>

% ensure results root exists before summary/pngs
[txt, n] = replace_exact(txt, '    if ~exist(out_data,"dir"), mkdir(out_data); end', ...
    ['    if ~exist(out_data,"dir"), mkdir(out_data); end' newline ...
     '    if ~exist(P.results_rx_resplice_v05,"dir"), mkdir(P.results_rx_resplice_v05); end']);
if n, log{end+1} = 'ensure rx_resplice results root exists'; end %#ok<AGROW>
end

function [txt, log] = patch_tx_stream(txt, log)
old = [ ...
'    this = fileparts(mfilename("fullpath"));' newline ...
'    addpath(fullfile(this,"common"));' newline ...
'' newline ...
'    tape_file = fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat");'];
new = [ ...
'    addpath(P.txrx);' newline ...
'' newline ...
'    tape_file = fullfile(P.txrx_tapes_digital,"tx_tape_v03.mat");'];
[txt, n] = replace_exact(txt, old, new);
if n, log{end+1} = 'tx_stream tape input -> txrx/tapes/digital'; end %#ok<AGROW>
end

% =====================================================================
% Utilities
% =====================================================================

function txt = ensure_pa_paths(txt)
if contains(txt, 'P = pa_paths();')
    return;
end
lines = splitlines(string(txt));
inserted = false;
for i = 1:min(numel(lines), 20)
    if startsWith(strtrim(lines(i)), "function ")
        lines = [lines(1:i); "    P = pa_paths();"; lines(i+1:end)];
        inserted = true;
        break;
    end
end
if ~inserted
    lines = ["P = pa_paths();"; lines];
end
txt = strjoin(lines, newline);
end

function [txt, changed] = replace_exact(txt, old, new)
if contains(txt, old)
    txt = strrep(txt, old, new);
    changed = true;
else
    changed = false;
end
end

function [txt, changed] = replace_regex(txt, pattern, repl)
newtxt = regexprep(txt, pattern, repl);
changed = ~strcmp(newtxt, txt);
txt = newtxt;
end

function write_text(pathstr, txt)
fid = fopen(pathstr, 'w');
if fid < 0
    error('Could not open for write: %s', pathstr);
end
cleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fwrite(fid, txt);
end

function out = relpath_safe(pathstr, root)
try
    out = erase(pathstr, [root filesep]);
catch
    out = pathstr;
end
end

function out = ternary(cond, a, b)
if cond
    out = a;
else
    out = b;
end
end