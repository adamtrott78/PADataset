function summary = generate_all_pretty_ota_pngs(repo_root)
%GENERATE_ALL_PRETTY_OTA_PNGS
%
% Generate the 15 clean OTA spectrogram assets used by the MILCOM deck:
%
%   3 protocols:
%       wifi
%       bluetooth
%       zigbee
%
%   5 behaviors:
%       PA1 -> Scan
%       PA2 -> Burst
%       PA3 -> Sustain
%       PA4 -> Hop
%       PA8 -> Replay
%
% Input layout:
%
%   data/<protocol>/ota/ota_core_high_run01/
%
% Files contain:
%
%   X : [N_windows x 2 x 400000] single
%
% where:
%
%   X(k,1,:) = I
%   X(k,2,:) = Q
%
% IMPORTANT:
%   PA1 uses the split files inside ota_core_high_run01:
%
%       *__PA1__part_01_of_02.mat
%       *__PA1__part_02_of_02.mat
%
%   The separate ota_pa1_run01 files are intentionally NOT used because
%   some of those files are truncated / unreadable.
%
% Output:
%
%   presentations/milcom2026/assets/ota/<protocol>/
%
%       scan.png
%       burst.png
%       sustain.png
%       hop.png
%       replay.png
%
% Example:
%
%   cd('/home/atrott/adamArchives/Adam/varMax/PADataset')
%   summary = generate_all_pretty_ota_pngs(pwd);

    if nargin < 1 || isempty(repo_root)
        repo_root = pwd;
    end

    repo_root = char(repo_root);

    % ---------------------------------------------------------------------
    % OTA sample rate
    % ---------------------------------------------------------------------
    Fs = 12.5e6;

    % ---------------------------------------------------------------------
    % Protocols
    % ---------------------------------------------------------------------
    protocols = {
        'wifi'
        'bluetooth'
        'zigbee'
    };

    % ---------------------------------------------------------------------
    % PA -> behavior mapping
    % ---------------------------------------------------------------------
    pa_specs = {
        'PA1', 'Scan'
        'PA2', 'Burst'
        'PA3', 'Sustain'
        'PA4', 'Hop'
        'PA8', 'Replay'
    };

    % For this first complete pass, use window 1 from the first readable
    % candidate file for each protocol / PA combination.
    window_idx = 1;

    % Results log
    summary = struct( ...
        'protocol', {}, ...
        'pa', {}, ...
        'behavior', {}, ...
        'source_file', {}, ...
        'window_idx', {}, ...
        'output_png', {} );

    result_idx = 0;

    fprintf('\n');
    fprintf('============================================================\n');
    fprintf('MILCOM OTA SPECTROGRAM GENERATOR\n');
    fprintf('============================================================\n');
    fprintf('Repo root:\n  %s\n', repo_root);
    fprintf('Fs: %.3f MS/s\n', Fs / 1e6);
    fprintf('\n');

    % =====================================================================
    % MAIN LOOP
    % =====================================================================
    for ip = 1:numel(protocols)

        protocol = protocols{ip};

        fprintf('\n');
        fprintf('============================================================\n');
        fprintf('=== %s ===\n', upper(protocol));
        fprintf('============================================================\n');

        out_dir = fullfile( ...
            repo_root, ...
            'presentations', ...
            'milcom2026', ...
            'assets', ...
            'ota', ...
            protocol);

        if ~exist(out_dir, 'dir')
            mkdir(out_dir);
        end

        for ipa = 1:size(pa_specs, 1)

            pa_label = pa_specs{ipa, 1};
            behavior = pa_specs{ipa, 2};

            fprintf('\n[%s / %s]\n', protocol, behavior);

            % -------------------------------------------------------------
            % Find candidate source files
            % -------------------------------------------------------------
            candidate_files = local_candidate_files( ...
                repo_root, protocol, pa_label);

            if isempty(candidate_files)
                error( ...
                    'No candidate files found for %s / %s (%s).', ...
                    protocol, behavior, pa_label);
            end

            % -------------------------------------------------------------
            % Try candidates until one reads successfully
            % -------------------------------------------------------------
            x = [];
            chosen_file = '';

            for ic = 1:numel(candidate_files)

                this_file = candidate_files{ic};

                fprintf('  Trying:\n');
                fprintf('    %s\n', this_file);

                try
                    x = local_load_window_as_complex( ...
                        this_file, window_idx);

                    chosen_file = this_file;

                    fprintf('  Read OK.\n');
                    break;

                catch ME
                    fprintf(2, '  SKIPPING unreadable candidate.\n');
                    fprintf(2, '    %s\n', ME.message);

                    x = [];
                    chosen_file = '';
                end
            end

            if isempty(x)
                error( ...
                    'Every candidate failed for %s / %s (%s).', ...
                    protocol, behavior, pa_label);
            end

            % -------------------------------------------------------------
            % Render
            % -------------------------------------------------------------
            out_png = fullfile( ...
                out_dir, ...
                sprintf('%s.png', lower(behavior)));

            local_render_clean_spectrogram( ...
                x, Fs, out_png);

            fprintf('  Selected source:\n');
            fprintf('    %s\n', chosen_file);
            fprintf('  Saved:\n');
            fprintf('    %s\n', out_png);

            % -------------------------------------------------------------
            % Log
            % -------------------------------------------------------------
            result_idx = result_idx + 1;

            summary(result_idx).protocol    = protocol;
            summary(result_idx).pa          = pa_label;
            summary(result_idx).behavior    = behavior;
            summary(result_idx).source_file = chosen_file;
            summary(result_idx).window_idx  = window_idx;
            summary(result_idx).output_png  = out_png;
        end
    end

    % =====================================================================
    % FINAL REPORT
    % =====================================================================
    fprintf('\n');
    fprintf('============================================================\n');
    fprintf('DONE\n');
    fprintf('============================================================\n');
    fprintf('Generated %d PNG files.\n', numel(summary));
    fprintf('\n');

    for k = 1:numel(summary)
        fprintf('%-10s %-8s -> %s\n', ...
            summary(k).protocol, ...
            summary(k).behavior, ...
            summary(k).output_png);
    end

    if numel(summary) ~= 15
        warning( ...
            'Expected 15 protocol/behavior assets, generated %d.', ...
            numel(summary));
    else
        fprintf('\nAll 15 protocol × behavior assets generated successfully.\n');
    end
end


% =========================================================================
% FIND SOURCE FILES
% =========================================================================
function files_out = local_candidate_files(repo_root, protocol, pa_label)

    core_dir = fullfile( ...
        repo_root, ...
        'data', ...
        protocol, ...
        'ota', ...
        'ota_core_high_run01');

    files_out = {};

    if ~exist(core_dir, 'dir')
        return;
    end

    if strcmpi(pa_label, 'PA1')

        % -------------------------------------------------------------
        % PA1 / Scan
        %
        % Use ONLY the healthy split files stored in the core OTA set.
        %
        % Example:
        %
        % ota_core_high_run01__shard_001__PA1__part_01_of_02.mat
        % ota_core_high_run01__shard_001__PA1__part_02_of_02.mat
        %
        % Each file is an independent bank of complete 400000-sample
        % windows. They do NOT need to be concatenated.
        % -------------------------------------------------------------
        d = dir(fullfile( ...
            core_dir, ...
            'ota_core_high_run01__shard_*__PA1__part_*.mat'));

    else

        % -------------------------------------------------------------
        % PA2 / PA3 / PA4 / PA8
        %
        % Example:
        %
        % ota_core_high_run01__shard_001__PA2.mat
        % -------------------------------------------------------------
        d = dir(fullfile( ...
            core_dir, ...
            sprintf( ...
                'ota_core_high_run01__shard_*__%s.mat', ...
                pa_label)));
    end

    if isempty(d)
        return;
    end

    % Filenames contain zero-padded shard IDs, so lexical sorting also
    % gives correct shard order.
    [~, order] = sort({d.name});
    d = d(order);

    for k = 1:numel(d)
        files_out{end+1} = fullfile( ...
            d(k).folder, ...
            d(k).name); %#ok<AGROW>
    end
end


% =========================================================================
% LOAD ONE WINDOW
% =========================================================================
function x = local_load_window_as_complex(mat_file, window_idx)
%
% Read ONE record from X without loading the full multi-GB tensor.
%
% Expected:
%
%   X = [N_windows x 2 x N_samples]
%
% Returns:
%
%   x = complex column vector [N_samples x 1]
%

    M = matfile(mat_file);

    info = whos(M, 'X');

    if isempty(info)
        error('Variable X not found in %s', mat_file);
    end

    sz = info.size;

    if numel(sz) ~= 3
        error( ...
            'Expected X to be 3-D; got size %s in %s', ...
            mat2str(sz), ...
            mat_file);
    end

    if sz(2) ~= 2
        error( ...
            'Expected X shape [N, 2, T]; got %s in %s', ...
            mat2str(sz), ...
            mat_file);
    end

    n_windows = sz(1);

    if window_idx < 1 || window_idx > n_windows
        error( ...
            'Requested window %d, but file contains %d windows.', ...
            window_idx, ...
            n_windows);
    end

    % ---------------------------------------------------------------------
    % IMPORTANT:
    %
    % Read only a single [1 x 2 x T] record.
    %
    % Do NOT call load(mat_file), because X may be many gigabytes.
    % ---------------------------------------------------------------------
    x_iq = squeeze(M.X(window_idx, :, :));

    % Expected after squeeze:
    %
    %   [2 x 400000]
    %
    % Be defensive about orientation.
    if size(x_iq, 1) ~= 2 && size(x_iq, 2) == 2
        x_iq = x_iq.';
    end

    if size(x_iq, 1) ~= 2
        error( ...
            'Selected record is not [2 x T]. Got %s in %s', ...
            mat2str(size(x_iq)), ...
            mat_file);
    end

    I = single(x_iq(1, :));
    Q = single(x_iq(2, :));

    x = complex(I, Q);
    x = x(:);

    if isempty(x)
        error('Selected IQ window is empty.');
    end

    if ~all(isfinite(x))
        error('Selected IQ window contains non-finite values.');
    end

    if rms(x) == 0
        error('Selected IQ window has zero RMS.');
    end
end


% =========================================================================
% RENDER CLEAN PRESENTATION SPECTROGRAM
% =========================================================================
function local_render_clean_spectrogram(x, Fs, out_png)
%
% Produce a high-resolution spectrogram with:
%
%   - no title
%   - no axes
%   - no tick labels
%   - no colorbar
%   - no margins
%
% Intended to be embedded directly inside the MILCOM SVG slides.
%

    % ---------------------------------------------------------------------
    % STFT settings
    % ---------------------------------------------------------------------
    nfft = 1024;
    noverlap = 768;
    win = hann(nfft, 'periodic');

    [S, F, T] = spectrogram( ...
        x, ...
        win, ...
        noverlap, ...
        nfft, ...
        Fs, ...
        'centered');

    PdB = 10 * log10(abs(S).^2 + 1e-12);

    % ---------------------------------------------------------------------
    % Presentation-friendly dynamic range
    %
    % Historical PA presentation renderer used a fixed 60 dB range below
    % the strongest spectral component.
    % ---------------------------------------------------------------------
    cmax = max(PdB(:));
    clim_lo = cmax - 60;

    % ---------------------------------------------------------------------
    % Large raster source image
    % ---------------------------------------------------------------------
    fig = figure( ...
        'Visible', 'off', ...
        'Color', 'w', ...
        'Position', [100 100 2400 1000]);

    ax = axes( ...
        fig, ...
        'Position', [0 0 1 1]);

    imagesc( ...
        ax, ...
        T * 1e3, ...
        F / 1e6, ...
        PdB);

    axis(ax, 'xy');
    axis(ax, 'off');

    colormap(ax, turbo);

    clim(ax, [clim_lo cmax]);

    % Ensure destination exists
    out_dir = fileparts(out_png);

    if ~exist(out_dir, 'dir')
        mkdir(out_dir);
    end

    % High-resolution PNG
    exportgraphics( ...
        ax, ...
        out_png, ...
        'Resolution', 300);

    close(fig);
end