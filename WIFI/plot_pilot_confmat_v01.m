function plot_pilot_confmat_v01(mat_path, out_png)
%PLOT_PILOT_CONFMAT_V01 Plot a confusion-matrix-style heatmap from eval_pilot_v01 outputs.
% Notes:
% - eval_pilot_v01 computes "cross-PA acceptance rates": rows = generated PA, cols = validator.
% - A window can (in principle) be accepted by multiple validators, so this is not a
%   strict single-label confusion matrix. In your current setup (off-diagonals ~0),
%   it behaves like one and is perfect for a slide.
%
% Usage:
%   plot_pilot_confmat_v01()  % uses pilot_out_v01/pilot_summary_v01.mat, writes png next to it
%   plot_pilot_confmat_v01("pilot_out_v01/pilot_summary_v01.mat", "pilot_out_v01/pilot_confmat.png")

    if nargin < 1 || isempty(mat_path)
        mat_path = fullfile("pilot_out_v01","pilot_summary_v01.mat");
    end
    S = load(mat_path);

    % ---- get labels + counts/rates robustly ----
    if isfield(S,"PAs"),     PAs = string(S.PAs);     else, error("Missing PAs in %s", mat_path); end
    if isfield(S,"evalPAs"), evalPAs = string(S.evalPAs); else, evalPAs = PAs; end

    if isfield(S,"accept_counts") && isfield(S,"total_counts")
        accept_counts = double(S.accept_counts);
        total_counts  = double(S.total_counts(:));
        rates = accept_counts ./ max(1, total_counts);           % row-normalized acceptance rates
    elseif isfield(S,"T") && istable(S.T)
        % If you saved the table directly, use it
        rates = table2array(S.T);
        if ~isequal(string(S.T.Properties.RowNames(:)), PAs), PAs = string(S.T.Properties.RowNames(:)); end
        evalPAs = string(S.T.Properties.VariableNames(:));
        accept_counts = []; total_counts = [];
    else
        error("Expected accept_counts+total_counts or table T in %s", mat_path);
    end

    % default output path
    if nargin < 2 || isempty(out_png)
        [p,~,~] = fileparts(mat_path);
        out_png = fullfile(p, "pilot_confmat.png");
    end

    % ---- plot (heatmap with annotations) ----
    fig = figure("Color","w","Position",[100 100 900 700]);

    h = heatmap(evalPAs, PAs, rates);
    h.XLabel = "Validator";
    h.YLabel = "Generated PA";
    h.CellLabelFormat = '%.3f';
    h.ColorLimits = [0 1];

    % Optional: show diagonal summary in command window
    d = diag(rates(:,1:min(end,size(rates,2))));
    fprintf("Diag mean=%.4f | min=%.4f | max=%.4f\n", mean(d,'omitnan'), min(d,[],'omitnan'), max(d,[],'omitnan'));

    exportgraphics(fig, out_png, "Resolution", 200);
    fprintf("Saved confusion-matrix-style plot: %s\n", out_png);

    % Also save a compact .mat next to it for reuse
    out_mat = replace(out_png, ".png", ".mat");
    save(out_mat, "PAs", "evalPAs", "rates", "accept_counts", "total_counts");
    fprintf("Saved matrix data: %s\n", out_mat);

    close(fig);
end