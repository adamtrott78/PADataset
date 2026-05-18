MAIN=main
OUT=build

.PHONY: all watch clean distclean

all:
	mkdir -p $(OUT)
	latexmk -pdf -interaction=nonstopmode -file-line-error -synctex=1 -outdir=$(OUT) $(MAIN).tex

watch:
	mkdir -p $(OUT)
	latexmk -pdf -pvc -view=none -view=none -view=none -interaction=nonstopmode -file-line-error -synctex=1 -outdir=$(OUT) $(MAIN).tex

clean:
	latexmk -C -outdir=$(OUT) $(MAIN).tex || true

distclean: clean
	rm -rf $(OUT)
