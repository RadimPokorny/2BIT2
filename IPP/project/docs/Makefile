# Makefile for LaTeX documentation

# Default target
all: dokumentace.pdf

# Compile LaTeX to PDF
dokumentace.pdf: dokumentace.tex
	pdflatex dokumentace.tex
	pdflatex dokumentace.tex  # Run twice for references

# Clean temporary files
clean:
	rm -f dokumentace.aux dokumentace.log dokumentace.out dokumentace.toc dokumentace.pdf

.PHONY: all clean