function [pa_id, window_id, seq, ok] = pa_dbpsk_header_decode_v03(hdr_samp, sps)
% Inverse of encode: integrate-and-dump symbols, DBPSK demod, CRC check.

    hdr_samp = hdr_samp(:);
    Ns = floor(numel(hdr_samp)/sps);
    hdr_samp = hdr_samp(1:Ns*sps);

    % integrate symbols
    sym = zeros(Ns,1);
    for k = 1:Ns
        a = (k-1)*sps + 1;
        b = a + sps - 1;
        sym(k) = mean(hdr_samp(a:b));
    end

    % expect Ns = 65 = ref + 64
    if Ns < 65
        pa_id = uint8(0); window_id = uint16(0); seq = uint16(0); ok = false; return;
    end
    sym = sym(1:65);

    bits = zeros(64,1,'uint8');
    for k = 2:65
        d = conj(sym(k-1)) * sym(k);
        bits(k-1) = uint8(real(d) < 0); % pi flip -> negative
    end

    pa_id = bits2u(bits(1:4));
    window_id = uint16(bits2u(bits(5:20)));
    seq = uint16(bits2u(bits(21:36)));

    crc_rx = uint16(bits2u(bits(49:64)));
    crc_ok = (pa_crc16_ccitt_v03(bits(1:48)) == crc_rx);

    ok = crc_ok;
end

function u = bits2u(b)
    b = uint8(b(:));
    u = uint32(0);
    for i = 1:numel(b)
        u = bitshift(u,1) + uint32(b(i));
    end
end