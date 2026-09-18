# Databricks notebook source
# MAGIC %md
# MAGIC # Silver: Airbnb Listings
# MAGIC Cleans `bronze_airbnb`, backfills postal codes missing from the source via a
# MAGIC point-in-polygon lookup against `data/geo/post_codes.geojson` (Level 5),
# MAGIC then drops rows that fail the data quality expectations below.

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.config import require_conf
from revodata_assessment.transformations.airbnb import clean_airbnb

# COMMAND ----------

# A Databricks Workspace Files path, mounted identically on the driver and
# every executor, so `clean_airbnb`'s UDF can read it directly per worker
# process instead of parsing ~470 Shapely polygons on the driver and shipping
# them through the UDF's closure -- that broadcast was observed to
# intermittently fail to materialize on Databricks serverless compute (see
# `geo.make_postcode_lookup_udf`).
postcodes_geojson_path = require_conf(spark, "postcodes_geojson_path")

# COMMAND ----------

expectations = {
    "has_postcode4": "postcode4 IS NOT NULL",
    "has_positive_price": "nightly_price_eur > 0",
    "has_positive_accommodates": "accommodates > 0",
}

# COMMAND ----------


@dp.materialized_view(
    name="silver_airbnb",
    table_properties={"quality": "silver"},
    comment="Cleaned Airbnb listings with postal codes backfilled via point-in-polygon lookup.",
)
@dp.expect_all_or_drop(expectations)
def silver_airbnb() -> DataFrame:
    """Clean bronze Airbnb listings, backfilling missing postal codes from geo data."""
    return clean_airbnb(spark.read.table("bronze_airbnb"), postcodes_geojson_path)
