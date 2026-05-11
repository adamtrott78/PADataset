root = '/home/atrott/adamArchives/Adam/varMax/PADataset';
addpath(root);

clear validate
rehash

input_spec.protocols   = "wifi";
input_spec.dataset_ids = "wifi_high_run01";
input_spec.shard_ids   = 7;
input_spec.pas         = "PA2";
input_spec.sample_mode = "first_n";
input_spec.n_per_file  = 10;

cfg = struct();
cfg.runtime.verbose = true;
cfg.runtime.print_every = 1;

cfg.output.save_csv = true;
cfg.output.save_mat = true;
cfg.output.out_dir = fullfile(root, "results", "ota", "validation");
cfg.output.base_name = "wifi_high_run01_qc_smoke";

[T, summary] = validate(input_spec, cfg);

disp(summary.overall_final);
disp(summary.by_pa_final);
disp(T(:, ["pa_label","window_id","integrity_label","integrity_score","integrity_reasons","semantic_label","semantic_score","semantic_reasons","final_bin","final_reason"]));
[G, final_bin, integrity_reasons, semantic_reasons] = findgroups(T.final_bin, T.integrity_reasons, T.semantic_reasons);
N = splitapply(@numel, T.final_bin, G);
Tgroups = table(final_bin, integrity_reasons, semantic_reasons, N,'VariableNames',{'final_bin','integrity_reasons','semantic_reasons','count'});
disp(sortrows(Tgroups, 'count', 'descend'));
disp("DONE");
exit