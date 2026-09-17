"""Silver-layer cleaning and postal code backfill for the Airbnb source.

As with `rentals.py`, row-level quality gates are declared as Lakeflow
expectations in the pipeline notebook, not here.
"""

import pyspark.sql.functions as F
from pyspark.sql import DataFrame

from revodata_assessment.cleaning import extract_postcode4
from revodata_assessment.geo import make_postcode_lookup_udf

_DEDUPLICATION_COLUMNS = [
    "postcode4",
    "latitude",
    "longitude",
    "room_type",
    "accommodates",
    "nightly_price_eur",
]


def clean_airbnb(df: DataFrame, postcodes_geojson_path: str) -> DataFrame:
    """Clean raw Airbnb listings and backfill postal codes missing from the source.

    Airbnb `zipcode` values arrive in three shapes: a full 6-character
    postal code (optionally wrapped in extra free text), a bare 4-digit
    code, or unusable/missing text. The first two are recovered with regex
    parsing (`extract_postcode4`); when no postal code can be parsed at all,
    this falls back to a point-in-polygon lookup against the
    `post_codes.geojson` PC4 boundaries using the listing's coordinates --
    the Level 5 backfill strategy. Exact duplicate listings (the raw export
    contains ~4% repeats) are also dropped here.

    `postcodes_geojson_path` must be readable from every executor, e.g. a
    Databricks Workspace Files path -- see `geo.make_postcode_lookup_udf`.
    """
    lookup_postcode = make_postcode_lookup_udf(postcodes_geojson_path)
    extract_postcode4_udf = F.udf(extract_postcode4, "string")

    parsed = (
        df.withColumn("latitude", F.col("latitude").cast("double"))
        .withColumn("longitude", F.col("longitude").cast("double"))
        .withColumn("postcode4_from_source", extract_postcode4_udf(F.col("zipcode")))
    )
    parsed = parsed.withColumn(
        "postcode4",
        F.coalesce(
            F.col("postcode4_from_source"),
            lookup_postcode(F.col("longitude"), F.col("latitude")),
        ),
    ).withColumn(
        "postcode_source",
        # Column.when is built dynamically (pyspark.sql.column._bin_op) and lacks a
        # type stub, so ty misreads it as missing an argument.
        F.when(F.col("postcode4_from_source").isNotNull(), F.lit("source"))  # ty: ignore[missing-argument]
        .when(F.col("postcode4").isNotNull(), F.lit("geo_backfill"))  # ty: ignore[missing-argument]
        .otherwise(F.lit("unresolved")),
    )

    return parsed.select(
        "postcode4",
        "postcode_source",
        "latitude",
        "longitude",
        F.col("room_type"),
        F.col("accommodates").cast("int").alias("accommodates"),
        F.col("bedrooms").cast("double").alias("bedrooms"),
        F.col("price").cast("double").alias("nightly_price_eur"),
        F.col("review_scores_value").cast("double").alias("review_scores_value"),
    ).dropDuplicates(_DEDUPLICATION_COLUMNS)
