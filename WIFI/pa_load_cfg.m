function cfg = pa_load_cfg(cfg_path)
%PA_LOAD_CFG Load config (JSON/YAML) + attach provenance without clobbering cfg.generator.

    cfg = pa_yaml_read(cfg_path);

    % Enrich provenance (non-fatal if unavailable)
    [matlab_version, toolbox_versions] = pa_versions();

    if ~isfield(cfg, "provenance"), cfg.provenance = struct(); end
    cfg.provenance.generator_commit  = pa_git_commit();      % 'unknown' if not in git
    cfg.provenance.generator_version = "v0.1";
    cfg.provenance.matlab_version    = matlab_version;
    cfg.provenance.toolbox_versions  = toolbox_versions;
end

function h = pa_git_commit()
    h = "unknown";
    [ok, out] = system("git rev-parse HEAD");
    if ok == 0
        out = strtrim(string(out));
        if strlength(out) >= 7, h = out; end
    end
end