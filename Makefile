.PHONY: venv run all paper clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

venv:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt
	$(PYTHON) -m spacy download en_core_web_sm

# Single book, for validation. Usage: make run BOOK=1342
run:
	$(PYTHON) -m src.pipeline --only $(BOOK)

all:
	$(PYTHON) -m src.pipeline --all

paper:
	cd paper && ../$(PYTHON) make_paper_assets.py && bash build.sh

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} +
	rm -rf data/booknlp
	rm -f paper/*.aux paper/*.bbl paper/*.blg paper/*.log paper/*.out paper/*.spl
