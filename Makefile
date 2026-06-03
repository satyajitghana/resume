# Resume v3 — build the display, ATS, and one-page PDFs (named, in repo root).
#
#   make            build all three PDFs into the repo root
#   make display    satyajit-resume.pdf           (kestrel watermark — for humans/portfolio)
#   make ats        satyajit-resume-ats.pdf       (no background — submit this to ATS/portals)
#   make onepager   satyajit-resume-one-pager.pdf + -one-pager-ats.pdf (condensed, single page)
#   make image      regenerate the dithered kestrel watermark (uv + scripts/dither.py)
#   make preview    render preview PNGs into preview/ (used by the README)
#   make check      run the local open-source ATS checker on the ATS PDF
#   make clean      remove build/ aux files

TECTONIC ?= tectonic
SRC      := src
OUT      := build
MODEL_URL := https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

.PHONY: all display ats onepager image preview check clean

all: display ats onepager

display: $(SRC)/assets/kestrel-dither.png
	cd $(SRC) && $(TECTONIC) resume.tex --outdir ../$(OUT)
	cp $(OUT)/resume.pdf satyajit-resume.pdf

ats:
	cd $(SRC) && $(TECTONIC) resume-ats.tex --outdir ../$(OUT)
	cp $(OUT)/resume-ats.pdf satyajit-resume-ats.pdf

onepager: $(SRC)/assets/kestrel-dither.png
	cd $(SRC) && $(TECTONIC) resume-onepager.tex --outdir ../$(OUT)
	cp $(OUT)/resume-onepager.pdf satyajit-resume-one-pager.pdf
	cd $(SRC) && $(TECTONIC) resume-onepager-ats.tex --outdir ../$(OUT)
	cp $(OUT)/resume-onepager-ats.pdf satyajit-resume-one-pager-ats.pdf

image:
	cd scripts && uv run dither.py

$(SRC)/assets/kestrel-dither.png:
	cd scripts && uv run dither.py

preview: display
	pdftoppm -png -r 150 satyajit-resume.pdf preview/resume
	mv -f preview/resume-1.png preview/resume-page1.png
	mv -f preview/resume-2.png preview/resume-page2.png

check: ats
	uv run --no-project \
	  --with pdfminer.six --with pymupdf --with spacy \
	  --with "en_core_web_sm @ $(MODEL_URL)" \
	  python scripts/ats_check.py satyajit-resume-ats.pdf

clean:
	rm -rf $(OUT)/*.aux $(OUT)/*.log $(OUT)/*.out $(OUT)/*.synctex.gz
