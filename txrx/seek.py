function seek()
%SEEK Inspect OTA tape ranges with stacked spectrograms.
%
% Best used in batch mode if MATLAB web graphics are unstable:
%   matlab -batch "cd('/home/atrott/adamArchives/Adam/varMax/PADataset'); seek"
%
% Edit the USER SETTINGS section below.

    % ============================================================
    % USER SETTINGS
    % ============================================================
    root = '/home/atrott/adamArchives/Adam/varMax/PADataset';

    protocol = "bluetooth";
    run_name = "bluetooth_high_run01";
    shard_id = 1;

    % Ranges to inspect: [start_sample end_sample]
    ranges = [
        1750000 2000000
        % 6500000 6900000
        % 7400000 7800000
        % 8100000 8300000
    ];

    % Max number of stacked panels per output figure
    max_panels_per_fig = 10;

    % Spectrogram parameters
    nfft = 1024;
    noverlap = 768;
    win = hamming(nfft);

    % Robust color scaling
    use_robust_clim = true;
    clim_lo_pct = 10;
    clim_hi_pct = 99.7;

    % X-axis control
    % x_tick_mode = 'step'  -> use x_tick_step
    % x_tick_mode = 'count' -> use x_tick_count
    x_tick_mode = 'step';
    x_tick_step = 50000;   % sample spacing between tick marks
    x_tick_count = 8;      % used only if x_tick_mode='count'

    % Figure sizing
    fig_width = 2200;
    panel_height = 280;
    min_fig_height = 700;

    % Save under /txrx/
    out_dir = fullfile( ...
        root, ...
        'txrx', ...
        'seek_outputs', ...
        char(protocol), ...
        char(run_name), ...
        sprintf('shard_%03d', shard_id));

    % Show colorbar on every subplot
    show_colorbar = false;
    % ============================================================


    % ----------------------------
    % Paths
    % ----------------------------
    addpath(fullfile(root, 'core'));
    addpath(fullfile(root, 'txrx'));

    protocol = string(protocol);
    run_name = string(run_name);

    prefix = protocol + "_";
    if startsWith(run_name, prefix)
        dataset_full = run_name;
    else
        dataset_full = prefix + run_name;
    end

    R = pa_protocol_roots(protocol);

    ota_file = fullfile( ...
        R.txrx_tapes_ota, ...
        char(dataset_full), ...
        sprintf('ota_tape_shard_%03d.mat', shard_id));

    if ~isfile(ota_file)
        error('OTA shard file not found: %s', ota_file);
    end

    if ~exist(out_dir, 'dir')
        mkdir(out_dir);
    end

    % ----------------------------
    % MAT-file access
    % ----------------------------
    M = matfile(ota_file);
    info = whos(M, 'x_tape');
    if isempty(info)
        error('Variable x_tape not found in %s', ota_file);
    end

    x_size = info.size;
    N = prod(x_size);

    rx_cfg = M.rx_cfg;
    Fs = rx_cfg.Fs;

    fprintf('Loaded OTA shard metadata:\n  %s\n', ota_file);
    fprintf('Samples: %d | Fs = %.6f MS/s\n', N, Fs/1e6);

    % ----------------------------
    % Validate ranges
    % ----------------------------
    if isempty(ranges)
        error('No ranges provided.');
    end

    keep = ranges(:,1) >= 1 & ranges(:,1) <= N & ranges(:,2) >= ranges(:,1);
    ranges = ranges(keep, :);

    if isempty(ranges)
        error('No valid ranges to process.');
    end

    n_ranges = size(ranges, 1);
    n_figs = ceil(n_ranges / max_panels_per_fig);

    % ----------------------------
    % Process figures
    % ----------------------------
    for fig_idx = 1:n_figs
        i1 = (fig_idx - 1) * max_panels_per_fig + 1;
        i2 = min(fig_idx * max_panels_per_fig, n_ranges);
        chunk = ranges(i1:i2, :);
        n_this = size(chunk, 1);

        fprintf('\nCreating stacked figure %d/%d with %d ranges...\n', ...
            fig_idx, n_figs, n_this);

        fig_h = max(min_fig_height, panel_height * n_this);

        f = figure( ...
            'Visible', 'off', ...
            'Color', 'w', ...
            'Position', [100 100 fig_width fig_h]);

        tl = tiledlayout(n_this, 1, ...
            'TileSpacing', 'compact', ...
            'Padding', 'compact');

        for j = 1:n_this
            global_idx = i1 + j - 1;
            a = chunk(j,1);
            b = min(chunk(j,2), N);

            fprintf('  Reading range %02d: %d:%d ...\n', global_idx, a, b);

            xseg = local_read_xseg(M, x_size, a, b);
            xseg = xseg(:);

            fprintf('  Computing spectrogram for range %02d...\n', global_idx);
            [SS, FF, ~] = spectrogram(xseg, win, noverlap, nfft, Fs, 'centered');
            PP = 10*log10(abs(SS).^2 + 1e-12);

            % Map spectrogram columns to absolute sample indices
            n_cols = size(PP, 2);
            x_abs = linspace(a, b, n_cols);

            ax = nexttile(tl);
            imagesc(ax, x_abs, FF/1e6, PP);
            axis(ax, 'xy');
            xlim(ax, [a b]);

            % Robust color scaling
            if use_robust_clim
                lo = prctile(PP(:), clim_lo_pct);
                hi = prctile(PP(:), clim_hi_pct);
                if isfinite(lo) && isfinite(hi) && hi > lo
                    clim(ax, [lo hi]);
                end
            end

            ylabel(ax, 'MHz');
            title(ax, sprintf('Range %02d | samples %d:%d', global_idx, a, b), ...
                'Interpreter', 'none');

            % X ticks
            xt = local_make_xticks(a, b, x_tick_mode, x_tick_step, x_tick_count);
            set(ax, 'XTick', xt);
            ax.XAxis.Exponent = 0;

            % Force literal integer tick labels
            xtlbl = arrayfun(@(v) sprintf('%.0f', v), xt, 'UniformOutput', false);
            set(ax, 'XTickLabel', xtlbl);

            xlabel(ax, 'Absolute sample index');

            if show_colorbar
                colorbar(ax);
            end
        end

        sgtitle(tl, sprintf( ...
            'Stacked Spectrograms | %s | %s | shard %03d | fig %d/%d', ...
            protocol, dataset_full, shard_id, fig_idx, n_figs), ...
            'Interpreter', 'none');

        out_png = fullfile(out_dir, sprintf('seek_stack_%02d.png', fig_idx));
        exportgraphics(f, out_png, 'Resolution', 200);
        close(f);

        fprintf('Saved %s\n', out_png);
    end

    fprintf('\nDone.\n');
end


function xseg = local_read_xseg(M, x_size, a, b)
% Read x_tape(a:b) without loading the whole MAT file.

    if numel(x_size) ~= 2
        error('x_tape must be a 2-D array/vector.');
    end

    if x_size(1) >= x_size(2)
        % Column vector / tall vector
        xseg = M.x_tape(a:b, 1);
    else
        % Row vector
        xseg = M.x_tape(1, a:b);
    end
end


function xt = local_make_xticks(a, b, x_tick_mode, x_tick_step, x_tick_count)
% Build x-axis ticks either by fixed spacing or by tick count.

    mode_str = lower(char(string(x_tick_mode)));

    switch mode_str
        case 'step'
            if isempty(x_tick_step) || x_tick_step <= 0
                xt = round(linspace(a, b, max(2, x_tick_count)));
                xt = unique(xt);
                return;
            end

            first_tick = ceil(a / x_tick_step) * x_tick_step;
            xt = first_tick:x_tick_step:b;

            % Always include endpoints
            xt = unique([a xt b]);

        case 'count'
            if isempty(x_tick_count) || x_tick_count < 2
                x_tick_count = 2;
            end
            xt = round(linspace(a, b, x_tick_count));
            xt = unique(xt);

        otherwise
            error('Unsupported x_tick_mode: %s', x_tick_mode);
    end
end