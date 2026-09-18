# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze: Airbnb Listings
# MAGIC Raw ingestion of the Airbnb CSV export, no cleaning applied.

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.config import require_conf

# COMMAND ----------

airbnb_path = require_conf(spark, "airbnb_path")

# COMMAND ----------


@dp.materialized_view(
    name="bronze_airbnb",
    table_properties={"quality": "bronze"},
    comment="Raw Airbnb listings, ingested as-is from the scraped CSV export.",
)
def bronze_airbnb() -> DataFrame:
    """Ingest the raw Airbnb CSV export."""
    return spark.read.option("header", "true").option("inferSchema", "true").csv(airbnb_path)
