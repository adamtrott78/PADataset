function pa_setup_paths()
    root = "/home/atrott/adamArchives/Adam/varMax/PADataset";

    addpath(fullfile(root, "core"));
    addpath(fullfile(root, "txrx"));
    addpath(fullfile(root, "tools"));
    addpath(genpath(fullfile(root, "protocol")));

    cd(root);

    fprintf("PADataset MATLAB paths initialized.\n");
    fprintf("Repo root: %s\n", pa_root());
end