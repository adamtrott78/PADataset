jobs_real = [
    struct("protocol","wifi",      "dataset_id","wifi_high_run01",      "shards",1:20,"do_capture",true,"do_resplice",true)
    struct("protocol","bluetooth", "dataset_id","bluetooth_high_run01", "shards",1:20,"do_capture",true,"do_resplice",true)
    struct("protocol","zigbee",    "dataset_id","zigbee_high_run01",    "shards",1:20,"do_capture",true,"do_resplice",true)

    struct("protocol","wifi",      "dataset_id","wifi_pa1_run01",       "shards",1:5, "do_capture",true,"do_resplice",true)
    struct("protocol","bluetooth", "dataset_id","bluetooth_pa1_run01",  "shards",1:5, "do_capture",true,"do_resplice",true)
    struct("protocol","zigbee",    "dataset_id","zigbee_pa1_run01",     "shards",1:5, "do_capture",true,"do_resplice",true)
];

jobs_fix = [
  struct("protocol","wifi","dataset_id","wifi_high_run01","shards",[4 6 7 9 12:20], "do_capture",false,"do_resplice",true)
];

capture_resplice_batch(jobs_fix, ...
  'skip_if_bank_exists', true, ...
  'max_capture_attempts', 20, ...
  'max_capture_events', 4, ...
  'min_fill_frac', 0.999, ...
  'pause_between_capture_attempts_s', 5.0, ...
  
  'seed_k', 100000, ...
  'seed_radius', 50000, ...
  'search_radius', 500, ...
  'slip_frames', -3:3, ...
  'auto_skip_records', 20, ...
  'auto_skip_search_radius', 500, ...
  'resplice_min_keep_frac', 0.98);


% =========================
% POST: build feature caches
% =========================

PY = "/home/atrott/miniforge3/envs/DNNs/bin/python";  % your env python
py_script = fullfile(pa_root(), "cacheBuild.py");
data_root = fullfile(pa_root(), "data");

% --- Cache 1: OTA core ---
cache_root_core = fullfile(getenv("HOME"), ...
    "adamArchives/Adam/varMax/PADataset/_feature_cache_nvme/len16384/norm/ota__ota_core_high_run01__high_run01");

run_cachebuild(PY, py_script, data_root, cache_root_core, ...
    "ota_core_high_run01", "ota_core_high_run01", "high_run01");

% --- Cache 2: OTA PA1 ---
cache_root_pa1 = fullfile(getenv("HOME"), ...
    "adamArchives/Adam/varMax/PADataset/_feature_cache_nvme/len16384/norm/ota__ota_pa1_run01__pa1_run01");

run_cachebuild(PY, py_script, data_root, cache_root_pa1, ...
    "ota_pa1_run01", "ota_pa1_run01", "pa1_run01");

fprintf("POST | cacheBuild | DONE (core + pa1)\n");

% -------- local helper (MATLAB supports local funcs in scripts) --------
function run_cachebuild(PY, py_script, data_root, cache_root, source_name, dataset_tag, noise_tag)
    % Quote everything so spaces/odd chars can't break the shell invocation
    cmd = sprintf('%s "%s" --data-root "%s" --cache-root "%s" --cache-len 16384 --normalize --source-type ota --source-name %s --dataset-tag %s --noise-tag %s', ...
        PY, py_script, data_root, cache_root, source_name, dataset_tag, noise_tag);

    fprintf("POST | cacheBuild | %s\n", cmd);
    [rc, out] = system(cmd);
    fprintf("%s\n", out);

    if rc ~= 0
        error("cacheBuild.py failed (source_name=%s) rc=%d", source_name, rc);
    end
end