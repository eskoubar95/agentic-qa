.PHONY: lint lint-fix format
lint:
	python -m ruff check .
format:
	python -m ruff format .
lint-fix: format
	python -m ruff check . --fix
