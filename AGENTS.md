# AGENTS.md

## Mission

This repository contains a Databricks asset bundle for the RevoData assessment. The agent should help with Python code, tests, bundle configuration, and Databricks workflow changes while staying aligned with the project conventions.

## Repository map

- `src/revodata_assessment/` — application code entry points.
- `tests/` — pytest suite.
- `notebooks/` — Databricks notebook and pipeline examples.
- `resources/` — Databricks bundle resources.
- `data/` — source data and sample outputs.
- `docs/` — project documentation and setup guidance.
- `databricks.yml` — bundle configuration.
- `pyproject.toml` — project metadata, tooling, and dev dependencies.
- `.justfile` — common local tasks.

## Operating conventions

- Target Python version: 3.12.
- Use `uv` for dependency management and running commands when possible.
- Prefer small, targeted edits over broad refactors.
- Keep code readable, explicit, and aligned with the Ruff/ty configuration in `pyproject.toml`.
- Avoid unnecessary dependencies or large framework changes.

## Required workflow

1. Before patching a bug, inspect the exact failing behavior and relevant tests.
2. Prefer adding or updating a test that captures the missing or broken behavior.
3. Make the minimal root-cause fix.
4. Run the smallest validation command that checks the changed behavior.

## Validation commands

Use the repo's standard commands:

- `uv sync --group dev`
- `uv run pytest`
- `uv run ruff check .`
- `uv run ty check .`
- `just lint`
- `just test`
- `just validate`

## Project-specific guidance

- Treat this as a Databricks bundle project, not a generic Python app.
- Keep bundle and resource changes consistent with the existing `resources/` and `databricks.yml` layout.
- If a task touches notebooks or Databricks APIs, preserve compatibility with the repo's configured Databricks runtime and patterns.
- Do not remove or bypass existing project tooling unless the task explicitly requires a change to the build or CI setup.

## Coding expectations

- Follow NumPy-style docstrings where appropriate.
- Keep imports organized and avoid dead code.
- Respect the Ruff ignores already configured in `pyproject.toml`.
- Keep tests fast and deterministic.
- Prefer clear naming and explicit logic over clever abstractions.

## Final quality bar

The agent should leave the repository in a working state, with:

- passing relevant tests,
- clean linting for touched files,
- no unexplained config drift,
- and changes that match the expectations of a Databricks-focused Python project.
