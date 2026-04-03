function tx_usrp_tone_troubleshoot_v01(ip, fc_hz, gain_db, tx_ant)
%TX_USRP_TONE_TROUBLESHOOT_V01 Send a clean complex tone continuously.
% Usage:
%   tx_usrp_tone_troubleshoot_v01("192.168.10.2", 2.437e9, 20, "TX/RX");

Fs = 20e6;
mcr = 100e6;
interp = round(mcr/Fs);

frameLen = 100000;              % 5 ms frames => low call rate
f0 = 200e3;                     % 200 kHz baseband tone
amp = 0.35;                     % headroom

n = single((0:frameLen-1).');
tone = amp * complex(cos(2*pi*(f0/Fs)*double(n)), sin(2*pi*(f0/Fs)*double(n)));

tx = comm.SDRuTransmitter( ...
    "Platform","N200/N210/USRP2", ...
    "IPAddress", ip, ...
    "CenterFrequency", fc_hz, ...
    "Gain", gain_db, ...
    "MasterClockRate", mcr, ...
    "InterpolationFactor", interp, ...
    "ChannelMapping", 1);

% Explicit antenna if supported
if nargin >= 4 && ~isempty(tx_ant) && isprop(tx,"Antenna")
    tx.Antenna = tx_ant;
end

fprintf("TX TONE | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | Fs=%.3f MS/s | frameLen=%d\n", ...
    ip, fc_hz/1e9, gain_db, Fs/1e6, frameLen);

underruns = 0;
t0 = tic;
k = 0;

try
    while true
        u = tx(tone);          % returns underrun flag (0/1) on most versions
        underruns = underruns + double(u);
        k = k + 1;

        if toc(t0) >= 1.0
            pk = max(abs(tone));
            pw = mean(abs(double(tone)).^2);
            fprintf("  frames=%d | underruns=%d | pk=%.3f | meanP=%.3e\n", k, underruns, pk, pw);
            t0 = tic;
        end
    end
catch ME
    release(tx);
    rethrow(ME);
end
end