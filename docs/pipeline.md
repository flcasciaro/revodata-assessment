# Pipeline Design

This documents the *why* behind the `property-revenue-pipeline`; see
`notebooks/pipelines/property_revenue/README.md` for a map of *what* each
file does.

## Goal

Identify which Amsterdam postal codes have the most investment potential,
and whether a property there would earn more as a long-term Kamernet lease
or a short-term Airbnb listing. That comparison drives every design choice
below.

## Architecture

A [medallion](https://www.databricks.com/glossary/medallion-architecture)
pipeline built with Lakeflow Declarative Pipelines (Level 3):

```
bronze_rentals ──▶ silver_rentals ──▶ gold_rentals_property_revenue ──▶ gold_rentals_postcode_revenue ─┐
                                                                                                          ├─▶ gold_postcode_revenue
bronze_airbnb  ──▶ silver_airbnb  ──▶ gold_airbnb_property_revenue  ──▶ gold_airbnb_postcode_revenue  ──┘
```

- **Bronze**: raw ingestion, no transformation, so the original scrape is
  always recoverable.
- **Silver**: typed, cleaned, quality-checked (see Expectations below).
- **Gold**: business metrics -- estimated revenue per property, then
  aggregated per postcode, then compared side-by-side.

Reusable parsing and Spark transformation logic lives in
`src/revodata_assessment/` (`cleaning.py`, `geo.py`,
`transformations/*.py`) and is unit tested independently of the pipeline
notebooks, which stay thin wiring around `@dp.table`. Streaming ingestion
(Level 4) was intentionally skipped: both sources are static, one-off
exports, so a streaming Auto Loader would add operational complexity
(checkpoints, schema evolution handling) without a real freshness
requirement to justify it.

## City scope

`rentals.json` covers every Dutch city (46,722 rows across ~700 cities;
Amsterdam is the largest at 8,095). `airbnb.csv` has no city column, but
every zipcode observed is in the 10xx-11xx range, i.e. Amsterdam only. The
pipeline does not filter either source by city: `silver_rentals` keeps all
~700 cities and carries `city` through as a column, so downstream consumers
can scope the data themselves. The practical consequence is that the
Kamernet-vs-Airbnb comparison in `gold_postcode_revenue` is only populated
on both sides for postcodes where Airbnb has listings -- elsewhere the
Airbnb columns are simply absent from the join.

## Why postcode4

Both sources ultimately support a 4-digit postal code (PC4): Kamernet's
`postalCode` is always a full 6-character code (verified during EDA -- see
`scratch/eda.ipynb`), and the
`post_codes.geojson` reference dataset used for backfilling Airbnb is itself
keyed by PC4, not the 6-character code. A PC4 area in Amsterdam is roughly
street-block-to-neighborhood sized, which is granular enough to spot
investment patterns while keeping enough listings per postcode for the
revenue averages to be meaningful -- the full 6-character code would each
cover only a handful of addresses per source, undersplitting both sides of
the comparison. `postcode4` is therefore the join/aggregation key
throughout silver and gold.

## Cleaning

- **Kamernet (`cleaning.parse_currency`, `parse_area_sqm`)**: `rent` and
  `areaSqm` are scraped as free text (`"€ 950,-  Utilities incl."`,
  `"14 m2"`) with several other fields wrapped in single-element JSON
  arrays by the scraper (e.g. `_id`); these are parsed/flattened into typed
  columns. Postal codes were already clean 6-character codes on every row,
  so no backfill was needed on this side.
- **Airbnb (`cleaning.normalize_postal_code`, `extract_postcode4`)**: 9,913
  rows, of which 2,254 have no `zipcode` at all, 3,119 already carry a bare
  4-digit code, and 4,530 carry a full 6-character code -- matching the
  starting analysis. A closer look also found ~10 rows where a valid
  postcode is embedded in noisy text (`"Nederland 1091 TS"`,
  `` "`1055tk" ``, `"1018  DW"` with a double space), alongside a handful of
  genuinely unusable values (`"...."`, `"b"`, `"0"`, `"342HUIS"`). Rather
  than treating "not a clean 6-character code" as automatically missing,
  `extract_postcode4` searches for the `NNNN LL` pattern anywhere in the
  string first, and only falls back to the geo lookup when nothing
  recoverable is found -- recovering those extra rows without a geo lookup
  and without discarding them as invalid. `latitude`/`longitude` were
  present for every row with a missing zipcode, so all missing-postcode
  rows are backfillable in principle; a handful still fail (falling
  outside every polygon in the reference dataset) and are dropped by the
  `has_postcode4` expectation.
- Airbnb also has ~388 exact duplicate rows (same coordinates, price, room
  type and capacity), dropped in `clean_airbnb`.

## Postal code backfill (Level 5)

`silver_airbnb` matches each listing with no parsable postal code against
`data/geo/post_codes.geojson` using a point-in-polygon lookup
(`geo.find_pc4_by_point`, wrapped as a pandas UDF in
`geo.make_postcode_lookup_udf`): the listing's `(longitude, latitude)` is
tested against each of the ~470 PC4 polygons, and the first one containing
the point supplies the postcode. A pandas UDF was used instead of a plain
row UDF to batch the Python/JVM serialization overhead, since every row is
checked against every polygon (no spatial index) -- acceptable at this
data volume, but the first thing to optimize (e.g. an R-tree via
`shapely.STRtree`) if the dataset grew substantially. `silver_airbnb` keeps
a `postcode_source` column (`source` / `geo_backfill` / `unresolved`) so the
backfill's impact stays auditable rather than silently blended into the
data.

The alternative stretch option -- querying an external postcode API via a
UDF -- was not used: it would add a network dependency and rate limits to
every pipeline run for data the provided GeoJSON already covers.

## Revenue estimate and its assumptions

Neither dataset includes booking or occupancy history, so revenue is an
estimate, not an observed figure (see `transformations/gold.py`):

- **Kamernet**: `monthly_rent_eur x 12`. A long-term lease is assumed to be
  continuously occupied.
- **Airbnb**: `nightly_price_eur x assumed_occupied_nights_per_year`
  (default 180, i.e. ~50% occupancy), configurable via the pipeline's
  `airbnb_assumed_occupied_nights_per_year` setting. This deliberately
  ignores Amsterdam's regulatory cap of 30 nights/year on short-term
  rental of an entire home: modeling that correctly requires splitting the
  assumption by `room_type` (a cap only applies to `Entire home/apt`, not
  to renting a room in an owner-occupied home) and was judged out of scope
  for the assessment's time box. Left as-is, the estimate overstates
  Airbnb revenue for entire-home listings, which is the single most
  important caveat when reading `gold_postcode_revenue` -- it structurally
  favors Airbnb over Kamernet wherever `room_type` skews toward entire
  homes.

`gold_postcode_revenue` joins the two per-postcode aggregates with a `full`
join (not `inner`): a postcode with listings on only one side is still
useful investment-potential signal, so it's kept and labeled with that side
as the `more_profitable_channel` rather than dropped.

## Data quality expectations (Level 3)

Each silver table declares its quality bar with `@dp.expect_all_or_drop`
rather than filtering inside the reusable transformation functions, so the
checks stay visible in the pipeline's data quality UI/event log instead of
being buried in library code:

- `silver_rentals`: non-null `postcode4`, `monthly_rent_eur > 50` (24 rows
  across the source carry a junk rent of `€ 1,-`), `area_sqm > 0`.
- `silver_airbnb`: non-null `postcode4` (i.e. the row must have resolved
  through parsing or the geo backfill), `nightly_price_eur > 0`,
  `accommodates > 0`.

## Deployment (Level 3)

Deployed as a Databricks Asset (Declarative Automation) Bundle --
`resources/property_revenue_pipeline.yml` defines the pipeline, which is
triggered manually; no scheduling job wraps it, since both sources are
static one-off exports with nothing to re-ingest on a timer.
`databricks.yml`'s `dev`/`test`/`prod` targets follow the bundle template
unchanged. Data file paths are passed in as pipeline
`configuration` (`rentals_path`, `airbnb_path`, `postcodes_geojson_path`)
resolved from `${workspace.file_path}`, the location the bundle syncs
`./data` to, rather than hardcoded -- the same pipeline definition works
across `dev`/`test`/`prod` without editing notebook code.

## CI/CD and pre-commit (Level 1)

The live pipeline is GitHub Actions, since this repo is hosted on GitHub:
`.github/workflows/pr-deploy-dev.yml` runs on every pull request targeting
`main`. Its `validate` job runs `ruff check`, `ruff format --check`, `ty`
and `pydoclint`, builds the wheel and diffs it against `src/` to catch a
source file that would silently not ship, then runs `pytest`. Only if that
job passes does `deploy-dev` run `databricks bundle validate` and
`databricks bundle deploy` against the `dev` target, so a PR's code can be
exercised in the workspace before it is merged. Deploys are serialised
across PRs with a job-level concurrency group, since every PR targets the
same `dev` deployment.

Both jobs authenticate with the `DATABRICKS_HOST` and `DATABRICKS_TOKEN`
repository secrets -- the tests need them as much as the deploy does, since
`tests/conftest.py` opens a real serverless Databricks Connect session
rather than a local Spark one.

`.azure/.azure-pipelines/` is the Azure DevOps equivalent that ships with
the RevoData DAB template (`ci.yml` on push, `cd.yml` deploying to `test`
then `prod` behind a manual approval). It is kept for reference but is not
wired up: its `groupName`, `keyVaultName` and `azureSubscription` variables
are still template placeholders.

`.pre-commit-config.yaml` runs the same lint/format/type checks locally
before a commit is made.

## Exporting to `data/output`

Gold tables live as governed Delta tables in Unity Catalog, not as files in
this repo -- that's the point of a medallion pipeline. For the assessment's
Parquet export deliverable, run `notebooks/export_gold_to_parquet.py`
manually after a pipeline run (not on every scheduled run: an ad hoc
snapshot for review is a different concern from the pipeline's real
output). It writes to a Unity Catalog Volume rather than a `/Workspace/...`
path, since Workspace Files don't support Spark's distributed writes; create
the volume once with `databricks volumes create workspace
revodata_assessment_dev exports MANAGED`, then after running the notebook,
pull the files down locally:

```bash
databricks fs cp -r dbfs:/Volumes/workspace/revodata_assessment_dev/exports/data_output ./data/output
```

## Known limitations / next steps

- The Airbnb 30-night Amsterdam regulation (see Revenue estimate above).
- The geo backfill does a linear scan over all polygons per row; fine at
  ~2,250 lookups, would need a spatial index at larger scale.
- No streaming ingestion (Level 4) -- not justified for two static,
  point-in-time exports; would revisit if the sources became live feeds.
- No dashboard/visualization (Level 2) was built; `gold_postcode_revenue`
  and `data/geo/amsterdam_areas.geojson` are ready to plug into one.
