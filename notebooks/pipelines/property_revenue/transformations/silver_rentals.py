# Databricks notebook source
# MAGIC %md
# MAGIC # Silver: Kamernet Rentals
# MAGIC Cleans, types and scopes `bronze_rentals`, then drops rows that fail the
# MAGIC data quality expectations below.

# COMMAND ----------

from databricks.sdk.runtime import spark
from pyspark import pipelines as dp
from pyspark.sql import DataFrame

from revodata_assessment.config import require_conf
from revodata_assessment.transformations.rentals import clean_rentals

# COMMAND ----------

amsterdam_city = require_conf(spark, "amsterdam_city")

# COMMAND ----------

expectations = {
    "has_postcode4": "postcode4 IS NOT NULL",
    "has_plausible_rent": "monthly_rent_eur > 50",
    "has_positive_area": "area_sqm > 0",
}

# COMMAND ----------


@dp.table(
    name="silver_rentals",
    table_properties={"quality": "silver"},
    comment="Cleaned, city-scoped Kamernet rentals with parsed rent/area and a derived postcode4.",
)
@dp.expect_all_or_drop(expectations)
def silver_rentals() -> DataFrame:
    """Clean bronze Kamernet rentals into a typed, quality-checked silver table."""
    return clean_rentals(spark.read.table("bronze_rentals"), city=amsterdam_city)
