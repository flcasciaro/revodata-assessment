# Development

## Project Structure

The project is structured as follows:

```text
revodata-assessment/
├── .github/workflows/              # GitHub Actions CI/CD
├── .just/                          # just recipe imports (DAB, shell settings)
├── data/                           # Source exports and the gold Parquet output
├── docs/                           # Documentation
├── notebooks/                      # Databricks notebooks (pipeline + export)
├── resources/                      # Databricks resources (pipeline definition)
├── scratch/                        # Exploratory analysis behind the design choices
├── src/                            # Source code
├── tests/                          # Tests
├── .gitignore                      # Git ignore patterns
├── .justfile                       # Development automation
├── .pre-commit-config.yaml         # Pre-commit hooks configuration
├── .python-version                 # Python version specification
├── databricks.yml                  # Bundle configuration
├── pyproject.toml                  # Python project configuration
├── README.md                       # Project documentation
└── uv.lock                         # Pinned dependency versions
```

## Project Configuration

Projects include three key configuration files that work together to define the project structure and behavior:

### databricks.yml

The Declarative Automation Bundle configuration:

- **Bundle name**: Uses the project name from template parameters
- **Artifact configuration**: Defines Python wheel packaging using `uv build` with dynamic versioning
- **Resources**: Specifies Databricks resources like jobs and pipelines

### pyproject.toml

The Python project configuration file that defines:

- **Project metadata**: Name, version, description, author information, and Python version requirements
- **Dependencies**: Core dependencies are minimal by default, with comprehensive development dependencies including:
  - `databricks-connect` for local Databricks development
  - `databricks-sdk` for Databricks integration
  - Python tooling: `ruff`, `ty`, `pytest`, `prek`, `commitizen`
- **Tool configuration**:
  - **Ruff**: Linting and formatting with RevoData's coding standards
  - **ty**: Fast type checking (Astral's type checker)
  - **Pytest**: Test configuration with coverage reporting
  - **Pydoclint**: Documentation linting with NumPy-style docstrings

## Code Quality

We ~~encourage~~ enforce code quality with pre-commit hooks and the CI
workflow in `.github/workflows/pr-deploy-dev.yml`, which runs the same
checks on every pull request. See [Bundle Deployment](bundle_deployment.md).

### Pre-commit Hooks

Ensure that the [`pre-commit`](https://pre-commit.com) hook defined in `.pre-commit-config.yaml` passes successfully:

- [`commitizen`](https://github.com/commitizen-tools/commitizen) to enforce conventional commit standards.
- [`ruff`](https://docs.astral.sh/ruff/) for linting and formatting.
- [`ty`](https://github.com/astral-sh/ty) for static type checking.
- [`pydoclint`](https://github.com/shmsi/pydoclint) to lint docstrings.



## Local Development with Databricks Connect

Run local code on Databricks compute. Four connection methods:

| Method | Use Case | Configuration |
|--------|----------|---------------|
| **VS Code Extension** | Visual cluster selection | [Install extension](https://marketplace.visualstudio.com/items?itemName=databricks.databricks) |
| **Serverless** | Development, testing | `DatabricksSession.builder.serverless(True).getOrCreate()` |
| **Profile-based** | Multiple workspaces | `Config(profile="<name>", cluster_id="<id>")` |
| **Environment** | CI/CD pipelines | Set `DATABRICKS_CONFIG_PROFILE` and `DATABRICKS_HOST` in `.env` |

### Testing on (serverless) Databricks Connect

Tests are configured to automatically run on (serverless) Databricks Connect. This is configured in the `tests/conftest.py` file, which is automatically discovered by `pytest`. A spark session for testing is created using the `DatabricksSession` builder with serverless mode enabled.

```python
from databricks.connect import DatabricksSession

spark = DatabricksSession.builder.serverless(True).getOrCreate()
```

## Troubleshooting

Common issues and solutions:

1. **Authentication**: Ensure your `.databrickscfg` is properly configured
2. **Environment conflicts**: Check that your `.env` file doesn't conflict with system environment variables
3. **Cluster access**: Verify you have permission to access the specified cluster or serverless compute
4. **Version compatibility**: Ensure your local Databricks Connect version is compatible with your workspace
5. **Conflict with PySpark**: [Databricks Connect conflicts with PySpark](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/troubleshooting#conflicting-pyspark-installations). Having both installed will cause errors when initializing the Spark context in Python.

...and of course:

![it-crowd](images/it-crowd.png)
