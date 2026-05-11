function find_top_ota_windows_v01(ota_file, out_root, varargin)
%FIND_TOP_OTA_WINDOWS_V01 Scan an OTA capture and save the top-K energetic chunks.
%
% Usage:
%   find_top_ota_windows_v01(ota_file, out_root)
%
%   find_top_ota_windows_v01(ota_file, out_root, ...
%       'window_len', 400000, ...
%       'stride', 100000, ...
%       'top_k', 10)
%
% Notes:
%   - Use window_len=400000 for PA-sized payload windows
%   - Use window_len=700000 for full record-sized windows
%   - Saves PNGs and a .mat report
%   - If graphics on Linux are flaky, run: opengl software

    ip = inputParser;
    addParameter(ip, 'window_len', 400000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'stride', 100000, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'top_k', 10, @(x) isnumeric(x) && isscalar(x) && x >= 1);
    addParameter(ip, 'nfft', 2048, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(ip, 'overlap', 1536, @(x) isnumeric(x) && isscalar(x) && x >= 0);
    parse(ip, varargin{:});

    window_len = double(ip.Results.window_len);
    stride = double(ip.Results.stride);
    top_k = double(ip.Results.top_k);
    nfft = double(ip.Results.nfft);
    overlap = double(ip.Results.overlap);

    if ~exist(out_root, 'dir')
        mkdir(out_root);
    end

    S = load(ota_file, 'x_tape', 'rx_cfg');
    x = S.x_tape(:);
    rx_cfg = S.rx_cfg;
    Fs = double(rx_cfg.Fs);

    N = numel(x);
    if N < window_len
        error('OTA capture is shorter than window_len.');
    end

    starts = 1:stride:(N - window_len + 1);
    nWins = numel(starts);

    stats = struct( ...
        'start_sample', cell(nWins,1), ...
        'end_sample', cell(nWins,1), ...
        'rms', cell(nWins,1), ...
        'mean_abs', cell(nWins,1), ...
        'max_abs', cell(nWins,1));

    fprintf('Scanning OTA file: %s\n', ota_file);
    fprintf('Total samples: %d | Fs = %.6f MS/s\n', N, Fs/1e6);
    fprintf('window_len = %d | stride = %d | candidates = %d\n', window_len, stride, nWins);

    for i = 1:nWins
        a = starts(i);
        b = a + window_len - 1;
        seg = x(a:b);

        stats(i).start_sample = a;
        stats(i).end_sample   = b;
        stats(i).rms          = sqrt(mean(abs(double(seg)).^2));
        stats(i).mean_abs     = mean(abs(double(seg)));
        stats(i).max_abs      = max(abs(double(seg)));
    end

    rms_vals = [stats.rms];
    [~, ord] = sort(rms_vals, 'descend');
    ord = ord(1:min(top_k, numel(ord)));

    report = struct();
    report.ota_file = ota_file;
    report.out_root = out_root;
    report.window_len = window_len;
    report.stride = stride;
    report.top_k = top_k;
    report.Fs = Fs;
    report.overruns = rx_cfg.overruns;
    report.selected = stats(ord);
    report.all_stats = stats;

    save(fullfile(out_root, 'top_windows_report.mat'), 'report', '-v7.3');

    for j = 1:numel(ord)
        k = ord(j);
        a = stats(k).start_sample;
        b = stats(k).end_sample;
        seg = x(a:b);

        png_file = fullfile(out_root, sprintf('rank_%02d_samples_%d_%d.png', j, a, b));
        make_window_plot(seg, Fs, a, b, png_file, nfft, overlap, stats(k));
        fprintf('Saved: %s\n', png_file);
    end

    fprintf('\nTop windows by RMS:\n');
    for j = 1:numel(ord)
        s = stats(ord(j));
        fprintf('  #%02d | [%d : %d] | rms=%.3e | mean|x|=%.3e | max|x|=%.3e\n', ...
            j, s.start_sample, s.end_sample, s.rms, s.mean_abs, s.max_abs);
    end
end

function make_window_plot(seg, Fs, a, b, png_file, nfft, overlap, s)
    t_ms = (0:numel(seg)-1).' / Fs * 1e3;

    fig = figure('Visible', 'off', 'Color', 'w', 'Position', [100 100 1400 900]);
    tl = tiledlayout(fig, 2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

    nexttile(tl, 1);
    plot(t_ms, real(seg), 'b-'); hold on;
    plot(t_ms, imag(seg), 'r-');
    hold off;
    grid on;
    xlabel('Time (ms)');
    ylabel('Amplitude');
    title(sprintf('Waveform | samples [%d : %d] | rms=%.3e | max|x|=%.3e', ...
        a, b, s.rms, s.max_abs));
    legend('Real', 'Imag', 'Location', 'best');

    nexttile(tl, 2);
    spectrogram(seg, hamming(nfft), overlap, nfft, Fs, 'centered', 'yaxis');
    title(sprintf('Spectrogram | samples [%d : %d]', a, b));
    xlabel('Time (s)');

    sgtitle(tl, sprintf('OTA window inspection | [%d : %d]', a, b));

    try
        exportgraphics(fig, png_file, 'Resolution', 150);
    catch
        saveas(fig, png_file);
    end
    close(fig);
end