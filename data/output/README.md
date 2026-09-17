# Pipeline Output

Parquet exports of the `property-revenue-pipeline` gold tables
(`gold_rentals_property_revenue`, `gold_airbnb_property_revenue`,
`gold_rentals_postcode_revenue`, `gold_airbnb_postcode_revenue`,
`gold_postcode_revenue`), produced by a real deployed pipeline run against
Databricks serverless compute (`dev` target). Each subfolder is Spark's
standard single-partition Parquet output (`_SUCCESS` marker + one
`.snappy.parquet` data file). Regenerate by following
`docs/pipeline.md#exporting-to-dataoutput` after a fresh pipeline run.
