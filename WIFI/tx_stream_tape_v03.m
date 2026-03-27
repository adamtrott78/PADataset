function tx_stream_tape_v03(ip, fc_hz, gain_db, tx_ant)
%TX_STREAM_TAPE_V03 Beacon mode -> SPACE -> stream tx_tape_v03.
%
% Usage:
%   build_tx_tape_v03
%   tx_stream_tape_v03("192.168.10.2", 2.437e9, 20, "TX/RX")

    this = fileparts(mfilename("fullpath"));
    addpath(fullfile(this,"common"));

    tape_file = fullfile(this,"pilot_out_v01","tx_tape_v03","tx_tape_v03.mat");
    S = load(tape_file, "tx_tape", "tx_params", "sync");
    tx_tape = S.tx_tape;
    p = S.tx_params;
    sync = S.sync;

    mcr = 100e6;
    interp = round(mcr / 12e6); % user-friendly default, but we print actual
    Fs = mcr / interp;

    fprintf("TX_v03 | IP=%s | Fc=%.6f GHz | Gain=%.1f dB | MCR=%.0f | interp=%d | Fs=%.6f MS/s\n", ...
        ip, fc_hz/1e9, gain_db, mcr, interp, Fs/1e6);

    tx = comm.SDRuTransmitter( ...
        "Platform","N200/N210/USRP2", ...
        "IPAddress", ip, ...
        "CenterFrequency", fc_hz, ...
        "Gain", gain_db, ...
        "MasterClockRate", mcr, ...
        "InterpolationFactor", interp, ...
        "ChannelMapping", 1);

    if nargin >= 4 && ~isempty(tx_ant) && isprop(tx,"Antenna")
        tx.Antenna = tx_ant;
    end

    % beacon frame: beacon preamble in first Lpre samples, rest zeros
    beacon = complex(zeros(p.frameLen,1,"single"), zeros(p.frameLen,1,"single"));
    beacon(1:p.Lpre) = sync.beacon_preamble;

    % UI for SPACE press
    st = struct("go",false,"quit",false);
    fig = figure("Name","TX_v03","Color","w","KeyPressFcn",@onkey);
    uicontrol("Style","text","String","Beacon running. Press SPACE to start tape. Press Q to quit.", ...
        "Units","normalized","Position",[0.05 0.4 0.9 0.2],"FontSize",14,"BackgroundColor","w");

    underruns = 0;
    t0 = tic;
    n_beacon = 0;

    try
        % --------- BEACON MODE ---------
        while ~st.go && ~st.quit
            underruns = underruns + double(tx(beacon));
            n_beacon = n_beacon + 1;

            if toc(t0) > 1.0
                fprintf("BEACON | frames=%d | underruns=%d\n", n_beacon, underruns);
                t0 = tic;
            end
            drawnow limitrate; % allows keypress callback
        end

        if st.quit
            release(tx); close(fig);
            fprintf("TX quit.\n");
            return;
        end

        fprintf("TX: SPACE pressed -> streaming tx_tape (%d samples)\n", numel(tx_tape));

        % --------- STREAM TAPE ---------
        N = numel(tx_tape);
        frameLen = p.frameLen;
        assert(mod(N, frameLen)==0, "tx_tape must be multiple of frameLen");

        nFrames = N/frameLen;
        t1 = tic;
        for k = 1:nFrames
            a = (k-1)*frameLen + 1;
            b = a + frameLen - 1;
            underruns = underruns + double(tx(tx_tape(a:b)));

            if mod(k,100) == 0 || k == nFrames
                fprintf("TX | %d/%d frames | underruns=%d | elapsed=%.1fs\n", ...
                    k, nFrames, underruns, toc(t1));
            end
        end

        release(tx); close(fig);
        fprintf("TX DONE | underruns=%d\n", underruns);

    catch ME
        try, release(tx); end %#ok<TRYNC>
        try, close(fig); end %#ok<TRYNC>
        rethrow(ME);
    end

    function onkey(~, ev)
        if strcmp(ev.Key,"space"), st.go = true; end
        if strcmp(ev.Key,"q"),     st.quit = true; end
    end
end