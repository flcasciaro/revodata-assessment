---
description: "Repository-aware engineering agent for the RevoData assessment"
---

# RevoData Assessment Agent

You are working in a Python and Databricks bundle repository.

## Goals

- Keep the project aligned with the repository's existing patterns.
- Prefer minimal, root-cause fixes.
- Validate with the smallest relevant command and keep the repo healthy.

## Repository context

- Python target: 3.12
- Package entry point: `src/revodata_assessment`
- Test framework: pytest
- Linting: Ruff
- Type checking: ty
- Common tasks: `just lint`, `just test`, `just validate`

## Working rules

1. Read the relevant files before editing.
2. Favor precise updates over broad rewrites.
3. Add or update tests for behavioral fixes.
4. Keep Databricks bundle changes consistent with existing configuration.
5. Leave the project in a clean and reviewable state.

## Useful commands

- `uv sync --group dev`
- `uv run pytest`
- `uv run ruff check .`
- `uv run ty check .`
- `just test`
- `just validate`

## Response style

Provide concise, actionable updates and explain the reasoning behind the fix when it is important to the task.
