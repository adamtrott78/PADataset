function rx_usrp_power_troubleshoot_v01(ip, fc_hz, gain_db, rx_ant)
%RX_USRP_POWER_TROUBLESHOOT_V01 Receive and print live power stats.
% Usage:
%   rx_usrp_power_troubleshoot_v01("192.168.10.2", 2.437e9, 10, "TX/RX");

Fs = 20e6;
mcr = 100e6;
decim = round(mcr/Fs);

frameLen = 100000;

rx = comm.SDRuReceiver( ...
    "Platform","N200/N210/USRP2", ...
    "IPAddress", ip, ...
    "CenterFrequency", fc_hz, ...
    "Gain", gain_db, ...
    "MasterClockRate", mcr, ...
    "DecimationFactor", decim, ...
    "SamplesPerFrame", frameLen, ...
    "OutputDataType","single", ...
    "ChannelMapping", 1);

% Explicit antenna if supported
if nargin >= 4 && ~isempty(rx_ant) && isprop(rx,"Antenna")
    rx.Antenna = rx_ant;
end

fprintf("RX POWER | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | Fs=%.3f MS/s | frameLen=%d\n", ...
    ip, fc_hz/1e9, gain_db, Fs/1e6, frameLen);

overruns = 0;
frames = 0;

t0 = tic;
p_acc = 0; pk_acc = 0;

try
    while true
        [y, len, ov] = rx();
        if ov, overruns = overruns + 1; end
        if len <= 0, continue; end
        y = y(1:len);

        frames = frames + 1;
        p = mean(abs(double(y)).^2);
        pk = max(abs(y));

        p_acc  = p_acc + p;
        pk_acc = max(pk_acc, pk);

        if toc(t0) >= 1.0
            fprintf("  frames=%d | overruns=%d | meanP=%.3e | pk=%.3f\n", ...
                frames, overruns, p_acc/max(1,frames), pk_acc);
            t0 = tic;
            frames = 0; p_acc = 0; pk_acc = 0;
        end
    end
catch ME
    release(rx);
    rethrow(ME);
end
end