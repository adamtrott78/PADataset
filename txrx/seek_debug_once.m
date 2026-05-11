function seek()
    root = '/home/atrott/adamArchives/Adam/varMax/PADataset';

    addpath(fullfile(root, 'core'));
    addpath(fullfile(root, 'txrx'));

    protocol = "zigbee";
    run_name = "zigbee_high_run01";
    shard_id = 1;

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

    % ---- MATFILE access, do not load full tape
    M = matfile(ota_file);
    info = whos(M, 'x_tape');
    N = info.size(1) * info.size(2);

    rx_cfg = M.rx_cfg;
    Fs = rx_cfg.Fs;

    % ------------------------------------------------------------
    % Ranges to inspect
    % ------------------------------------------------------------
    ranges = [
        1 100000
    ];

    use_fixed_tick_step = false;
    tick_step = 10000;
    n_ticks = 20;

    % Max panels per stacked figure
    max_panels_per_fig = 14;

    % Save under /txrx/
    out_dir = fullfile( ...
        root, ...
        'txrx', ...
        'seek_outputs', ...
        char(protocol), ...
        char(dataset_full), ...
        sprintf('shard_%03d', shard_id));

    if ~exist(out_dir, 'dir')
        mkdir(out_dir);
    end

    % Spectrogram settings
    nfft = 1024;
    noverlap = 768;
    win = hamming(nfft);

    fprintf('Loaded OTA shard metadata:\n  %s\n', ota_file);
    fprintf('Samples: %d | Fs = %.6f MS/s\n', N, Fs/1e6);

    % Keep only valid ranges
    keep = ranges(:,1) >= 1 & ranges(:,1) <= N & ranges(:,2) >= ranges(:,1);
    ranges = ranges(keep, :);

    if isempty(ranges)
        error('No valid ranges to process.');
    end

    % Break ranges into pages
    n_ranges = size(ranges, 1);
    n_figs = ceil(n_ranges / max_panels_per_fig);

    for fig_idx = 1:n_figs
        i1 = (fig_idx - 1) * max_panels_per_fig + 1;
        i2 = min(fig_idx * max_panels_per_fig, n_ranges);
        chunk = ranges(i1:i2, :);
        n_this = size(chunk, 1);

        fprintf('\nCreating stacked figure %d/%d with %d ranges...\n', ...
            fig_idx, n_figs, n_this);

        fig_h = max(250 * n_this, 700);
        f = figure( ...
            'Visible', 'off', ...
            'Color', 'w', ...
            'Renderer', 'opengl', ...
            'Position', [100 100 1800 fig_h]);

        tl = tiledlayout(n_this, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

        for j = 1:n_this
            a = chunk(j,1);
            b = min(chunk(j,2), N);

            fprintf('  Reading range %02d: %d:%d ...\n', i1 + j - 1, a, b);
            xseg = M.x_tape(a:b, 1);
            xseg = xseg(:);

            fprintf('  Computing spectrogram for range %02d...\n', i1 + j - 1);
            [SS, FF, TT] = spectrogram(xseg, win, noverlap, nfft, Fs, 'centered');
            PP = 10*log10(abs(SS).^2 + 1e-12);

            ax = nexttile(tl);

            % Convert time axis to absolute sample index
            x_samples = a - 1 + TT * Fs;

            imagesc(ax, x_samples, FF/1e6, PP);
            axis(ax, 'xy');
            xlim(ax, [a b]);

            if use_fixed_tick_step
                xt = a:tick_step:b;
            else
                xt = round(linspace(a, b, n_ticks));
            end

            set(ax, 'XTick', xt);
            set(ax, 'XTickLabel', compose('%.0f', xt));
            xtickangle(ax, 0);

            % Robust color limits so strong bursts do not fully dominate
            lo = prctile(PP(:), 10);
            hi = prctile(PP(:), 99.7);
            if isfinite(lo) && isfinite(hi) && hi > lo
                clim(ax, [lo hi]);
            end

            ylabel(ax, 'MHz');
            title(ax, sprintf('Range %02d | samples %d:%d', i1 + j - 1, a, b), ...
                'Interpreter', 'none');

            xt = get(ax, 'XTick');
            set(ax, 'XTickLabel', compose('%.0f', xt));

            if j < n_this
                ax.XTickLabel = [];
            else
                xlabel(ax, 'Absolute sample index');
            end
        end

        sgtitle(tl, sprintf('Stacked Spectrograms | %s | %s | shard %03d | fig %d/%d', ...
            protocol, dataset_full, shard_id, fig_idx, n_figs), ...
            'Interpreter', 'none');

        out_png = fullfile(out_dir, sprintf('seek_stack_%02d.png', fig_idx));
        fprintf('Saving %s ...\n', out_png);
        
        try
            set(f, 'Renderer', 'opengl');
            print(f, out_png, '-dpng', '-r200');
        catch ME
            warning('print with opengl failed: %s', ME.message);
            try
                set(f, 'Renderer', 'painters');
                print(f, out_png, '-dpng', '-r200');
            catch ME2
                close(f);
                rethrow(ME2);
            end
        end
        
        close(f);
        fprintf('Saved %s\n', out_png);
    end

    fprintf('\nDone.\n');
end