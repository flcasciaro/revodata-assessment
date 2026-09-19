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

```bash
just test
```

`tests/conftest.py` opens a real serverless Databricks Connect session rather
than a local Spark one, so 12 of the 48 tests need a reachable workspace and
valid credentials. Without them those 12 fail with `default auth: cannot
configure default credentials` while the other 36 pass. The same credentials
drive CI, as two repository secrets -- see
[Bundle Deployment](docs/bundle_deployment.md).

#### Why Databricks Connect and not a local PySpark session

A local `SparkSession` would make those 12 tests run offline in seconds, which
is tempting. It was rejected for three reasons:

- **It would test a different engine than the one that runs the pipeline.** On
  Databricks serverless, Python UDFs execute in an isolated sandbox, Unity
  Catalog governs every read, and the execution model is Spark Connect rather
  than a local JVM. Asserting that `clean_rentals` works under local Spark
  proves it works somewhere the pipeline never runs.
- **The two cannot share one virtualenv.** `databricks-connect` ships its own
  `pyspark` and [conflicts with a separately installed
  one](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/python/troubleshooting#conflicting-pyspark-installations),
  so supporting both would mean two dependency sets and two ways to be wrong.
- **The serverless-specific failures are the ones worth catching.** Two real
  bugs surfaced this way and could not have surfaced locally: the geo UDF's
  polygon closure intermittently failing to materialize on the executor (fixed
  in `geo.make_postcode_lookup_udf` by closing over a path instead of the
  polygons), and `shapely` missing from the remote UDF environment (fixed with
  `DatabricksEnv().withDependencies(...)` in `tests/conftest.py`).

The cost is a suite that is not hermetic: it needs a workspace, and a full run
takes minutes rather than seconds. For a project whose entire job is to run on
Databricks, that is the right trade.

#### Why a trial workspace and not Databricks Free Edition

This was built against a 14-day Databricks **free trial** workspace rather than
the free-forever **Free Edition** that replaced Community Edition. Free Edition
was tried first and cannot run this project.

There, 6 of the 48 tests fail with:

```
pyspark.errors.exceptions.connect.SparkException:
[ISOLATION_STARTUP_FAILURE.SANDBOX_STARTUP] Failed to start isolated execution environment.
```

Those 6 are exactly and only the tests that execute a **Python UDF** on the
remote serverless cluster: the 2 in `tests/test_transformations_rentals.py`
(`clean_rentals` wraps the `cleaning.py` parsers as `F.udf`) and the 4 in
`tests/test_transformations_airbnb.py` (`F.udf` plus the `pandas_udf` geo
lookup). The other 6 Spark tests pass -- they use only native Spark
expressions and never need a sandbox.

On serverless every Python UDF runs in an isolated container, and
[`ISOLATION_STARTUP_FAILURE.SANDBOX_STARTUP`](https://docs.databricks.com/aws/en/error-messages/isolation-startup-failure-error-class)
means that container never started. It is a platform-level error (SQLSTATE
`XXKSS`) whose documented remedy is to contact Databricks support, which Free
Edition does not include. It is consistent with two published [Free Edition
limitations](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations):
outbound internet access restricted to a small set of trusted domains -- the
test session declares a custom environment that must install `shapely` from
PyPI before any UDF sandbox can start -- and tight serverless compute quotas.

The same commit, changing only the CLI profile, runs 48/48 on the trial
workspace. And since the Level 5 postal code backfill *is* a pandas UDF, a
workspace that cannot start UDF sandboxes cannot run the pipeline either, not
just its tests. Hence the trial.

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

## How this was built

Three phases, in that order; `git log` follows the same arc.

### 1. Exploration, run directly on Databricks

Before any pipeline code, both sources were explored in a notebook running on
the workspace itself -- `scratch/eda.ipynb`, kept in the repo as the record the
design decisions rest on. It reads the raw files from Workspace Files with
Spark, so the exploration ran against the same engine and the same data the
pipeline would later use, not against a pandas sample on a laptop.

What it established:

- **Kamernet (`rentals.json`)** -- 46,722 listings across ~700 Dutch cities
  (Amsterdam the largest at 8,095). `postalCode` is a clean 6-character code on
  *every* row, so no backfill is needed on this side. `rent` and `areaSqm`,
  however, are scraped free text (`"EUR 950,-  Utilities incl."`, `"14 m2"`),
  and several fields arrive wrapped in single-element JSON arrays.
- **Airbnb (`airbnb.csv`)** -- 9,913 listings, no city column, every observed
  zipcode in the Amsterdam 10xx-11xx range. Only 4,530 rows carry a full
  6-character code; 3,119 carry a bare 4-digit one and 2,254 have no `zipcode`
  at all. Every row missing a zipcode does have coordinates, which is what
  makes the geo backfill viable. Roughly 388 rows are exact duplicates, and
  about 10 more hide a valid postcode inside noisy text (`"Nederland 1091 TS"`,
  `"1018  DW"`) that a strict format check would have discarded.
- **The join key** -- Kamernet is 6-character, Airbnb is mixed, and
  `post_codes.geojson` is keyed by 4-digit PC4 only, so PC4 is the one key both
  sources can support. A PC4 area is roughly block-to-neighbourhood sized:
  granular enough to show patterns, coarse enough to keep per-postcode averages
  meaningful.
- **The backfill prototype** -- the point-in-polygon lookup was proven in the
  notebook as a `pandas_udf` over the ~470 PC4 polygons before being promoted
  to `src/revodata_assessment/geo.py`.

Full reasoning in [Pipeline Design](docs/pipeline.md).

### 2. Implementation, in iterations

The pipeline was not written in one pass. The steps that actually changed the
design:

1. **Medallion skeleton** -- bronze/silver/gold as Lakeflow Declarative
   Pipeline notebooks, with the reusable logic split out into
   `src/revodata_assessment/` so it could be unit tested away from the
   pipeline. That split answers the assessment asking for buildable packages in
   `src` *and* notebooks: the notebooks stay thin wiring, the wheel carries the
   logic and is installed into the pipeline environment via `${var.wheel_path}`.
2. **Serverless everywhere** -- pipeline, tests and deploy target all moved to
   serverless compute. This is what forced the custom UDF environment and the
   artifact shipping in `tests/conftest.py`.
3. **Modern pipeline API** -- migrated off the legacy DLT spelling onto
   `pyspark.pipelines` (`dp.materialized_view`, `dp.expect_all_or_drop`).
4. **Dropping the Amsterdam filter** -- an early version scoped rentals to
   Amsterdam. Nothing in the assessment asked for that, and it silently
   discarded ~38k of the 46,722 Kamernet listings, so it was removed across the
   codebase and the gold Parquet exports were regenerated without it.
5. **Materialized views, stated explicitly** -- every dataset returns a batch
   DataFrame, so `@dp.table` and `@dp.materialized_view` build the same thing.
   The decorator was made explicit so the intent is readable instead of
   inferred from a return type.
6. **Streaming, evaluated and declined** -- a streaming read of `rentals.json`
   was prototyped, then deliberately dropped. Auto Loader incrementalizes per
   *file*, not per record, and `rentals.json` is a single 69 MB file holding one
   JSON array: the stream yields one micro-batch with all 46,722 rows and
   nothing afterwards. The analysis is kept in
   [Pipeline Design](docs/pipeline.md) rather than in code.

### 3. CI/CD

`.github/workflows/pr-deploy-dev.yml` runs on every pull request to `main`:

- **`validate`** -- `ruff check`, `ruff format --check`, `ty` and `pydoclint`;
  then a packaging guard that unpacks the built sdist and diffs it against
  `src/`, so a source file that never makes it into the wheel fails CI instead
  of the pipeline; then the full `pytest` suite with coverage.
- **`deploy-dev`** -- gated on `validate`: `databricks bundle validate` and
  `databricks bundle deploy --target dev`, then `bundle summary` written to the
  GitHub step summary. Deploys are serialised through a concurrency group,
  because every PR targets the same `dev` bundle state.

Since the tests open a real Databricks Connect session, CI needs the same
credentials the deploy does: `DATABRICKS_HOST` and `DATABRICKS_TOKEN` as
**repository** secrets -- environment secrets are not visible to the job and
produce exactly the `default auth: cannot configure default credentials`
failure described above. See [Bundle Deployment](docs/bundle_deployment.md).

### Session transcripts

`claude_sessions/` holds the raw Claude Code session exports (one `.jsonl` per
session) from building this project. They are committed as-is so the work
described above can be traced back to the conversations that produced it.

## Documentation

Comprehensive documentation can be found in the [documentation](docs/README.md).

- **[Pipeline Design](docs/pipeline.md)** - What the property-revenue pipeline does and why
- **[Getting Started](docs/getting_started.md)** - Set up your development environment
- **[Development](docs/development.md)** - Project structure, configuration, code quality, and (testing on) Databricks Connect
- **[Bundle Deployment](docs/bundle_deployment.md)** - Deployment of Declarative Automation Bundles (formerly Databricks Asset Bundles), Git strategy, and CI/CD
- **[Coding Standards](docs/coding_standard.md)** - Code style and conventions

## Troubleshooting

- Refer to the [Databricks documentation](https://docs.databricks.com/dev-tools/bundles/index.html) for bundle-specific questions
