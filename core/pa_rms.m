function r = pa_rms(x)
    r = sqrt(mean(abs(double(x)).^2));
end