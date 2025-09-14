.PHONY: help install-dev test test-all qa lint fmt cov cov-combine clean list-envs

help:
	@echo "Targets:"
	@echo "  install-dev     Install dev dependencies (editable + [dev])"
	@echo "  test            Run pytest quickly (current env)"
	@echo "  test-all        Run full tox matrix"
	@echo "  qa              Run linters via tox (qa env)"
	@echo "  lint            Run flake8/black/isort/ruff checks"
	@echo "  fmt             Auto-format with black, isort, ruff"
	@echo "  cov             Run pytest with coverage (current env)"
	@echo "  cov-combine     Combine per-env coverage into XML/HTML"
	@echo "  clean           Remove caches, build and coverage artifacts"
	@echo "  list-envs       List tox environments"

install-dev:
	python -m pip install -U pip setuptools wheel
	pip install -e .[dev]
	pre-commit install || true

test:
	pytest -q

test-all:
	tox -q

qa:
	tox -q -e qa

lint:
	flake8 vectordb
	black --check vectordb
	isort --check-only --diff vectordb
	ruff check vectordb

fmt:
	black vectordb
	isort vectordb
	ruff check --fix vectordb

cov:
	pytest --cov=vectordb --cov-report=term-missing --cov-report=xml --cov-report=html

cov-combine:
	python -m pip install coverage >/dev/null 2>&1 || true
	coverage combine
	coverage xml -o coverage.xml
	coverage html -d htmlcov

clean:
	rm -rf .pytest_cache .ruff_cache .tox build dist site \
	       htmlcov htmlcov-* coverage.xml .coverage .coverage.* \
	       vectordb/__pycache__ vectordb/**/*.pyc

list-envs:
	tox -av

