function summary = pa_relabel_bank_labels_v01(protocols, bank_name, pa_names)
%PA_RELABEL_BANK_LABELS_V01
% Overwrite y (labels) in bank files under:
%   data/<proto>/ota/<bank_name>/*.mat
%
% Label mapping is defined by pa_names order:
%   pa_names = ["PA1","PA2","PA3","PA4","PA8"]
% so y = index-1 (int32).
%
% Deterministic policy:
% - PA is parsed ONLY from filename suffix "__PAx.mat"
% - errors if PA token missing or unknown
% - writes y without loading X (matfile writable)

    root = string(pa_root());
    protocols = string(protocols(:).');
    pa_names  = string(pa_names(:).');

    % build map: "PAx" -> int32 code
    pa_to_code = containers.Map('KeyType','char','ValueType','int32');
    for i = 1:numel(pa_names)
        pa_to_code(char(pa_names(i))) = int32(i-1);
    end

    summary = struct();
    summary.protocols = protocols;
    summary.bank_name = string(bank_name);
    summary.pa_names  = pa_names;
    summary.files = {};

    for p = 1:numel(protocols)
        proto = protocols(p);
        bank_dir = fullfile(root, "data", char(proto), "ota", char(bank_name));

        if ~isfolder(bank_dir)
            error("Bank dir missing: %s", bank_dir);
        end

        ff = dir(fullfile(bank_dir, "*.mat"));
        if isempty(ff)
            error("No .mat files in bank dir: %s", bank_dir);
        end

        n_ok = 0;
        for i = 1:numel(ff)
            f = fullfile(ff(i).folder, ff(i).name);

            % parse PA token from filename: ...__PA4.mat
            tok = regexp(ff(i).name, '__([Pp][Aa]\d+)\.mat$', 'tokens', 'once');
            if isempty(tok)
                error("Cannot parse PA token from filename: %s", ff(i).name);
            end
            pa = upper(string(tok{1}));

            if ~isKey(pa_to_code, char(pa))
                error("Unknown PA token %s in %s (pa_names=%s)", pa, ff(i).name, strjoin(pa_names,","));
            end
            y_code = pa_to_code(char(pa));

            % infer N from X without loading it
            SX = whos('-file', f, 'X');
            if isempty(SX)
                error("Missing X in bank file: %s", f);
            end
            N = SX.size(1);

            M = matfile(f, 'Writable', true);
            M.y = repmat(y_code, N, 1); % int32 scalar replicated

            n_ok = n_ok + 1;
            summary.files{end+1,1} = f; %#ok<AGROW>
        end

        fprintf("RELABEL | %s | %s | files=%d\n", proto, bank_name, n_ok);
    end
end