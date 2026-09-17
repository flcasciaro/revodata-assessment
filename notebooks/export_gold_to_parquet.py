# Databricks notebook source
# MAGIC %md
# MAGIC # Export Gold Tables to Parquet
# MAGIC
# MAGIC A one-off, manually-run notebook (not part of the scheduled pipeline) that
# MAGIC writes each gold table out as Parquet under a Unity Catalog Volume, so it
# MAGIC can be downloaded into the repository's `./data/output` for the assessment
# MAGIC deliverable. A Volume is used rather than a `/Workspace/...` path because
# MAGIC Workspace Files don't support Spark's distributed writes (`Mkdirs failed`).
# MAGIC See `docs/pipeline.md#exporting-to-dataoutput` for the `databricks fs cp`
# MAGIC command used to pull the files down locally after running this notebook.
# MAGIC
# MAGIC A gold Delta table is the pipeline's real, governed output; this export is
# MAGIC a snapshot for review purposes, not something the pipeline itself should
# MAGIC do on every scheduled run.

# COMMAND ----------

from databricks.sdk.runtime import dbutils, spark

# COMMAND ----------

dbutils.widgets.text("schema", "revodata_assessment_dev")
dbutils.widgets.text(
    "export_path", "/Volumes/workspace/revodata_assessment_dev/exports/data_output"
)
schema = dbutils.widgets.get("schema")
export_path = dbutils.widgets.get("export_path")

# COMMAND ----------

gold_tables = [
    "gold_rentals_property_revenue",
    "gold_airbnb_property_revenue",
    "gold_rentals_postcode_revenue",
    "gold_airbnb_postcode_revenue",
    "gold_postcode_revenue",
]

for table in gold_tables:
    (
        spark.table(f"{schema}.{table}")
        .coalesce(1)
        .write.mode("overwrite")
        .parquet(f"{export_path}/{table}")
    )

print(f"Exported {len(gold_tables)} gold tables to {export_path}")
