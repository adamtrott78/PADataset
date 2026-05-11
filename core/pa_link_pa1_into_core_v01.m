function summary = pa_link_pa1_into_core_v01(protocols, from_bank, to_bank)
%PA_LINK_PA1_INTO_CORE_V01
% Symlink PA1 bank files from data/<proto>/ota/<from_bank> into data/<proto>/ota/<to_bank>.
%
% This allows DataSetup(source_type="ota", source_name=to_bank) to see PA1 alongside PA2/3/4/8.
%
% Deterministic policy:
% - only links files matching *__PA1.mat
% - does NOT overwrite existing destination files
% - errors if ln fails

    root = string(pa_root());
    protocols = string(protocols(:).');

    from_bank = string(from_bank);
    to_bank   = string(to_bank);

    summary = struct();
    summary.protocols = protocols;
    summary.from_bank = from_bank;
    summary.to_bank   = to_bank;
    summary.linked = struct();

    for p = 1:numel(protocols)
        proto = protocols(p);

        src_dir = fullfile(root, "data", char(proto), "ota", char(from_bank));
        dst_dir = fullfile(root, "data", char(proto), "ota", char(to_bank));

        if ~isfolder(src_dir)
            error("Source bank dir missing: %s", src_dir);
        end
        if ~isfolder(dst_dir)
            mkdir(dst_dir);
        end

        dd = dir(fullfile(src_dir, "*__PA1.mat"));
        if isempty(dd)
            fprintf("LINK | %s | no PA1 bank files found in %s\n", proto, src_dir);
            summary.linked.(char(proto)) = 0;
            continue;
        end

        n_link = 0;
        for i = 1:numel(dd)
            src = fullfile(dd(i).folder, dd(i).name);
            dst = fullfile(dst_dir, dd(i).name);

            if isfile(dst)
                % destination already exists; skip deterministically
                continue;
            end

            cmd = sprintf('ln -s "%s" "%s"', src, dst);
            [rc, out] = system(cmd);
            if rc ~= 0
                error("ln failed (rc=%d): %s\ncmd=%s", rc, out, cmd);
            end
            n_link = n_link + 1;
        end

        fprintf("LINK | %s | linked %d files into %s\n", proto, n_link, dst_dir);
        summary.linked.(char(proto)) = n_link;
    end
end