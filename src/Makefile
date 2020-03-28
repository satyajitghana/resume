RESUME_FILE = resume

all:
	-mkdir target
	xelatex -synctex=1 -interaction=nonstopmode -output-directory=target ${RESUME_FILE}.tex

clean:
	rm -r target/