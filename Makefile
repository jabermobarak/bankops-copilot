.PHONY: run test lint evaluate
run:
	python scripts/run.py
test:
	python -m pytest -q
lint:
	ruff check .
	ruff format --check .
evaluate:
	python scripts/evaluate.py
