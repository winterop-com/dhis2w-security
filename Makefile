.DEFAULT_GOAL := help

.PHONY: help install lint test coverage build clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Sync the development environment
	uv sync --all-groups

lint:  ## Run ruff, mypy and pyright
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests
	uv run pyright src

test:  ## Run the test suite
	BROWSER=true uv run pytest -q

coverage:  ## Run the test suite with coverage
	BROWSER=true uv run pytest --cov=dhis2w_security --cov-report=term-missing

build:  ## Build the wheel and the source distribution
	uv build

clean:  ## Remove build output and tool caches
	rm -rf dist build .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
