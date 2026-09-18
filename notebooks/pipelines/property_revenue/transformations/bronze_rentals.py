# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze: Kamernet Rentals
# MAGIC Raw ingestion of the Kamernet rentals JSON export, no cleaning applied.

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.config import require_conf

# COMMAND ----------

rentals_path = require_conf(spark, "rentals_path")

# COMMAND ----------


@dp.materialized_view(
    name="bronze_rentals",
    table_properties={"quality": "bronze"},
    comment="Raw Kamernet rental listings, ingested as-is from the scraped JSON export.",
)
def bronze_rentals() -> DataFrame:
    """Ingest the raw Kamernet rentals JSON export.

    The export is a single JSON array rather than newline-delimited JSON,
    hence `multiLine`.
    """
    return spark.read.option("multiLine", "true").json(rentals_path)
