% core/pa_paths.m
function P = pa_paths()
    root = pa_root();

    P.root = root;

    P.config = fullfile(root, 'config');

    P.data_root = fullfile(root, 'data');
    P.data_wifi = fullfile(P.data_root, 'wifi');
    P.data_wifi_digital = fullfile(P.data_wifi, 'digital');
    P.data_wifi_pilot = fullfile(P.data_wifi_digital, 'pilot');
    P.data_wifi_ota = fullfile(P.data_wifi, 'ota');
    P.data_wifi_spliced = fullfile(P.data_wifi_ota, 'spliced');
    P.data_wifi_spliced_v03 = fullfile(P.data_wifi_spliced, 'v03');
    P.data_wifi_spliced_v05 = fullfile(P.data_wifi_spliced, 'v05');

    P.txrx = fullfile(root, 'txrx');
    P.txrx_tapes = fullfile(P.txrx, 'tapes');
    P.txrx_tapes_digital = fullfile(P.txrx_tapes, 'digital');
    P.txrx_tapes_ota = fullfile(P.txrx_tapes, 'ota');

    P.results = fullfile(root, 'results');
    P.results_wifi = fullfile(P.results, 'wifi');
    P.results_wifi_digital = fullfile(P.results_wifi, 'digital');
    P.results_wifi_ota = fullfile(P.results_wifi, 'ota');
    P.results_rx_resplice_v03 = fullfile(P.results_wifi_ota, 'rx_resplice_tape_v03');
    P.results_rx_resplice_v05 = fullfile(P.results_wifi_ota, 'rx_resplice_tape_v05');
    P.results_tape_inspect = fullfile(P.results_wifi_ota, 'tape_inspect');
    P.protocol = fullfile(root, 'protocol');
    P.protocol_wifi = fullfile(P.protocol, 'wifi');
    P.tools = fullfile(root, 'tools');

    P.data_wifi_digital_as_tx12p5 = fullfile(P.data_wifi_digital, 'as_tx12p5');

    P.results_wifi_digital_eval_pilot = fullfile(P.results_wifi_digital, 'eval_pilot_v01');
    P.results_wifi_digital_eval_pilot_evidence = fullfile(P.results_wifi_digital_eval_pilot, 'evidence_pack');
    P.results_wifi_digital_run_pilot = fullfile(P.results_wifi_digital, 'run_pilot_v01');
    P.results_wifi_digital_run_pilot_viz = fullfile(P.results_wifi_digital_run_pilot, 'viz');
    P.results_wifi_digital_make_pa_slide = fullfile(P.results_wifi_digital, 'make_pa_slide_png_pipeline_v01');
    P.results_wifi_ota_eval_quick = fullfile(P.results_wifi_ota, 'eval_ota_quick_v01');
    P.results_wifi_ota_eval_quick_png = fullfile(P.results_wifi_ota_eval_quick, 'png');
    P.results_rx_resplice_v03_png_pairs = fullfile(P.results_rx_resplice_v03, 'png_pairs');
    P.results_rx_resplice_v05_png = fullfile(P.results_rx_resplice_v05, 'png');
    P.results_rx_resplice_v05_png_pairs = fullfile(P.results_rx_resplice_v05, 'png_pairs');
end