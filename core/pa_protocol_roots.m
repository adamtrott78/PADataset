function R = pa_protocol_roots(protocol)
%PA_PROTOCOL_ROOTS Return standard data/results/tape roots for one protocol.
%
% R = pa_protocol_roots("wifi")
% R = pa_protocol_roots("bluetooth")
% R = pa_protocol_roots("zigbee")

    protocol = string(protocol);
    assert(any(protocol == ["wifi","bluetooth","zigbee"]), ...
        "protocol must be one of: wifi, bluetooth, zigbee");

    root = pa_root();

    R = struct();
    R.root = root;
    R.protocol = char(protocol);

    R.data_protocol = fullfile(root, 'data', char(protocol));
    R.data_digital = fullfile(R.data_protocol, 'digital');
    R.data_pilot = fullfile(R.data_digital, 'pilot');
    R.data_pilot_shards = fullfile(R.data_digital, 'pilot_shards');
    R.data_ota = fullfile(R.data_protocol, 'ota');
    R.data_ota_spliced = fullfile(R.data_ota, 'spliced');
    R.data_ota_spliced_v05 = fullfile(R.data_ota_spliced, 'v05');

    R.results_protocol = fullfile(root, 'results', char(protocol));
    R.results_digital = fullfile(R.results_protocol, 'digital');
    R.results_ota = fullfile(R.results_protocol, 'ota');

    R.txrx = fullfile(root, 'txrx');
    R.txrx_tapes = fullfile(R.txrx, 'tapes');
    R.txrx_tapes_digital = fullfile(R.txrx_tapes, 'digital', char(protocol));
    R.txrx_tapes_ota = fullfile(R.txrx_tapes, 'ota', char(protocol));
end
