PYTHON ?= python3
REPOOS = env PYTHONPATH=src $(PYTHON) -m repoos

.PHONY: verify test lint format format-check typecheck build validate cli-smoke \
	agentops-pr agentops-weekly agentops-monthly hooks-smoke mcp-smoke

verify: format-check lint typecheck test validate cli-smoke build

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

format-check:
	$(PYTHON) -m ruff format --check .

typecheck:
	$(PYTHON) -m mypy src/repoos

build:
	$(PYTHON) -m build --no-isolation

validate:
	$(REPOOS) --format json validate --all

cli-smoke:
	$(REPOOS) --help
	$(REPOOS) --format json doctor
	$(REPOOS) --format json check-update --project .

agentops-pr: verify

agentops-weekly:
	$(REPOOS) --format json audit --all

agentops-monthly:
	$(REPOOS) --format json audit --all

hooks-smoke:
	$(REPOOS) --format json validate --all

mcp-smoke:
	$(PYTHON) tools/agentops/audit_mcp.py --smoke
