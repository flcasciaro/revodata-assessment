# property_revenue

This folder defines the `property-revenue-pipeline` Lakeflow Declarative
Pipeline: a medallion (bronze/silver/gold) pipeline that ingests Kamernet
rentals and Airbnb listings, cleans them, backfills missing Airbnb postal
codes from geo data, and estimates potential rental revenue per property and
per postal code.

- `transformations`: one dataset definition per file, run in dependency
  order by the Lakeflow Declarative Pipelines runtime:
  - `bronze_rentals`, `bronze_airbnb` -- raw ingestion.
  - `silver_rentals`, `silver_airbnb` -- cleaned, typed, quality-checked
    (`@dp.expect_all_or_drop`) data. `silver_airbnb` also backfills postal
    codes missing from the source via a point-in-polygon lookup against
    `data/geo/post_codes.geojson`.
  - `gold_rentals_property_revenue`, `gold_airbnb_property_revenue` --
    estimated annual revenue per listing.
  - `gold_rentals_postcode_revenue`, `gold_airbnb_postcode_revenue` --
    the above aggregated to postcode4.
  - `gold_postcode_revenue` -- the two postcode4 aggregates joined
    side-by-side, with a `more_profitable_channel` column. This is the
    table that answers the assessment's core question.
- `explorations`: ad-hoc notebooks used to sanity-check the gold tables.
  Not executed as part of the pipeline.

See `../../../docs/pipeline.md` for the design rationale (why Amsterdam-only
scoping, why postcode4, the revenue assumptions, and the geo backfill
approach) rather than a restatement of the code here.
