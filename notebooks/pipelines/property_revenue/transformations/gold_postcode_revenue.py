# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Postcode Revenue Comparison
# MAGIC Joins the Kamernet and Airbnb postcode4 gold tables side-by-side and flags
# MAGIC which channel is more profitable in each postcode -- the table that
# MAGIC answers the assessment's investment-potential question.

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.transformations.gold import postcode_revenue_comparison

# COMMAND ----------


@dp.table(
    name="gold_postcode_revenue",
    table_properties={"quality": "gold"},
    comment="Per-postcode4 comparison of Kamernet vs. Airbnb estimated annual revenue.",
)
def gold_postcode_revenue() -> DataFrame:
    """Compare estimated Kamernet and Airbnb revenue per postcode4."""
    return postcode_revenue_comparison(
        spark.read.table("gold_rentals_postcode_revenue"),
        spark.read.table("gold_airbnb_postcode_revenue"),
    )
