"""Helpers for reading required Databricks pipeline configuration."""

from pyspark.sql import SparkSession


def require_conf(spark: SparkSession, key: str) -> str:
    """Read a required Spark configuration value, raising if it is unset.

    `spark.conf.get(key)` without a default returns `str | None`; pipeline
    notebooks need a definite value (and a clear failure) since these are
    passed straight into I/O paths and other required parameters.
    """
    value = spark.conf.get(key)
    if value is None:
        msg = f"Missing required pipeline configuration: {key}"
        raise ValueError(msg)
    return value
