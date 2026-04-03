function inspect_ota_sync_leak_v02()
    wifi_root = fileparts(mfilename("fullpath"));
    data_ota  = fullfile(wifi_root,"pilot_out_v01","data_ota");
    PAs = ["PA2","PA3","PA4","PA8"];
    
    syncLen = 20000; syncAmp = 0.35;
    sync = make_sync_bpsk(syncLen, syncAmp);
    
    gate_ratio = 25;
    gate_ms    = 2.0;  % only count "leak" if peak is within first/last 2 ms
    
    for pa = PAs
        f = fullfile(data_ota, sprintf("ota_rx_S01_%s.mat", pa));
        S = load(f,"Xrx_all","meta_rx");
        X = S.Xrx_all; M = S.meta_rx;
        Fs = double(M(1).fs_hz);
    
        N = size(X,2);
        hit = 0;
    
        for i = 1:N
            x = X(:,i); x = x(:) - mean(x); x = x / (rms(x)+1e-12);
    
            c = abs(conv(x, conj(flipud(sync)), "valid"));
            [pk, k] = max(c);
            med = median(c)+1e-12;
            ratio = pk/med;
    
            k_ms = (k-1)/Fs*1e3;
            W_ms = numel(x)/Fs*1e3;
    
            is_edge = (k_ms <= gate_ms) || (k_ms >= (W_ms - gate_ms));
    
            if ratio > gate_ratio && is_edge
                hit = hit + 1;
                fprintf("SYNC-EDGE %s i=%d wid=%d ratio=%.1f k=%.2f ms\n", ...
                    pa, i, double(M(i).window_id), ratio, k_ms);
            end
        end
    
        fprintf("%s: %d/%d windows show STRONG sync near edges\n\n", pa, hit, N);
    end
end

% ---------- helpers ----------
function [k0, ratio] = find_sync_pos_local(x, sync)
c = abs(conv(x, conj(flipud(sync)), "valid"));
pk = max(c);
med = median(c) + 1e-12;
ratio = pk / med;
if ~isfinite(ratio) || ratio < 1
    k0 = [];
    return;
end
[~,k0] = max(c); % 1-based start index in x
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