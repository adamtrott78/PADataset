function crc = pa_crc16_ccitt_v03(bits)
% CRC-16-CCITT (poly 0x1021), init 0xFFFF, MSB-first.

    poly = uint16(hex2dec("1021"));
    reg  = uint16(hex2dec("FFFF"));

    bits = uint8(bits(:));
    for i = 1:numel(bits)
        b = bits(i);
        reg = bitxor(reg, bitshift(uint16(b),15));
        for k = 1:1
            if bitand(reg, uint16(32768)) ~= 0
                reg = bitxor(bitshift(reg,1), poly);
            else
                reg = bitshift(reg,1);
            end
        end
    end
    crc = reg;
end
