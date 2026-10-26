# ==============================================================================
# DERA — Database Engineering & Reverse Analysis
# Enterprise Monorepo Makefile
# ==============================================================================

.DEFAULT_GOAL := help
PYTHON := python
NPM := npm

.PHONY: help
help: ## Display available commands
	@echo "DERA Monorepo Engineering Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install Python and Node.js dependencies
	$(PYTHON) -m pip install -e ".[dev]"
	$(NPM) install

.PHONY: lint
lint: ## Run Python and TypeScript linter checks
	$(PYTHON) -m ruff check packages/ apps/ tests/
	$(PYTHON) scripts/ci/validate_docs.py
	$(PYTHON) scripts/ci/validate_i18n.py

.PHONY: format
format: ## Format code with Ruff and Prettier
	$(PYTHON) -m ruff format packages/ apps/ tests/

.PHONY: typecheck
typecheck: ## Execute TypeScript compiler check without emitting files
	npx tsc --noEmit

.PHONY: test
test: ## Run unit, integration, and architecture test suites
	$(PYTHON) -m unittest discover tests/

.PHONY: build
build: ## Compile Python packages and build TypeScript workspaces
	$(PYTHON) -m compileall packages/ apps/ tests/
	$(NPM) run build

.PHONY: dev-api
dev-api: ## Run local FastAPI development server
	$(PYTHON) -m uvicorn dera_api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: clean
clean: ## Remove temporary build files, test caches, and compiled artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf dist/ build/ *.egg-info .next/ out/
