# Databricks notebook source
# MAGIC %md
# MAGIC ### Postcode Revenue Exploration
# MAGIC
# MAGIC Ad-hoc checks against the pipeline's gold tables: which postcodes look
# MAGIC most promising, and how many Airbnb rows needed a geo backfill.
# MAGIC
# MAGIC **Note**: This notebook is not executed as part of the pipeline.

# COMMAND ----------

from databricks.sdk.runtime import display, spark

# COMMAND ----------

# MAGIC %md
# MAGIC #### Top postcodes by more-profitable channel

# COMMAND ----------

display(
    spark.table("gold_postcode_revenue").orderBy(
        "more_profitable_channel",
        # Column.desc is built dynamically (pyspark.sql.column._unary_op) and lacks a
        # type stub, so ty misreads it as missing an argument.
        spark.table("gold_postcode_revenue")["airbnb_avg_estimated_annual_revenue_eur"].desc(),  # ty: ignore[missing-argument]
    )
)

# COMMAND ----------

# MAGIC %md
# MAGIC #### How many Airbnb listings needed a postal code backfill?

# COMMAND ----------

display(spark.table("silver_airbnb").groupBy("postcode_source").count())
