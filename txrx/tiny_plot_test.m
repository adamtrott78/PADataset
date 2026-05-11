close all force
f = figure('Visible','off');
plot(1:100);
drawnow;
out_png = fullfile(tempdir, 'tiny_plot_test.png');
exportgraphics(f, out_png, 'Resolution', 150);
disp(out_png)
close(f)
exit