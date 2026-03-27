function [y, phi_out] = pa_mix_freq_offset_block(x, Fs, df_hz, phi_in)
%PA_MIX_FREQ_OFFSET_BLOCK Apply y[n]=x[n]*exp(j*(phi_in + 2pi*df*n/Fs)), return phi_out (phase continuity).
    if nargin < 4, phi_in = 0; end
    x = x(:);
    n = single(0:numel(x)-1).';
    dphi = single(2*pi) * single(df_hz) / single(Fs);
    ph = single(phi_in) + dphi * n;
    y = x .* complex(cos(ph), sin(ph));
    phi_out = double(phi_in) + double(dphi) * double(numel(x));  % unwrapped
    % Keep phase bounded (optional; deterministic either way)
    phi_out = mod(phi_out, 2*pi);
end