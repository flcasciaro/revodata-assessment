# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Airbnb Property Revenue
# MAGIC Estimated annual revenue per Airbnb listing (nightly price x an assumed
# MAGIC number of occupied nights per year -- see `docs/pipeline.md` for why).

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.config import require_conf
from revodata_assessment.transformations.gold import airbnb_property_revenue

# COMMAND ----------

assumed_occupied_nights_per_year = int(
    require_conf(spark, "airbnb_assumed_occupied_nights_per_year")
)

# COMMAND ----------


@dp.table(
    name="gold_airbnb_property_revenue",
    table_properties={"quality": "gold"},
    comment="Estimated annual revenue per Airbnb listing.",
)
def gold_airbnb_property_revenue() -> DataFrame:
    """Compute per-property estimated annual revenue for Airbnb listings."""
    return airbnb_property_revenue(
        spark.read.table("silver_airbnb"),
        assumed_occupied_nights_per_year=assumed_occupied_nights_per_year,
    )
