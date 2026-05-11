function out = pa_detect_freq_revisit(bin_trace)
%PA_DETECT_FREQ_REVISIT Revisit detector from centroid-bin trace.
% Revisit present if any centroid bin occurs in >=2 non-consecutive runs.

    k = bin_trace(:);
    if isempty(k)
        out = struct("present",false,"run_bins",zeros(0,1),"run_count",0);
        return;
    end

    % run-length encode bins
    run_bins = k([true; diff(k) ~= 0]);
    run_count = numel(run_bins);

    % revisit if any bin appears in more than one run
    present = numel(unique(run_bins)) < run_count;

    out = struct("present",present,"run_bins",run_bins,"run_count",run_count);
end