.PHONY: setup install run run-chat run-board update-kb clean lint format test test-coverage test-verbose web-setup web-dev web-build

# Create virtual environment and install dependencies
setup:
	uv venv
	uv pip install -e .

# Install dependencies only
install:
	uv pip install -r requirements.txt

# Install development dependencies
dev-install:
	uv pip install -e ".[dev]"

# Run the main server
run:
	python -m cool_squad.main

# Run the chat server only
run-chat-server:
	python -m cool_squad.main --chat-only

# Run the board server only
run-board-server:
	python -m cool_squad.main --board-only

# Run the chat client
run-chat:
	python -m cool_squad.client \#welcome alice

# Run the board client
run-board:
	python -m cool_squad.board_client general alice

# Update the knowledge base
update-kb:
	python -m cool_squad.main --update-knowledge

# Format code with black
format:
	black cool_squad tests

# Sort imports with isort
sort-imports:
	isort cool_squad tests

# Run all formatting
lint: format sort-imports

# Run tests
test:
	pytest tests

# Run tests with coverage report
test-coverage:
	pytest --cov=cool_squad tests/ --cov-report=term-missing

# Run tests with verbose output
test-verbose:
	pytest -v tests/

# Web frontend commands
web-setup:
	cd web && bun install

web-dev:
	cd web && bun run dev

web-build:
	cd web && bun run build

# Clean up generated files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf web/build
	rm -rf web/.svelte-kit
	rm -rf web/node_modules

# Show help
help:
	@echo "Available commands:"
	@echo "  make setup          - Create virtual environment and install dependencies"
	@echo "  make install        - Install dependencies only"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make run            - Run the main server"
	@echo "  make run-chat-server - Run the chat server only"
	@echo "  make run-board-server - Run the board server only"
	@echo "  make run-chat       - Run the chat client"
	@echo "  make run-board      - Run the board client"
	@echo "  make update-kb      - Update the knowledge base"
	@echo "  make web-setup      - Install web frontend dependencies"
	@echo "  make web-dev        - Run web frontend development server"
	@echo "  make web-build      - Build web frontend for production"
	@echo "  make format         - Format code with black"
	@echo "  make sort-imports   - Sort imports with isort"
	@echo "  make lint           - Run all formatting"
	@echo "  make test           - Run tests"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make test-verbose   - Run tests with verbose output"
	@echo "  make clean          - Clean up generated files" 