function [seed64, seed32] = pa_sha_seed(master_seed, schema_version, session_id, tape_id, segment_id, window_id, suffix)
%PA_SHA_SEED Stable SHA-256 -> uint64 + uint32 seeds.
% Uses UTF-8 bytes for hashing (deterministic across platforms).
% suffix optional (e.g., "payload","scrambler","noise").

    if nargin < 7 || isempty(suffix), suffix = ""; end

    msg = sprintf("%s|%s|%s|%s|%s|%s|%s", ...
        num2str(uint64(master_seed)), string(schema_version), num2str(session_id), ...
        num2str(tape_id), num2str(segment_id), num2str(window_id), string(suffix));

    % Convert to UTF-8 bytes (MATLAB-safe)
    bytes = unicode2native(char(msg), "UTF-8");   % returns uint8 row vector

    md = java.security.MessageDigest.getInstance("SHA-256");
    md.update(bytes);
    dig = typecast(md.digest(), "uint8");         % 32 bytes

    % First 8 bytes interpreted as big-endian uint64
    seed64 = uint64(0);
    for i = 1:8
        seed64 = bitshift(seed64, 8) + uint64(dig(i));
    end

    seed32 = uint32(bitand(seed64, uint64(2^32-1)));
end