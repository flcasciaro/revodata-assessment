"""Pytest configuration file for PySpark testing."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from databricks.connect import DatabricksEnv, DatabricksSession
from pyspark.sql import SparkSession

_SRC_ROOT = Path(__file__).resolve().parent.parent / "src"

# Kept in sync with the `shapely` constraint in pyproject.toml's `dependencies`:
# the pandas UDF in `revodata_assessment.geo` needs it on the remote worker too.
_UDF_ENV = DatabricksEnv().withDependencies("shapely>=2.0.0")


@pytest.fixture(scope="session")
def spark() -> Generator[SparkSession, None, None]:
    """Fixture for a serverless DatabricksSession instance for testing.

    Pandas UDFs under test (see `revodata_assessment.geo`) call back into
    `revodata_assessment` from the remote worker, so the package is zipped
    and shipped to the serverless session as a pyfile artifact -- otherwise
    cloudpickle deserialization on the worker fails with `ModuleNotFoundError`
    since the package isn't installed on the remote cluster. `shapely`, a
    third-party dependency of that module, is declared via `DatabricksEnv`
    so it's installed into the remote UDF execution environment too.
    """
    spark_serverless_session = (
        DatabricksSession.builder.serverless(True).withEnvironment(_UDF_ENV).getOrCreate()
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = shutil.make_archive(
            str(Path(tmp_dir) / "revodata_assessment"), "zip", root_dir=_SRC_ROOT
        )
        # A bare Windows path (e.g. `C:\...`) is misparsed as URI scheme `c`, so
        # it must be passed as a proper `file://` URI instead.
        spark_serverless_session.addArtifacts(Path(archive_path).absolute().as_uri(), pyfile=True)
    yield spark_serverless_session
    spark_serverless_session.stop()
