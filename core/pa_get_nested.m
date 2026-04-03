function v = pa_get_nested(s, path)
%PA_GET_NESTED Get nested struct field by dot-path (e.g., "a.b.c").
    parts = split(string(path), ".");
    v = s;
    for i = 1:numel(parts)
        p = char(parts(i));
        if isstruct(v) && isfield(v, p)
            v = v.(p);
        else
            error("Missing field '%s' while resolving '%s'", p, path);
        end
    end
end