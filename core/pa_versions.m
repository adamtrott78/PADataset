function [matlab_version, toolbox_versions] = pa_versions()
%PA_VERSIONS Capture MATLAB + relevant toolbox versions as struct.

    matlab_version = string(version);
    v = ver;
    toolbox_versions = struct();
    for i = 1:numel(v)
        name = matlab.lang.makeValidName(string(v(i).Name));
        toolbox_versions.(name) = string(v(i).Version);
    end
end