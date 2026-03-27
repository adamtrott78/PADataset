function resplice_ota_from_sync_v01()
%RESP LICE_OTA_FROM_SYNC_V01
% Repairs OTA payload windows when sync leaks into payload.
% Strategy:
%  - Build a long stream Z by concatenating saved payload windows.
%  - Detect sync position inside each saved payload window i.
%  - If found, treat it as the sync that precedes window (i+1).
%  - Rebuild window (i+1) as: Z(sync_start + frameLen : + frameLen + W - 1).
%
% Output:
%  WIFI/pilot_out_v01/data_ota_resplice/ota_rx_S01_<PA>_resplice.mat
%    Xrx_all_fix, meta_rx_fix, resplice_info

wifi_root = fileparts(mfilename("fullpath"));
in_dir  = fullfile(wifi_root,"pilot_out_v01","data_ota");
out_dir = fullfile(wifi_root,"pilot_out_v01","data_ota_resplice");
if ~exist(out_dir,"dir"), mkdir(out_dir); end

PAs = ["PA2","PA3","PA4","PA8"];

% Must match TX/RX
W        = 400000;
frameLen = 100000;
syncLen  = 20000;
syncAmp  = 0.35;

ratio_thr = 25;      % same "spirit" as your gate
min_k_sep = 2000;    % just sanity, not critical

sync = make_sync_bpsk(syncLen, syncAmp);

for pa = PAs
    f = fullfile(in_dir, sprintf("ota_rx_S01_%s.mat", pa));
    assert(isfile(f), "Missing %s", f);
    S = load(f,"Xrx_all","meta_rx");
    X = S.Xrx_all;
    M = S.meta_rx;

    N = size(X,2);
    fprintf("\n[%s] loaded %d windows\n", pa, N);

    % Concatenate saved payload windows into one long stream
    Z = reshape(X, [], 1);

    leak_pos   = zeros(N,1);
    leak_ratio = zeros(N,1);

    % 1) detect sync leaks per saved payload window
    for i = 1:N
        x = X(:,i);
        x = x(:) - mean(x);
        x = x / (rms(x) + 1e-12);

        [k0, rr] = find_sync_pos_local(x, sync);
        if ~isempty(k0) && rr > ratio_thr
            leak_pos(i)   = k0;
            leak_ratio(i) = rr;
        end
    end

    hit = nnz(leak_pos);
    fprintf("[%s] %d/%d windows have sync inside payload (ratio>%.1f)\n", pa, hit, N, ratio_thr);

    % 2) resplice: repair window (i+1) using sync found in window i
    Xfix = X;
    Mfix = M;

    repaired = false(N,1);
    src_i    = zeros(N,1);
    src_k    = zeros(N,1);
    src_rr   = zeros(N,1);

    for i = 1:(N-1)
        k0 = leak_pos(i);
        if k0 <= 0, continue; end

        s_global = int64((i-1)*W + k0);          % sync start in Z (1-based)
        start    = s_global + frameLen;          % payload start after syncFrame
        stop     = start + (W-1);

        if stop <= numel(Z)
            xnew = Z(start:stop);

            % Light sanity: ensure we didn't immediately re-hit sync at the front
            xt = xnew - mean(xnew);
            xt = xt / (rms(xt) + 1e-12);
            [kchk, rrchk] = find_sync_pos_local(xt, sync);
            if ~isempty(kchk) && kchk < min_k_sep && rrchk > ratio_thr
                % If sync is still right at the start, something is wrong with this repair
                continue;
            end

            Xfix(:,i+1) = xnew;
            repaired(i+1) = true;
            src_i(i+1)  = i;
            src_k(i+1)  = k0;
            src_rr(i+1) = leak_ratio(i);
        end
    end

    fprintf("[%s] repaired %d windows (most repairs are i>=2)\n", pa, nnz(repaired));

    resplice_info = struct();
    resplice_info.ratio_thr = ratio_thr;
    resplice_info.W = W;
    resplice_info.frameLen = frameLen;
    resplice_info.syncLen = syncLen;
    resplice_info.leak_pos = leak_pos;
    resplice_info.leak_ratio = leak_ratio;
    resplice_info.repaired = repaired;
    resplice_info.repair_source_window_i = src_i;
    resplice_info.repair_sync_pos_in_i = src_k;
    resplice_info.repair_sync_ratio_in_i = src_rr;

    out = fullfile(out_dir, sprintf("ota_rx_S01_%s_resplice.mat", pa));
    Xrx_all_fix = Xfix;
    meta_rx_fix = Mfix;
    save(out, "Xrx_all_fix","meta_rx_fix","resplice_info","-v7");
    fprintf("[%s] wrote %s\n", pa, out);
end

fprintf("\nDONE. Next: point eval_ota_quick_v01 to data_ota_resplice and load Xrx_all_fix.\n");
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