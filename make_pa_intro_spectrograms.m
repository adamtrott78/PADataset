function make_pa_intro_spectrograms(sample_mode, fixed_index)
%MAKE_PA_INTRO_SPECTROGRAMS_V01
% Create 12 spectrogram images, one for each protocol / PA combo, from the
% digital noisy dataset used for training.
%
% Expected input files:
%   data/<protocol>/digital/pilot_noisy_torch/pilot_noisy_torch_S01_<PA>.mat
%
% Expected variable in each file:
%   X  -> usually [N, 2, T]
%
% Optional variable:
%   meta
%
% Usage:
%   make_pa_intro_spectrograms_v01
%   make_pa_intro_spectrograms_v01("first")
%   make_pa_intro_spectrograms_v01("random")
%   make_pa_intro_spectrograms_v01("fixed", 7)
%
% Output:
%   results/presentation/pa_intro_spectrograms/*.png

    if nargin < 1 || isempty(sample_mode)
        sample_mode = "first";   % "first" | "random" | "fixed"
    end
    if nargin < 2 || isempty(fixed_index)
        fixed_index = 1;
    end

    rng(1);  % deterministic if using random mode

    % ---------------------------------------------------------------------
    % Resolve repo root
    % ---------------------------------------------------------------------
    if exist('pa_root', 'file') == 2
        root = pa_root();
    else
        root = local_find_repo_root(pwd);
    end

    if strlength(root) == 0
        error('Could not resolve PADataset repo root.');
    end

    out_dir = fullfile(root, "results", "presentation", "pa_intro_spectrograms");
    if ~exist(out_dir, 'dir')
        mkdir(out_dir);
    end

    protocols = ["wifi", "bluetooth", "zigbee"];
    PAs = ["PA2", "PA3", "PA4", "PA8"];

    % ---------------------------------------------------------------------
    % Spectrogram settings
    % ---------------------------------------------------------------------
    nfft = 1024;
    noverlap = 768;
    win = hann(nfft, "periodic");

    fprintf('Saving spectrograms to:\n  %s\n\n', out_dir);

    for protocol = protocols
        for pa = PAs

            in_file = fullfile(root, "data", protocol, "digital", ...
                "pilot_noisy_torch", sprintf("pilot_noisy_torch_S01_%s.mat", pa));

            if ~isfile(in_file)
                warning('Missing file: %s', in_file);
                continue;
            end

            S = load(in_file);

            if ~isfield(S, 'X')
                warning('File does not contain variable X: %s', in_file);
                continue;
            end

            X = S.X;
            meta = [];
            if isfield(S, 'meta')
                meta = S.meta;
            end

            [x_iq, sample_idx, n_samples] = local_pick_sample(X, sample_mode, fixed_index);

            % x_iq should be [2, T]
            x_iq = single(x_iq);
            x_c = complex(x_iq(1,:), x_iq(2,:));

            Fs = local_get_fs(meta, sample_idx);

            [SS, FF, TT] = spectrogram(x_c, win, noverlap, nfft, Fs, "centered");
            PP = 10*log10(abs(SS).^2 + 1e-12);

            % dynamic range clamp for cleaner figures
            cmax = max(PP(:));
            clim_lo = cmax - 60;

            f = figure('Visible', 'off', 'Color', 'w', ...
                'Position', [100 100 1400 420]);

            imagesc(TT*1e3, FF/1e6, PP);
            axis xy;
            colormap turbo;
            colorbar;
            clim([clim_lo cmax]);

            xlabel('Time (ms)', 'FontSize', 12);
            ylabel('Frequency (MHz)', 'FontSize', 12);
            title(sprintf('%s — %s Spectrogram', ...
                local_pretty_protocol(protocol), pa), ...
                'FontSize', 14, 'FontWeight', 'bold');

            set(gca, 'FontSize', 11);

            out_png = fullfile(out_dir, sprintf('spectrogram_%s_%s.png', protocol, pa));
            exportgraphics(f, out_png, 'Resolution', 200);
            close(f);

            wid_txt = "";
            if ~isempty(meta)
                wid_txt = local_get_window_id_text(meta, sample_idx);
            end

            fprintf('Saved %-55s | sample %d / %d%s\n', ...
                out_png, sample_idx, n_samples, wid_txt);
        end
    end

    fprintf('\nDone.\n');
end


function [x_iq, sample_idx, n_samples] = local_pick_sample(X, sample_mode, fixed_index)
% Supports:
%   X as [N, 2, T]
%   X as [2, T, N]

    sz = size(X);

    if ndims(X) ~= 3
        error('Expected X to be 3-D, got size %s', mat2str(sz));
    end

    if sz(2) == 2
        % [N, 2, T]
        n_samples = sz(1);

        switch string(sample_mode)
            case "first"
                sample_idx = 1;
            case "random"
                sample_idx = randi(n_samples);
            case "fixed"
                sample_idx = min(max(1, round(fixed_index)), n_samples);
            otherwise
                error('Unknown sample_mode: %s', sample_mode);
        end

        x_iq = squeeze(X(sample_idx, :, :));

    elseif sz(1) == 2
        % [2, T, N]
        n_samples = sz(3);

        switch string(sample_mode)
            case "first"
                sample_idx = 1;
            case "random"
                sample_idx = randi(n_samples);
            case "fixed"
                sample_idx = min(max(1, round(fixed_index)), n_samples);
            otherwise
                error('Unknown sample_mode: %s', sample_mode);
        end

        x_iq = squeeze(X(:, :, sample_idx));

    else
        error('Unsupported X shape: %s', mat2str(sz));
    end

    if ~isequal(size(x_iq,1), 2)
        error('Selected sample is not [2, T]. Got size %s', mat2str(size(x_iq)));
    end
end


function Fs = local_get_fs(meta, sample_idx)
    Fs = 20e6;  % fallback default

    if isempty(meta)
        return;
    end

    try
        if numel(meta) >= sample_idx && isfield(meta(sample_idx), 'fs_hz')
            Fs = double(meta(sample_idx).fs_hz);
        end
    catch
        % keep fallback
    end
end


function txt = local_get_window_id_text(meta, sample_idx)
    txt = "";
    try
        if numel(meta) >= sample_idx && isfield(meta(sample_idx), 'window_id')
            txt = sprintf(' | window_id=%d', double(meta(sample_idx).window_id));
        end
    catch
        txt = "";
    end
end


function name = local_pretty_protocol(protocol)
    switch string(protocol)
        case "wifi"
            name = "WiFi";
        case "bluetooth"
            name = "Bluetooth";
        case "zigbee"
            name = "Zigbee";
        otherwise
            name = string(protocol);
    end
end


function root = local_find_repo_root(start_dir)
% Walk upward looking for a folder that looks like the PADataset repo root.

    root = "";
    d = string(start_dir);

    for k = 1:10
        has_data = exist(fullfile(d, 'data'), 'dir') == 7;
        has_results = exist(fullfile(d, 'results'), 'dir') == 7;
        has_txrx = exist(fullfile(d, 'txrx'), 'dir') == 7;

        if has_data && has_results && has_txrx
            root = d;
            return;
        end

        parent = string(fileparts(d));
        if parent == d
            break;
        end
        d = parent;
    end
end