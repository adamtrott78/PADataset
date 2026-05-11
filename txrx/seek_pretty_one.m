function seek_pretty_one()
%SEEK_PRETTY_ONE Render one beautiful spectrogram PNG for a single OTA range.
%
% Run with:
%   matlab -batch "cd('/home/atrott/adamArchives/Adam/varMax/PADataset'); seek_pretty_one"
%
% Output:
%   txrx/seek_outputs_pretty/<protocol>/<run_name>/shard_###/pretty_<a>_<b>.png

    % ============================================================
    % USER SETTINGS
    % ============================================================
    root = '/home/atrott/adamArchives/Adam/varMax/PADataset';

    protocol = "wifi";
    run_name = "wifi_high_smoke";
    shard_id = 1;

    % one range only
    a = 6300001;
    b = 7000000;

    % pretty rendering settings
    out_dpi = 300;
    fig_w = 2600;
    fig_h = 900;

    % pspectrum settings
    freq_resolution_hz = 40e3;   % try 20e3 or 50e3 too
    overlap_percent = 85;        % high overlap = smoother image
    leakage = 0.85;              % pretty/smooth tradeoff

    % color scaling
    use_robust_clim = true;
    clim_lo_pct = 8;
    clim_hi_pct = 99.8;

    % display controls
    show_colorbar = true;
    show_sample_ticks = true;
    show_time_ms_ticks = false;  % set true if you prefer time instead of sample index

    % colormap: turbo / parula / hot
    cmap_name = "turbo";
    % ============================================================

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

    out_dir = fullfile( ...
        root, ...
        'txrx', ...
        'seek_outputs_pretty', ...
        char(protocol), ...
        char(run_name), ...
        sprintf('shard_%03d', shard_id));

    if ~exist(out_dir, 'dir')
        mkdir(out_dir);
    end

    M = matfile(ota_file);
    info = whos(M, 'x_tape');
    if isempty(info)
        error('Variable x_tape not found in %s', ota_file);
    end

    x_size = info.size;
    N = prod(x_size);

    rx_cfg = M.rx_cfg;
    Fs = rx_cfg.Fs;

    a = max(1, round(a));
    b = min(N, round(b));

    if b < a
        error('Invalid range: [%d, %d]', a, b);
    end

    fprintf('Loaded OTA shard:\n  %s\n', ota_file);
    fprintf('Samples: %d | Fs = %.6f MS/s\n', N, Fs/1e6);
    fprintf('Reading pretty range: %d:%d\n', a, b);

    xseg = local_read_xseg(M, x_size, a, b);
    xseg = xseg(:);

    fprintf('Computing pspectrum...\n');
    [P, F, T] = pspectrum( ...
        xseg, Fs, 'spectrogram', ...
        'FrequencyResolution', freq_resolution_hz, ...
        'OverlapPercent', overlap_percent, ...
        'Leakage', leakage);

    % dB image
    PdB = pow2db(P + eps);

    % robust color scaling
    c_lo = min(PdB(:));
    c_hi = max(PdB(:));
    if use_robust_clim
        lo = prctile(PdB(:), clim_lo_pct);
        hi = prctile(PdB(:), clim_hi_pct);
        if isfinite(lo) && isfinite(hi) && hi > lo
            c_lo = lo;
            c_hi = hi;
        end
    end

    % x-axis mapping
    t_sec = T(:).';
    x_abs = a + (t_sec / max(t_sec(end), eps)) * (b - a);
    t_ms = t_sec * 1e3;

    % figure
    f = figure( ...
        'Visible', 'off', ...
        'Color', 'w', ...
        'Position', [100 100 fig_w fig_h]);

    ax = axes(f);
    imagesc(ax, x_abs, F/1e6, PdB);
    axis(ax, 'xy');
    colormap(ax, char(cmap_name));
    clim(ax, [c_lo c_hi]);

    % titles / labels
    title(ax, sprintf('%s | %s | shard %03d | samples %d:%d', ...
        protocol, dataset_full, shard_id, a, b), ...
        'Interpreter', 'none', ...
        'FontWeight', 'bold', ...
        'FontSize', 16);

    ylabel(ax, 'Frequency (MHz)', 'FontSize', 13);

    if show_time_ms_ticks
        xlabel(ax, 'Time within range (ms)', 'FontSize', 13);
        xticks(ax, linspace(x_abs(1), x_abs(end), 8));
        xticklabels(ax, compose('%.1f', linspace(t_ms(1), t_ms(end), 8)));
    elseif show_sample_ticks
        xlabel(ax, 'Sample Index', 'FontSize', 13);
        xt = round(linspace(a, b, 8));
        xticks(ax, xt);
        xticklabels(ax, compose('%d', xt));
    else
        xlabel(ax, '', 'FontSize', 13);
        xticks(ax, []);
    end

    ax.FontSize = 11;
    ax.LineWidth = 1;
    ax.Box = 'on';
    ax.XAxis.Exponent = 0;

    if show_colorbar
        cb = colorbar(ax);
        cb.Label.String = 'Power/Frequency (dB)';
        cb.Label.FontSize = 12;
    end

    % cleaner margins
    set(ax, 'LooseInset', max(get(ax,'TightInset'), 0.02));

    out_png = fullfile(out_dir, sprintf('pretty_%d_%d.png', a, b));
    exportgraphics(f, out_png, 'Resolution', out_dpi);
    close(f);

    fprintf('Saved pretty PNG:\n  %s\n', out_png);
end


function xseg = local_read_xseg(M, x_size, a, b)
    if numel(x_size) ~= 2
        error('x_tape must be a 2-D array/vector.');
    end

    if x_size(1) >= x_size(2)
        xseg = M.x_tape(a:b, 1);
    else
        xseg = M.x_tape(1, a:b);
    end
end