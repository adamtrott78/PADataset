% core/pa_root.m
function root = pa_root()
    this = fileparts(mfilename('fullpath'));
    root = fileparts(this);   % PADataset/
end