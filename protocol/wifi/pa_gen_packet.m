function [x_pkt, info] = pa_gen_packet(payload_seed32, scrambler_init, wlanCfg)
%PA_GEN_PACKET Deterministic single NonHT packet waveform (STRICT).
% Uses exactly ONE scrambler-control mechanism:
%   wlanWaveformGenerator(..., "ScramblerInitialization", scr)
% If unsupported by your WLAN Toolbox, this function errors (by design).

    rs = RandStream("mt19937ar", "Seed", double(payload_seed32));
    nbits = 8 * wlanCfg.PSDULength;
    psdu  = randi(rs, [0 1], nbits, 1);     % numeric 0/1 column

    scr = double(scrambler_init);           % must be 1..127
    if ~(scr >= 1 && scr <= 127 && isfinite(scr))
        error("scrambler_init must be in [1..127], got %g", scr);
    end

    % STRICT: one method only
    try
        x = wlanWaveformGenerator(psdu, wlanCfg, "ScramblerInitialization", scr);
    catch ME
        error([ ...
            "Your WLAN Toolbox does not support setting scrambler init via " + ...
            "wlanWaveformGenerator(...,'ScramblerInitialization',...). " + ...
            "For this project spec (per-packet scrambler control), you must upgrade " + ...
            "MATLAB/WLAN Toolbox to a version that supports it. Original error:\n%s" ...
        ], ME.message);
    end

    x_pkt = complex(single(real(x)), single(imag(x)));
    x_pkt = x_pkt(:);

    info = struct( "nbits", nbits, ...
        "psdu_bytes", wlanCfg.PSDULength, ...
        "scrambler_init", scr, ...
        "nsamp", numel(x_pkt) ...
    );
end