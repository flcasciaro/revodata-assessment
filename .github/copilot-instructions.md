# Copilot instructions for RevoData assessment

## Project context

This repo is a Python-based Databricks asset bundle project. The code lives under `src/revodata_assessment`, with tests under `tests`, Databricks resources under `resources`, and notebook/pipeline examples under `notebooks`.

## Preferred workflow

- Use `uv` for Python commands.
- Prefer small, surgical changes over broad refactors.
- Add or update tests before finalizing bug fixes.
- Validate with the smallest relevant command.

## Tooling

- Python: 3.12
- Lint: Ruff
- Type checking: ty
- Tests: pytest
- Common tasks: `just lint`, `just test`, `just validate`

## Guardrails

- Keep the Databricks bundle structure intact.
- Preserve naming and configuration patterns already used in the repo.
- Avoid unnecessary dependencies and do not introduce one-off hacks.
- Favor explicit, maintainable code over clever shortcuts.

## Examples of good behavior

- Fix the root cause, not just the symptom.
- Match the existing style of the repository.
- Keep docs and examples aligned with code changes.
- Ensure bundle/resource updates remain coherent with `databricks.yml`.
