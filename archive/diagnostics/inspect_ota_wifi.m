function inspect_ota_wifi(do_rename_no_ext)
%INSPECT_OTA_WIFI Locate and sanity-check OTA capture files from inside PADataset/WIFI/.
%
% Place this file at:
%   ...\PADataset\WIFI\inspect_ota_wifi.m
%
% It will look for:
%   ...\PADataset\WIFI\pilot_out_v01\data_ota\ota_rx_S01_PA{2,3,4,8}.mat
%
% Usage:
%   inspect_ota_wifi();          % just report
%   inspect_ota_wifi(true);      % also rename files missing .mat extension

    if nargin < 1, do_rename_no_ext = false; end

    wifi_root = fileparts(mfilename("fullpath"));   % folder containing this script
    data_ota  = fullfile(wifi_root, "pilot_out_v01", "data_ota");

    fprintf("WIFI root : %s\n", wifi_root);
    fprintf("data_ota  : %s\n", data_ota);
    fprintf("pwd       : %s\n\n", pwd);

    if ~isfolder(data_ota)
        error("Missing folder: %s", data_ota);
    end

    % Show what's actually in the folder
    d = dir(fullfile(data_ota, "ota_rx_S01_PA*"));
    fprintf("Files matching ota_rx_S01_PA* (%d):\n", numel(d));
    for k = 1:numel(d)
        fprintf("  %s\n", d(k).name);
    end
    fprintf("\n");

    PAs = ["PA2","PA3","PA4","PA8"];
    session_id = 1;

    for pa = PAs
        base = sprintf("ota_rx_S%02d_%s", session_id, pa);
        fmat = fullfile(data_ota, base + ".mat");
        fraw = fullfile(data_ota, base); % in case it was saved without extension

        f = "";
        if isfile(fmat)
            f = fmat;
        elseif isfile(fraw)
            f = fraw;
            if do_rename_no_ext
                movefile(fraw, fmat);
                fprintf("[RENAMED] %s -> %s\n", fraw, fmat);
                f = fmat;
            end
        else
            fprintf("[MISSING] %s (and %s)\n", fmat, fraw);
            continue;
        end

        fprintf("[OK] %s\n", f);

        % Quick inspect without loading everything into memory
        info = whos("-file", f);
        names = string({info.name});
        fprintf("  vars: %s\n", strjoin(names, ", "));

        % Load expected vars (tolerant)
        S = load(f);
        if isfield(S,"Xrx_all")
            sz = size(S.Xrx_all);
            fprintf("  Xrx_all size: [%d x %d] (%s)\n", sz(1), sz(2), class(S.Xrx_all));
        else
            fprintf("  NOTE: missing Xrx_all\n");
        end
        if isfield(S,"meta_rx")
            fprintf("  meta_rx count: %d\n", numel(S.meta_rx));
        else
            fprintf("  NOTE: missing meta_rx\n");
        end
        if isfield(S,"rx_cfg")
            fprintf("  rx_cfg present\n");
        end
        fprintf("\n");
    end
end