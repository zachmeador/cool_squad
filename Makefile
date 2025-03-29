.PHONY: setup dev-install run dev stop stop-force update-kb run-cli test test-coverage test-verbose web-setup web-dev web-build clean clean-logs help

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
	@mkdir -p _data/logs
	@$(MAKE) stop-force  # ensure no stray processes
	@python -m cool_squad.main > _data/logs/server.log 2>&1 & echo $$! > .server.pid
	@cd web && bun run dev > ../_data/logs/web.log 2>&1 & echo $$! > ../.web.pid
	@echo "servers started! check _data/logs directory for output"
	@echo "use 'make stop' to shut down all servers"

dev-clean:
	@$(MAKE) clean-logs
	@$(MAKE) dev

dev-restart:
	@echo "restarting development servers..."
	@$(MAKE) stop
	@$(MAKE) dev

stop:
	@echo "stopping all servers..."
	@if [ -f .server.pid ]; then kill $$(cat .server.pid) 2>/dev/null || true; rm .server.pid; fi
	@if [ -f .web.pid ]; then kill $$(cat .web.pid) 2>/dev/null || true; rm .web.pid; fi
	@pkill -f "next dev" 2>/dev/null || true
	@pkill -f "cool_squad.main" 2>/dev/null || true
	@pkill -f "python -m cool_squad" 2>/dev/null || true
	@echo "all servers stopped"

stop-force:
	@echo "force stopping all potential server processes..."
	@if [ -f .server.pid ]; then kill -9 $$(cat .server.pid) 2>/dev/null || true; rm .server.pid; fi
	@if [ -f .web.pid ]; then kill -9 $$(cat .web.pid) 2>/dev/null || true; rm .web.pid; fi
	@pkill -9 -f "next dev" 2>/dev/null || true
	@pkill -9 -f "cool_squad.main" 2>/dev/null || true
	@pkill -9 -f "python -m cool_squad" 2>/dev/null || true
	@echo "killed any stray processes"

#
# cleanup commands
#
clean-logs:
	@echo "cleaning logs..."
	@rm -rf _data/logs/
	@mkdir -p _data/logs/
	@echo "logs cleared"

clean:
	@echo "cleaning app state..."
	@rm -rf _data/
	@rm -rf .server.pid .web.pid
	@$(MAKE) clean-logs
	@echo "app state cleared"

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
# testing
#
test:
	pytest tests

test-coverage:
	pytest --cov=cool_squad tests/ --cov-report=term-missing

test-verbose:
	pytest -v tests/

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
	@echo "    make stop-force     - force stop all potential server processes"
	@echo ""
	@echo "  cleanup:"
	@echo "    make clean-logs     - clear all logs"
	@echo "    make clean          - clear all app state"
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