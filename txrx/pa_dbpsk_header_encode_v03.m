function hdr = pa_dbpsk_header_encode_v03(pa_id, window_id, seq, sps, amp)
% 64-bit header: [pa_id(4) | window_id(16) | seq(16) | reserved(12) | crc16(16)]
% DBPSK with 1 reference symbol (+1), then 64 data symbols.

    pa_id = uint8(pa_id);
    window_id = uint16(window_id);
    seq = uint16(seq);

    bits = zeros(64,1,'uint8');

    bits(1:4)   = u2bits(pa_id, 4);
    bits(5:20)  = u2bits(window_id, 16);
    bits(21:36) = u2bits(seq, 16);
    bits(37:48) = zeros(12,1,'uint8'); % reserved

    crc = pa_crc16_ccitt_v03(bits(1:48));
    bits(49:64) = u2bits(crc, 16);

    % DBPSK symbols: ref + Nbits
    N = numel(bits);
    syms = complex(zeros(N+1,1), 0);

    ph = 0;
    syms(1) = 1; % reference
    for k = 1:N
        if bits(k) == 1
            ph = ph + pi;
        end
        syms(k+1) = exp(1j*ph);
    end

    % oversample
    hdr = amp * complex(repelem(single(real(syms)), sps), repelem(single(imag(syms)), sps));
end

function b = u2bits(u, n)
% MSB-first
    u = uint32(u);
    b = zeros(n,1,'uint8');
    for i = 1:n
        sh = n-i;
        b(i) = uint8(bitand(bitshift(u,-sh),1));
    end
end