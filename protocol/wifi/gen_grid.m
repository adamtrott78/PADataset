function gen_grid()
%SEEK_GEN_GRID_V01
% Generate 10 windows per PA (PA1/PA5/PA6/PA7) using gen_windows_* functions
% and render a 4x10 spectrogram grid (one row per PA).
%
% Inspired by seek(): stacked spectrogram inspection workflow. :contentReference[oaicite:1]{index=1}

    % ---------------- USER SETTINGS ----------------
    PAs = ["PA1","PA5","PA6","PA7"];
    n_per_pa = 10;

    session_id = 1;
    tape_id = 1;

    % Spectrogram params (same style as seek)
    nfft = 1024;
    noverlap = 768;
    win = hamming(nfft);

    use_robust_clim = true;
    clim_lo_pct = 10;
    clim_hi_pct = 99.7;

    fig_width = 3400;      % big: 10 columns
    fig_height = 1400;     % big: 4 rows

    % Output
    out_name = "seek_gen_grid_v01.png";
    % ------------------------------------------------

    root = pa_root();
    addpath(fullfile(root, "core"));
    addpath(genpath(fullfile(root, "protocol")));

    P = pa_paths();
    cfg = pa_load_cfg(fullfile(P.config, "starter.json"));
    wlanCfg = pa_make_wlan_cfg(cfg);

    Fs = double(pa_get_nested(cfg, "rates.fs_hz"));

    out_dir = fullfile(P.results_wifi_digital, "seek_gen_grid_v01");
    if ~exist(out_dir, "dir"), mkdir(out_dir); end
    out_png = fullfile(out_dir, out_name);

    % Pre-generate windows for each PA
    X_by_pa = containers.Map();
    for r = 1:numel(PAs)
        pa = PAs(r);

        % Unique segment id per PA row so schedules differ cleanly
        segment_id = 100 + r;

        plan = pa_plan_segment_windows(cfg, session_id, tape_id, segment_id, n_per_pa);

        switch pa
            case "PA1"
                [Xsig, ~] = pa_gen_windows_pa1_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan);
            case "PA5"
                [Xsig, ~] = pa_gen_windows_pa5_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan);
            case "PA6"
                [Xsig, ~] = pa_gen_windows_pa6_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan);
            case "PA7"
                [Xsig, ~] = pa_gen_windows_pa7_stream(cfg, wlanCfg, session_id, tape_id, segment_id, plan);
            otherwise
                error("Unsupported PA %s", pa);
        end

        X_by_pa(char(pa)) = Xsig; % [W x n_per_pa]
    end

    % ---------------- Render grid ----------------
    f = figure("Visible","off", "Color","w", "Position",[100 100 fig_width fig_height]);
    tl = tiledlayout(numel(PAs), n_per_pa, "TileSpacing","compact", "Padding","compact");

    for r = 1:numel(PAs)
        pa = PAs(r);
        Xsig = X_by_pa(char(pa));

        for c = 1:n_per_pa
            x = Xsig(:,c);
            x = x(:);

            [S,F,T] = spectrogram(x, win, noverlap, nfft, Fs, "centered");
            Pdb = 10*log10(abs(S).^2 + 1e-12);

            ax = nexttile(tl);

            imagesc(ax, T*1e3, F/1e6, Pdb);
            axis(ax, "xy");

            if use_robust_clim
                lo = prctile(Pdb(:), clim_lo_pct);
                hi = prctile(Pdb(:), clim_hi_pct);
                if isfinite(lo) && isfinite(hi) && hi > lo
                    clim(ax, [lo hi]);
                end
            end

            % Minimal labels: row label on first col, col label on top row
            ax.XTick = [];
            ax.YTick = [];

            if c == 1
                ylabel(ax, "MHz");
                ax.YTickMode = "auto";
                ax.YTick = [-10 -5 0 5 10];
                ax.YTickLabel = compose("%g", ax.YTick);
                title(ax, sprintf("%s | #%02d", pa, c), "Interpreter","none", "FontSize", 9, "FontWeight","bold");
            else
                title(ax, sprintf("#%02d", c), "Interpreter","none", "FontSize", 9);
            end

            if r == 1
                % show column titles only on first row
                title(ax, sprintf("%s #%02d", pa, c), "Interpreter","none", "FontSize", 9);
            end

            if c == 1
                % add a left-side row label using annotation-like title
                % (tiledlayout doesn't support row labels directly)
                text(ax, -0.20, 0.5, char(pa), "Units","normalized", ...
                    "Rotation", 90, "HorizontalAlignment","center", ...
                    "FontWeight","bold", "FontSize", 11);
            end
        end
    end

    sgtitle(tl, sprintf("Generated Spectrogram Grid | %d samples each | %s", n_per_pa, strjoin(PAs, ", ")), ...
        "Interpreter","none", "FontWeight","bold");

    exportgraphics(f, out_png, "Resolution", 200);
    close(f);

    fprintf("Saved: %s\n", out_png);
end