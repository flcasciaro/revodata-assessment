# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Airbnb Postcode Revenue
# MAGIC `gold_airbnb_property_revenue` aggregated to postcode4 level.

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.transformations.gold import postcode_revenue

# COMMAND ----------


@dp.materialized_view(
    name="gold_airbnb_postcode_revenue",
    table_properties={"quality": "gold"},
    comment="Airbnb listing count and estimated annual revenue per postcode4.",
)
def gold_airbnb_postcode_revenue() -> DataFrame:
    """Aggregate Airbnb property revenue estimates to postcode4 level."""
    return postcode_revenue(spark.read.table("gold_airbnb_property_revenue"))
