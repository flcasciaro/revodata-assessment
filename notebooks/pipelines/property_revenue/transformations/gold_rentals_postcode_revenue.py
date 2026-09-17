# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Kamernet Postcode Revenue
# MAGIC `gold_rentals_property_revenue` aggregated to postcode4 level.

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.transformations.gold import postcode_revenue

# COMMAND ----------


@dp.table(
    name="gold_rentals_postcode_revenue",
    table_properties={"quality": "gold"},
    comment="Kamernet listing count and estimated annual revenue per postcode4.",
)
def gold_rentals_postcode_revenue() -> DataFrame:
    """Aggregate Kamernet property revenue estimates to postcode4 level."""
    return postcode_revenue(spark.read.table("gold_rentals_property_revenue"))
