function [x_pkt, info] = zb_gen_packet(payload_seed32, zbCfg)
%ZB_GEN_PACKET Deterministic single Zigbee O-QPSK packet waveform (STRICT).

    rs = RandStream("mt19937ar", "Seed", double(payload_seed32));

    nbits = 8 * zbCfg.PSDULength;
    psdu  = randi(rs, [0 1], nbits, 1);   % numeric 0/1 column

    try
        x = lrwpanWaveformGenerator(psdu, zbCfg);
    catch ME
        error([ ...
            "Zigbee packet generation failed via lrwpanWaveformGenerator(psdu, zbCfg). " + ...
            "Check Communications Toolbox support and cfg fields. Original error:\n%s" ...
        ], ME.message);
    end

    x_pkt = complex(single(real(x)), single(imag(x)));
    x_pkt = x_pkt(:);

    info = struct( ...
        "nbits", nbits, ...
        "psdu_bytes", zbCfg.PSDULength, ...
        "sample_rate_hz", double(zbCfg.SampleRate), ...
        "nsamp", numel(x_pkt) ...
    );
end