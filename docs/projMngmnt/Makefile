# Makefile
# From https://danielkaes.wordpress.com/2009/03/14/compiling-latex-documents-using-makefiles/

TEX=latexmk -pdf

all: poc rev0 final

poc:
	$(TEX) POC_Team_Contrib.tex

rev0:
	$(TEX) Rev0_Team_Contrib.tex

final:
	$(TEX) Final_Team_Contrib.tex

clean-all:
	rm -f *.dvi *.log *.bak *.aux *.bbl *.blg *.idx *.ps *.eps *.pdf *.toc *.synctex.gz *.out *~

clean:
	rm -f *.log *.bak *.aux *.bbl *.blg *.idx *.toc *.synctex.gz *.out *~