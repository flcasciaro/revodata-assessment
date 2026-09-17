"""Point-in-polygon postal code lookup used to backfill missing Airbnb postal codes.

This implements the Level 5 stretch goal: enrich Airbnb rows that have no
usable postal code by matching their (longitude, latitude) against the
`post_codes.geojson` PC4 (4-digit postal code area) boundaries.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import StringType
from pyspark.sql.udf import UserDefinedFunction
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry


@dataclass(frozen=True)
class PostcodePolygon:
    """A single postal code area polygon from the `post_codes.geojson` reference dataset."""

    pc4_code: str
    geometry: BaseGeometry


def load_postcode_polygons(geojson_path: str) -> list[PostcodePolygon]:
    """Load postal code polygons from a `post_codes.geojson`-style GeoJSON file.

    Each feature's `pc4_code` property carries the 4-digit postal code prefix
    (not the full 6-character code) for the area covered by its polygon.
    """
    with Path(geojson_path).open(encoding="utf-8") as geojson_file:
        geojson_data = json.load(geojson_file)
    return [
        PostcodePolygon(
            pc4_code=feature["properties"]["pc4_code"],
            geometry=shape(feature["geometry"]),
        )
        for feature in geojson_data["features"]
    ]


def find_pc4_by_point(
    longitude: float | None,
    latitude: float | None,
    polygons: list[PostcodePolygon],
) -> str | None:
    """Find the 4-digit postal code whose polygon contains the given coordinate.

    Returns None when the coordinate is missing or falls outside every known
    polygon, e.g. a listing just outside the reference dataset's coverage.
    """
    if longitude is None or latitude is None:
        return None
    point = Point(float(longitude), float(latitude))
    for polygon in polygons:
        if polygon.geometry.contains(point):
            return polygon.pc4_code
    return None


@lru_cache(maxsize=4)
def _load_postcode_polygons_on_worker(geojson_path: str) -> list[PostcodePolygon]:
    """Load and cache postal code polygons once per executor Python process.

    `geojson_path` is a Databricks Workspace Files path, mounted identically
    on the driver and every executor within a pipeline's cluster, so each
    worker can read the (22MB) reference file directly -- no broadcast
    involved. The `lru_cache` means repeated pandas UDF batches on the same
    worker reuse the parsed polygons instead of re-parsing the file every
    batch.
    """
    return load_postcode_polygons(geojson_path)


def make_postcode_lookup_udf(geojson_path: str) -> UserDefinedFunction:
    """Build a pandas UDF that backfills postal codes from longitude/latitude pairs.

    Takes the GeoJSON's path and loads/caches polygons lazily per worker
    process, rather than pre-building ~470 Shapely geometries on the driver
    and shipping them through the UDF's closure: a closure/broadcast that
    size was observed to intermittently fail to materialize on the executor
    on Databricks serverless compute (`FileNotFoundError` reading the
    broadcast block from local disk). Closing over a plain path string avoids
    that broadcast entirely.
    """

    @pandas_udf(StringType())  # ty: ignore[no-matching-overload] -- pandas_udf's overloaded stub doesn't match this valid usage
    def lookup_postcode(longitudes: pd.Series, latitudes: pd.Series) -> pd.Series:
        """Look up the 4-digit postal code for each longitude/latitude pair."""
        polygons = _load_postcode_polygons_on_worker(geojson_path)
        return pd.Series(
            [
                find_pc4_by_point(longitude, latitude, polygons)
                for longitude, latitude in zip(longitudes, latitudes, strict=True)
            ]
        )

    return lookup_postcode
