.PHONY: setup test example full plots report validate clean

PYTHON ?= python
VENV ?= .venv

setup:
	$(PYTHON) -m venv $(VENV)
	./$(VENV)/bin/pip install --upgrade pip
	./$(VENV)/bin/pip install -r requirements.txt pytest

test:
	env -u PYTHONPATH pytest -q

example:
	bash scripts/run_example.sh

full:
	bash scripts/run_full.sh

plots:
	MPLBACKEND=Agg $(PYTHON) scripts/plot_results.py

report:
	$(PYTHON) scripts/generate_report.py

validate:
	MPLBACKEND=Agg $(PYTHON) scripts/loo_validation.py

clean:
	rm -rf .pytest_cache __pycache__ scripts/__pycache__ tests/__pycache__
	rm -rf data/processed/*.csv results/*.csv results/*.json figures/*.png
	rm -f reports/*.md
