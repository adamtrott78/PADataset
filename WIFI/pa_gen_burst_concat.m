function [x_burst, burst_meta] = pa_gen_burst_concat(payload_seed32, scrambler_inits, wlanCfg, num_packets, idle_time_s, fs)
%PA_GEN_BURST_CONCAT Generate multi-packet burst by concatenating packets + idle gaps (signal-only).
% Gaps are zeros here; noise is added later per pipeline.

    assert(numel(scrambler_inits) == num_packets, "scrambler_inits must have length num_packets");

    gap = zeros(round(idle_time_s * fs), 1, "single");
    x_cells = cell(1, num_packets);
    pkt_info = cell(1, num_packets);

    for k = 1:num_packets
        [xk, ik] = pa_gen_packet(uint32(payload_seed32 + uint32(k-1)), scrambler_inits(k), wlanCfg);
        x_cells{k} = xk;
        pkt_info{k} = ik;
    end

    % Concatenate with idle gaps between packets
    x_burst = x_cells{1};
    for k = 2:num_packets
        x_burst = [x_burst; complex(gap, zeros(size(gap),"single")); x_cells{k}]; %#ok<AGROW>
    end

    burst_meta = struct("num_packets", num_packets, "idle_time_s", idle_time_s, "pkt_info", {pkt_info}, "nsamp", numel(x_burst));
end