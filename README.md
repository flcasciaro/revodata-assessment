# revodata-assessment

![Databricks Runtime](https://img.shields.io/badge/Databricks%20Runtime-16.4--LTS-%231B3139)
[![python](https://img.shields.io/badge/python-3.12-g)](https://www.python.org)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with ty](https://img.shields.io/badge/type%20checked-ty-261230.svg)](https://github.com/astral-sh/ty)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

RevoData technical assessment submission: a medallion-architecture Databricks
pipeline that ingests Kamernet rental and Airbnb listing data, cleans it,
backfills missing Airbnb postal codes from geo data, and
estimates potential revenue per property and per postal code to compare
long-term (Kamernet) vs. short-term (Airbnb) rental income.

- **[Pipeline Design](docs/pipeline.md)** -- what the pipeline does and, more
  importantly, why: scoping, cleaning, the postal code backfill, and the
  revenue assumptions.
- `scratch/eda.ipynb` -- the exploratory analysis that the cleaning and
  backfill decisions are based on.

The `revodata-assessment` project was generated from [RevoData Declarative Automation Bundle Templates](https://github.com/revodatanl/revo-dabs) version `1.0.0`.

## Results

Parquet snapshots of all five gold tables live in [`data/output`](data/output),
exported from a real pipeline run on Databricks serverless. The table that
answers the assessment's question is `gold_postcode_revenue`: one row per
4-digit postal code, with the average estimated annual revenue for each
channel side by side and a `more_profitable_channel` column.

It covers **1,828 postal codes**, but the two sources do not overlap evenly:

| Coverage | Postal codes |
| --- | ---: |
| Kamernet listings only | 1,743 |
| Both channels | 81 |
| Airbnb listings only | 4 |

**Read `more_profitable_channel` with that coverage in mind.** Counted across
all 1,828 rows it reports `rental` 1,744 times and `airbnb` 84 times, which
looks like a decisive win for long-term leasing. It is not. Where a postal
code has no Airbnb listings at all there is nothing to compare, and the
column falls back to `rental`; 1,743 of those 1,744 rows are that fallback
rather than an actual comparison.

Restricted to the 81 postal codes where **both** channels are present, the
result inverts:

| Among postcodes with both channels (81) | |
| --- | ---: |
| Airbnb more profitable | 80 |
| Kamernet more profitable | 1 |
| Median avg. annual revenue, Kamernet | EUR 11,189 |
| Median avg. annual revenue, Airbnb | EUR 33,604 |

So on this data short-term letting looks roughly three times more profitable
wherever a like-for-like comparison is possible -- concentrated in Amsterdam,
since every Airbnb zipcode in the source falls in the 10xx-11xx range while
the Kamernet export covers ~700 Dutch cities.

Two caveats before taking that at face value, both detailed in
[Pipeline Design](docs/pipeline.md):

- The Airbnb figure assumes 180 occupied nights per year and **ignores
  Amsterdam's 30-night regulatory cap** on short-term letting of entire
  homes. That inflates the Airbnb side substantially for exactly the
  postcodes where the comparison is possible.
- Neither source contains booking history, so "revenue" is a documented
  estimate throughout, not an observed figure.

Single-sided postal codes are deliberately kept rather than dropped -- an
area with Kamernet supply and no Airbnb presence is itself an
investment-potential signal -- but that design choice is what makes the
raw `more_profitable_channel` counts misleading at national scope.

## Prerequisites

Ensure you have the following tools installed:

- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager and project management
- **[git](https://git-scm.com/)** - Version control system
- **[Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html)** - Command-line interface for Databricks operations
- **[just](https://just.systems/man/en/packages.html)** - Build automation tool (very convenient during development)

**Platform Support**: This project is designed for **Linux**, **macOS** and **Windows**.

## Quick Start

Set up a fully configured development environment -- virtualenv, dependencies
and pre-commit hooks -- by running:

```bash
just
```

That is all you need for linting. Everything else, **including the test
suite**, talks to a real Databricks workspace; see below.

```bash
just lint     # ruff, ty and pydoclint -- runs fully offline
just test     # pytest -- REQUIRES a Databricks workspace, see Running it
just list     # all available recipes
```

## Running it

### 1. Authenticate

```bash
databricks auth login --host https://<your-workspace>.cloud.databricks.com
```

The `just` bundle recipes pass `--profile $PROFILE_NAME`, which defaults to
`DEFAULT`. To use a different profile, set it in a git-ignored `.env` file at
the repository root (the `.justfile` loads it automatically) rather than
editing any tracked file:

```bash
echo 'PROFILE_NAME=my-profile' >> .env
```

### 2. Point the bundle at your workspace

Two values assume the workspace this was built against, and both need changing
for any other one:

- `databricks.yml` -- `targets.dev.workspace.host` must match your profile's
  host URL.
- `resources/property_revenue_pipeline.yml` -- `catalog: workspace`. That was
  the only managed catalog available in the trial workspace used here.
  Substitute a Unity Catalog catalog you can write to.

### 3. Deploy and run

Deploying only syncs code and registers resources -- it does **not** execute
anything. The pipeline has to be run separately:

```bash
just validate   # check the bundle resolves
just deploy     # sync code + register the pipeline
just run        # trigger a pipeline update -- this is what builds the tables
just summary    # links to the deployed resources
```

The gold tables then exist as Delta tables in Unity Catalog. `just destroy`
removes everything again.

### 4. Tests

`tests/conftest.py` opens a real serverless Databricks Connect session rather
than a local Spark one, so 12 of the 48 tests need a reachable workspace and
valid credentials. Without them those 12 fail with `default auth: cannot
configure default credentials` while the other 36 pass. The same credentials
drive CI, as two repository secrets -- see
[Bundle Deployment](docs/bundle_deployment.md).

```bash
just test
```

### 5. Regenerating `data/output` (optional)

The Parquet snapshots are committed, so this is only needed after changing the
pipeline. It needs a Unity Catalog Volume, because Workspace Files do not
support Spark's distributed writes:

```bash
databricks volumes create workspace revodata_assessment_dev exports MANAGED
# run notebooks/export_gold_to_parquet.py in the workspace, then:
databricks fs cp -r   dbfs:/Volumes/workspace/revodata_assessment_dev/exports/data_output   ./data/output
```

Replace each directory rather than copying over it -- Spark names every part
file after a fresh transaction id, so copying on top leaves two part files per
folder and silently doubles every table. Full detail in
[Pipeline Design](docs/pipeline.md#exporting-to-dataoutput).

## Documentation

Comprehensive documentation can be found in the [documentation](docs/README.md).

- **[Pipeline Design](docs/pipeline.md)** - What the property-revenue pipeline does and why
- **[Getting Started](docs/getting_started.md)** - Set up your development environment
- **[Development](docs/development.md)** - Project structure, configuration, code quality, and (testing on) Databricks Connect
- **[Bundle Deployment](docs/bundle_deployment.md)** - Deployment of Declarative Automation Bundles (formerly Databricks Asset Bundles), Git strategy, and CI/CD
- **[Coding Standards](docs/coding_standard.md)** - Code style and conventions

## Troubleshooting

- Refer to the [Databricks documentation](https://docs.databricks.com/dev-tools/bundles/index.html) for bundle-specific questions
