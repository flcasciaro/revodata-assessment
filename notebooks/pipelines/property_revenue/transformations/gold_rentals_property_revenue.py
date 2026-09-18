# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Kamernet Property Revenue
# MAGIC Estimated annual revenue per Kamernet listing (monthly rent x 12, since a
# MAGIC long-term lease is assumed to be continuously occupied).

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.transformations.gold import rentals_property_revenue

# COMMAND ----------


@dp.materialized_view(
    name="gold_rentals_property_revenue",
    table_properties={"quality": "gold"},
    comment="Estimated annual revenue per Kamernet listing.",
)
def gold_rentals_property_revenue() -> DataFrame:
    """Compute per-property estimated annual revenue for Kamernet rentals."""
    return rentals_property_revenue(spark.read.table("silver_rentals"))
