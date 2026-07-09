#!/usr/bin/env bash
# Compila o manuscrito (elsarticle + bibtex). Uso: bash paper/build.sh
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
bibtex main >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
echo "OK -> $(pwd)/main.pdf"
