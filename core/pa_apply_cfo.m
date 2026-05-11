function y = pa_apply_cfo(x, Fs, f_cfo_hz)
    n = single(0:numel(x)-1).';
    ph = single(2*pi) * single(f_cfo_hz) * n / single(Fs);
    y = x .* complex(cos(ph), sin(ph));
end