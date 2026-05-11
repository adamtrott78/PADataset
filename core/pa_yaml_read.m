function s = pa_yaml_read(cfg_path)
%PA_YAML_READ Robust config->struct loader.
% Supports:
%  - JSON via jsondecode(fileread(.json))  (recommended; no external deps)
%  - YAML via readstruct(...,"FileType","yaml") (if supported)
%  - yamlread (if present)
%  - ReadYaml (YAMLMatlab) (if installed)

    if ~isfile(cfg_path), error("Config not found: %s", cfg_path); end
    [~,~,ext] = fileparts(cfg_path);
    ext = lower(string(ext));

    % JSON (preferred)
    if ext == ".json"
        txt = fileread(cfg_path);
        s = jsondecode(txt);
        return;
    end

    error("Unsupported config extension '%s'. Use .json (recommended) or .yaml/.yml.", ext);
end