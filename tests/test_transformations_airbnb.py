"""Tests for the Airbnb silver transformation, including the geo postal code backfill."""

import json
from collections.abc import Generator

import pytest
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat
from pyspark.sql import DataFrame, Row, SparkSession

from revodata_assessment.transformations.airbnb import clean_airbnb

# A single unit square at pc4 "1010", matching what `clean_airbnb` should
# backfill the missing-postcode row below to.
_TEST_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"pc4_code": "1010"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
        },
    ],
}

_COLUMNS = [
    "zipcode",
    "latitude",
    "longitude",
    "room_type",
    "accommodates",
    "bedrooms",
    "price",
    "review_scores_value",
]


@pytest.fixture(scope="module")
def postcodes_geojson_path() -> Generator[str, None, None]:
    """Upload the test postal code polygons to the workspace, returning their path.

    Mirrors `silver_airbnb`: `clean_airbnb` reads the GeoJSON directly from a
    workspace path on each executor (see `geo.make_postcode_lookup_udf`), so
    the fixture must live somewhere every executor can read it too -- there's
    no filesystem shared between this local test process and the remote
    serverless cluster otherwise.
    """
    workspace_client = WorkspaceClient()
    user_name = workspace_client.current_user.me().user_name
    workspace_path = f"/Workspace/Users/{user_name}/.tmp_test_postcodes.geojson"
    workspace_client.workspace.upload(
        workspace_path,
        json.dumps(_TEST_GEOJSON).encode("utf-8"),
        format=ImportFormat.AUTO,
        overwrite=True,
    )
    try:
        yield workspace_path
    finally:
        workspace_client.workspace.delete(workspace_path)


def _bronze_airbnb(spark: SparkSession) -> DataFrame:
    # Row.__new__'s stub declares `*args: str`, but Row accepts any value at runtime;
    # the `None`s below (testing missing/unparsable values) trip ty's stricter check.
    rows = [
        # Full 6-character postal code: used as-is.
        Row("1052 AB", "0.9", "0.9", "Entire home/apt", "4", "2.0", "130", "100.0"),
        # Bare 4-digit postal code: used as-is.
        Row("1053", "0.8", "0.8", "Private room", "2", "1.0", "80", "90.0"),
        # Missing postal code but valid coordinates: backfilled via the polygon lookup.
        Row(None, "0.5", "0.5", "Private room", "2", "1.0", "59", "100.0"),  # ty: ignore[invalid-argument-type]
        # Unparsable postal code and coordinates outside all known polygons.
        Row("....", "5.0", "5.0", "Shared room", "1", "1.0", "40", None),  # ty: ignore[invalid-argument-type]
        # Exact duplicate of the first row: should be deduplicated away.
        Row("1052 AB", "0.9", "0.9", "Entire home/apt", "4", "2.0", "130", "100.0"),
    ]
    return spark.createDataFrame(rows, schema=_COLUMNS)


def test_clean_airbnb_deduplicates_exact_repeats(
    spark: SparkSession, postcodes_geojson_path: str
) -> None:
    """The duplicated listing is collapsed into a single row."""
    result = clean_airbnb(_bronze_airbnb(spark), postcodes_geojson_path)
    assert result.count() == 4


def test_clean_airbnb_keeps_source_postal_codes(
    spark: SparkSession, postcodes_geojson_path: str
) -> None:
    """A 6-character or bare 4-digit source postal code is used without a geo lookup."""
    result = {
        row["nightly_price_eur"]: (row["postcode4"], row["postcode_source"])
        for row in clean_airbnb(_bronze_airbnb(spark), postcodes_geojson_path).collect()
    }
    assert result[130.0] == ("1052", "source")
    assert result[80.0] == ("1053", "source")


def test_clean_airbnb_backfills_missing_postcode_from_coordinates(
    spark: SparkSession, postcodes_geojson_path: str
) -> None:
    """A missing postal code is backfilled from the point-in-polygon geo lookup."""
    result = {
        row["nightly_price_eur"]: (row["postcode4"], row["postcode_source"])
        for row in clean_airbnb(_bronze_airbnb(spark), postcodes_geojson_path).collect()
    }
    assert result[59.0] == ("1010", "geo_backfill")


def test_clean_airbnb_leaves_unresolvable_rows_null(
    spark: SparkSession, postcodes_geojson_path: str
) -> None:
    """A row with no parsable postal code and coordinates outside every polygon stays null."""
    result = {
        row["nightly_price_eur"]: (row["postcode4"], row["postcode_source"])
        for row in clean_airbnb(_bronze_airbnb(spark), postcodes_geojson_path).collect()
    }
    assert result[40.0] == (None, "unresolved")
