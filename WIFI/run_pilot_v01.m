function run_pilot_v01()
%RUN_PILOT_V01 Pilot generator/validator sanity suite for PA2/PA3/PA4/PA8.
% - Batched generation (no full segments)
% - Computes per-PA pass rates + distributions
% - Cross-PA validator sanity for PA2/PA3/PA4 (PA8 eval only on PA8 windows in v0.1)

    cfg = pa_load_cfg("starter.json");
    pa_validate_cfg(cfg);
    wlanCfg = pa_make_wlan_cfg(cfg);

    out_root = fullfile("pilot_out_v01");
    viz_root = fullfile(out_root, "viz");
    if ~exist(out_root, "dir"), mkdir(out_root); end
    if ~exist(viz_root, "dir"), mkdir(viz_root); end

    % Pilot size knobs
    N_per_pa = 200;        % requested
    batch = 16;            % keep RAM sane (16 windows ~ 50MB signal-only)
    viz_per_pa = 6;        % saves a few diagnostic plots per PA

    % Use 1 session for pilot by default (fast); change to 1:4 if you want session splits now
    sessions = 1;

    PAs = ["PA2","PA3","PA4","PA8"];
    K = numel(PAs);

    % Confusion-like acceptance matrix for PA2/PA3/PA4 only (PA8 requires schedule)
    evalPAs = ["PA2","PA3","PA4"];
    Ke = numel(evalPAs);
    accept_counts = zeros(K, Ke);
    total_counts  = zeros(K, 1);

    % Per-PA metric accumulators (means/stds)
    stats = struct();

    for s = sessions
        session_id = s;
        tape_id = 1;

        for pi = 1:K
            pa = PAs(pi);
            fprintf("\n=== Session %d | %s | target %d windows ===\n", session_id, pa, N_per_pa);

            n_done = 0;
            seg_id = 0;

            % online accumulators for this PA
            acc = init_acc(pa);

            % keep a few windows for viz (store final x + vr + schedule if PA8)
            viz_store = struct("x",[],"vr",[],"sch",[]);
            viz_store.x = cell(0,1); viz_store.vr = cell(0,1); viz_store.sch = cell(0,1);

            while n_done < N_per_pa
                seg_id = seg_id + 1;
                n_batch = min(batch, N_per_pa - n_done);

                plan = pa_plan_segment_windows(cfg, session_id, tape_id, seg_id, n_batch);

                % --- generate signal-only batch ---
                switch pa
                    case "PA2"
                        [Xsig, sch] = pa_gen_windows_pa2_stream(cfg, wlanCfg, session_id, tape_id, seg_id, plan); %#ok<ASGLU>
                    case "PA3"
                        [Xsig, sch] = pa_gen_windows_pa3_stream(cfg, wlanCfg, session_id, tape_id, seg_id, plan); %#ok<ASGLU>
                    case "PA4"
                        [Xsig, sch] = pa_gen_windows_pa4_stream(cfg, wlanCfg, session_id, tape_id, seg_id, plan); %#ok<ASGLU>
                    case "PA8"
                        window_ids = (n_done + (1:n_batch)).';
                        [Xsig, sch] = pa_gen_windows_pa8_stream(cfg, wlanCfg, session_id, tape_id, plan, window_ids);
                    otherwise
                        error("Unknown PA %s", pa);
                end

                % --- validate each window with its PA-specific processor ---
                for i = 1:n_batch
                    window_id = n_done + i; % pilot-global within PA/session (deterministic)
                    x_sig = Xsig(:,i);

                    switch pa
                        case "PA2"
                            [x_fin, vr] = pa_process_window_pa2_v01(cfg, x_sig, session_id, tape_id, seg_id, window_id);
                        case "PA3"
                            [x_fin, vr] = pa_process_window_pa3_v01(cfg, x_sig, session_id, tape_id, seg_id, window_id);
                        case "PA4"
                            [x_fin, vr] = pa_process_window_pa4_v01(cfg, x_sig, session_id, tape_id, seg_id, window_id);
                        case "PA8"
                            [x_fin, vr] = pa_process_window_pa8_v01(cfg, x_sig, sch(i), session_id, tape_id, seg_id, window_id);
                    end

                    total_counts(pi) = total_counts(pi) + 1;

                    % update per-PA accumulators
                    acc = update_acc(acc, pa, vr);

                    % cross-PA sanity for PA2/PA3/PA4
                    for ej = 1:Ke
                        pa_eval = evalPAs(ej);
                        v2 = eval_on(pa_eval, cfg, x_sig, session_id, tape_id, seg_id, window_id);
                        accept_counts(pi, ej) = accept_counts(pi, ej) + double(v2.valid);
                    end

                    % store a few for viz
                    if numel(viz_store.x) < viz_per_pa
                        viz_store.x{end+1,1} = x_fin; %#ok<AGROW>
                        viz_store.vr{end+1,1} = vr;
                        if pa == "PA8"
                            viz_store.sch{end+1,1} = sch(i);
                        else
                            viz_store.sch{end+1,1} = [];
                        end
                    end
                end

                n_done = n_done + n_batch;
                fprintf("  %s: %d/%d done\r", pa, n_done, N_per_pa);
            end
            fprintf("\n");

            stats.(char(pa)) = finalize_acc(acc);

            % write viz pack
            pa_viz_dir = fullfile(viz_root, char(pa));
            if ~exist(pa_viz_dir, "dir"), mkdir(pa_viz_dir); end
            for k = 1:numel(viz_store.x)
                save_viz(pa, cfg, viz_store.x{k}, viz_store.vr{k}, viz_store.sch{k}, fullfile(pa_viz_dir, sprintf("%s_%02d.png", pa, k)));
            end
        end
    end

    % Build acceptance matrix table (rows = generated PA, cols = validator PA2/PA3/PA4)
    rates = accept_counts ./ max(1, total_counts);
    T = array2table(rates, "VariableNames", cellstr(evalPAs), "RowNames", cellstr(PAs));

    fprintf("\n=== Cross-PA acceptance rates (columns are validators) ===\n");
    disp(T);

    save(fullfile(out_root, "pilot_summary_v01.mat"), "cfg", "stats", "T", "accept_counts", "total_counts", "PAs", "evalPAs");
    fprintf("Saved: %s\n", fullfile(out_root, "pilot_summary_v01.mat"));
end

% ---------- helpers ----------

function acc = init_acc(pa)
    acc = struct();
    acc.pa = pa;
    acc.n = 0;
    acc.n_valid = 0;

    % generic accumulators
    acc.sum_peak = 0; acc.sum_papr = 0;

    % semantic det accumulators (only add fields used by that PA)
    acc.sum_shape = 0; acc.sum_energy = 0; acc.sum_cv = 0;
    acc.sum_fj = 0; acc.sum_span = 0;
    acc.sum_sim = 0;
end

function acc = update_acc(acc, pa, vr)
    acc.n = acc.n + 1;
    acc.n_valid = acc.n_valid + double(vr.valid);

    if isfield(vr,"qc")
        acc.sum_peak = acc.sum_peak + double(vr.qc.window_peak);
        acc.sum_papr = acc.sum_papr + double(vr.qc.window_papr);
    end

    if isfield(vr,"det") && isfield(vr.det,"stationarity")
        acc.sum_shape = acc.sum_shape + double(vr.det.stationarity.shape);
        acc.sum_energy = acc.sum_energy + double(vr.det.stationarity.energy);
        acc.sum_cv = acc.sum_cv + double(vr.det.stationarity.energy_cv);
    end

    switch string(pa)
        case "PA2"
            acc.sum_span = acc.sum_span + double(vr.det.burst.span.frac);
        case {"PA3","PA4"}
            acc.sum_span = acc.sum_span + double(vr.det.burst.span.frac);
            acc.sum_fj = acc.sum_fj + double(vr.det.freq.jump.count);
        case "PA8"
            acc.sum_span = acc.sum_span + double(vr.det.repeat.span.frac);
            acc.sum_sim = acc.sum_sim + double(vr.det.repeat.similarity.score);
    end
end

function out = finalize_acc(acc)
    out = struct();
    out.n = acc.n;
    out.valid_rate = acc.n_valid / max(1, acc.n);
    out.mean_peak = acc.sum_peak / max(1, acc.n);
    out.mean_papr = acc.sum_papr / max(1, acc.n);
    out.mean_stationarity_shape = acc.sum_shape / max(1, acc.n);
    out.mean_stationarity_energy = acc.sum_energy / max(1, acc.n);
    out.mean_stationarity_energy_cv = acc.sum_cv / max(1, acc.n);
    out.mean_span = acc.sum_span / max(1, acc.n);
    out.mean_freq_jump = acc.sum_fj / max(1, acc.n);
    out.mean_repeat_similarity = acc.sum_sim / max(1, acc.n);
end

function vr = eval_on(pa_eval, cfg, x_sig, session_id, tape_id, segment_id, window_id)
% Evaluate non-PA8 validators on a given signal-only window.
    switch string(pa_eval)
        case "PA2"
            [~, vr] = pa_process_window_pa2_v01(cfg, x_sig, session_id, tape_id, segment_id, window_id);
        case "PA3"
            [~, vr] = pa_process_window_pa3_v01(cfg, x_sig, session_id, tape_id, segment_id, window_id);
        case "PA4"
            [~, vr] = pa_process_window_pa4_v01(cfg, x_sig, session_id, tape_id, segment_id, window_id);
        otherwise
            error("eval_on only supports PA2/PA3/PA4 in v0.1");
    end
end

function save_viz(pa, cfg, x, vr, sch, out_png)
% Minimal visual sanity plot: envelope + (optional) centroid trace + annotations.
    Fs = double(pa_get_nested(cfg,"rates.fs_hz"));
    t = (0:numel(x)-1)/Fs*1e3; % ms

    f = figure("Visible","off","Color","w","Position",[100 100 1200 650]);
    tiledlayout(2,1,"Padding","compact","TileSpacing","compact");

    % Envelope
    nexttile;
    plot(t, abs(x).^2);
    xlabel("Time (ms)"); ylabel("|x|^2"); title(sprintf("%s envelope | valid=%d | %s", pa, vr.valid, vr.reject_reason), "Interpreter","none");
    grid on;

    % Second panel: centroid bin trace if present, else stationarity text
    nexttile;
    if isfield(vr,"det") && isfield(vr.det,"freq") && isfield(vr.det.freq,"jump") && isfield(vr.det.freq.jump,"bin_trace")
        plot(vr.det.freq.jump.bin_trace, "-");
        xlabel("STFT frame"); ylabel("Centroid bin (1..nbins)"); grid on;
        title(sprintf("freq.jump.count=%d", vr.det.freq.jump.count), "Interpreter","none");
    else
        axis off;
        txt = "";
        if isfield(vr,"det") && isfield(vr.det,"stationarity")
            txt = sprintf("stationarity.shape=%.3f\nstationarity.energy=%.3f\nenergy_cv=%.3f", ...
                vr.det.stationarity.shape, vr.det.stationarity.energy, vr.det.stationarity.energy_cv);
        end
        text(0.05,0.7,txt,"FontSize",14);
        if string(pa)=="PA8" && ~isempty(sch)
            text(0.05,0.4,sprintf("repeats=%d mode=%s span=%.3f sim=%.3f", ...
                sch.repeat_count, string(sch.mode), vr.det.repeat.span.frac, vr.det.repeat.similarity.score), "FontSize",14);
        end
    end

    exportgraphics(f, out_png);
    close(f);
end