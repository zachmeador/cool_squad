.PHONY: setup dev-install run dev stop update-kb run-cli test test-coverage test-verbose web-setup web-dev web-build help

#
# environment setup
#
setup:
	uv venv
	uv pip install -e .

dev-install:
	uv pip install -e ".[dev]"

#
# server commands
#
run:
	python -m cool_squad.main

dev:
	@echo "starting all servers in development mode..."
	@mkdir -p logs
	@python -m cool_squad.main > logs/server.log 2>&1 & echo $$! > .server.pid
	@cd web && bun run dev > ../logs/web.log 2>&1 & echo $$! > ../.web.pid
	@echo "servers started! check logs/ directory for output"
	@echo "use 'make stop' to shut down all servers"

stop:
	@echo "stopping all servers..."
	@if [ -f .server.pid ]; then kill $$(cat .server.pid) 2>/dev/null || true; rm .server.pid; fi
	@if [ -f .web.pid ]; then kill $$(cat .web.pid) 2>/dev/null || true; rm .web.pid; fi
	@echo "all servers stopped"

#
# client commands
#
run-cli:
	python cli.py

#
# knowledge base
#
update-kb:
	python -m cool_squad.main --update-knowledge

#
# web frontend
#
web-setup:
	cd web && bun install

web-dev:
	cd web && bun run dev

web-build:
	cd web && bun run build

#
# development tools
#
format:
	black cool_squad tests

sort-imports:
	isort cool_squad tests

lint: format sort-imports

#
# testing
#
test:
	pytest tests

test-coverage:
	pytest --cov=cool_squad tests/ --cov-report=term-missing

test-verbose:
	pytest -v tests/

#
# cleanup
#
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf web/build web/.svelte-kit web/node_modules
	rm -rf logs/ .server.pid .web.pid

#
# help
#
help:
	@echo "available commands:"
	@echo ""
	@echo "  environment:"
	@echo "    make setup          - create virtual environment and install dependencies"
	@echo "    make dev-install    - install development dependencies"
	@echo ""
	@echo "  servers:"
	@echo "    make run            - run the main server (fastapi server)"
	@echo "    make dev            - start all servers in development mode"
	@echo "    make stop           - stop all running servers"
	@echo ""
	@echo "  clients:"
	@echo "    make run-cli        - run the CLI client"
	@echo ""
	@echo "  knowledge base:"
	@echo "    make update-kb      - update the knowledge base and exit"
	@echo ""
	@echo "  web frontend:"
	@echo "    make web-setup      - install web frontend dependencies"
	@echo "    make web-dev        - run web frontend development server"
	@echo "    make web-build      - build web frontend for production"
	@echo ""
	@echo "  development:"
	@echo "    make format         - format code with black"
	@echo "    make sort-imports   - sort imports with isort"
	@echo "    make lint           - run all formatting"
	@echo ""
	@echo "  testing:"
	@echo "    make test           - run tests"
	@echo "    make test-coverage  - run tests with coverage report"
	@echo "    make test-verbose   - run tests with verbose output"
	@echo ""
	@echo "  cleanup:"
	@echo "    make clean          - clean up generated files" 