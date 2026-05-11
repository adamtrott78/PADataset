function mc = pa_mask_close(m, kernel_samps)
    k = max(1, kernel_samps);
    % dilation then erosion
    d = movmax(single(m), k) > 0;
    mc = movmin(single(d), k) > 0;
end