# Resume v3 — build the dithered-kestrel display PDF and the clean ATS PDF.
#
#   make            build both PDFs into build/
#   make display    build/resume.pdf      (with kestrel watermark — for humans/portfolio)
#   make ats        build/resume-ats.pdf  (no background — submit this to ATS/job portals)
#   make image      regenerate the dithered kestrel watermark (uv + scripts/dither.py)
#   make preview    render preview PNGs into preview/ (used by the README)
#   make check      run the local open-source ATS checker on build/resume-ats.pdf
#   make clean

TECTONIC ?= tectonic
SRC      := src
OUT      := build
MODEL_URL := https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

.PHONY: all display ats image preview check clean

all: display ats

display: $(SRC)/assets/kestrel-dither.png
	cd $(SRC) && $(TECTONIC) resume.tex --outdir ../$(OUT)

ats:
	cd $(SRC) && $(TECTONIC) resume-ats.tex --outdir ../$(OUT)

image:
	cd scripts && uv run dither.py

$(SRC)/assets/kestrel-dither.png:
	cd scripts && uv run dither.py

preview: display
	pdftoppm -png -r 150 $(OUT)/resume.pdf preview/resume
	mv -f preview/resume-1.png preview/resume-page1.png
	mv -f preview/resume-2.png preview/resume-page2.png

check: ats
	uv run --no-project \
	  --with pdfminer.six --with pymupdf --with spacy \
	  --with "en_core_web_sm @ $(MODEL_URL)" \
	  python scripts/ats_check.py $(OUT)/resume-ats.pdf

clean:
	rm -rf $(OUT)/*.pdf $(OUT)/*.aux $(OUT)/*.log $(OUT)/*.out
