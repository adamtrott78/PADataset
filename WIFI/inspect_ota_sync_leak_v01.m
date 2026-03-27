function inspect_ota_sync_leak_v01()
% Checks whether the per-window sync appears INSIDE saved payload windows (bad).

wifi_root = fileparts(mfilename("fullpath"));
data_ota  = fullfile(wifi_root,"pilot_out_v01","data_ota_resplice");

PAs = ["PA2","PA3","PA4","PA8"];

% Must match TX/RX
syncLen = 20000;
syncAmp = 0.35;
sync = make_sync_bpsk(syncLen, syncAmp);

for pa = PAs
    f = fullfile(data_ota, sprintf("ota_rx_S01_%s_resplice.mat", pa));
    S = load(f,"Xrx_all_fix","meta_rx_fix");
    
    X = S.Xrx_all_fix;
    M = S.meta_rx_fix;
    
    N = size(X,2);
    hit = 0;

    for i = 1:N
        x = X(:,i);
        x = x(:) - mean(x);
        x = x / (rms(x) + 1e-12);

        % brute correlation (no decimation) against sync
        c = abs(conv(x, conj(flipud(sync)), "valid"));
        pk = max(c);
        med = median(c) + 1e-12;
        ratio = pk / med;

        if ratio > 25    % same spirit as your find_sync gate
            hit = hit + 1;
            fprintf("SYNC-LEAK %s i=%d wid=%d ratio=%.1f\n", pa, i, M(i).window_id, ratio);
        end
    end

    fprintf("%s: %d/%d windows show sync inside payload\n\n", pa, hit, N);
end
end

function sync = make_sync_bpsk(N, amp)
chips = lfsr_mseq_127();
bpsk  = single(2*chips - 1);
rep   = ceil(N/numel(bpsk));
v     = repmat(bpsk, rep, 1); v = v(1:N);
sync  = amp * complex(v, zeros(N,1,"single"));
end

function bits = lfsr_mseq_127()
state = ones(7,1,'logical');
bits  = false(127,1);
for k=1:127
    bits(k) = state(end);
    newb = xor(state(end), state(3));
    state = [newb; state(1:end-1)];
end
bits = single(bits);
end