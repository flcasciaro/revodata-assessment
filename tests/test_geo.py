"""Unit tests for the point-in-polygon postal code backfill in `revodata_assessment.geo`."""

import json
from pathlib import Path

from shapely.geometry import Polygon

from revodata_assessment.geo import PostcodePolygon, find_pc4_by_point, load_postcode_polygons

# Two adjacent unit squares, used instead of the real ~470-polygon dataset so
# these tests stay fast and their expected results are obvious by inspection.
_POLYGONS = [
    PostcodePolygon(pc4_code="1000", geometry=Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])),
    PostcodePolygon(pc4_code="1001", geometry=Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])),
]


def test_find_pc4_by_point_inside_first_polygon() -> None:
    """Matches a coordinate to the postal code of the polygon that contains it."""
    assert find_pc4_by_point(longitude=0.5, latitude=0.5, polygons=_POLYGONS) == "1000"


def test_find_pc4_by_point_inside_second_polygon() -> None:
    """Matches a coordinate against every polygon, not just the first one checked."""
    assert find_pc4_by_point(longitude=1.5, latitude=0.5, polygons=_POLYGONS) == "1001"


def test_find_pc4_by_point_outside_all_polygons() -> None:
    """Returns None when the coordinate falls outside every known polygon."""
    assert find_pc4_by_point(longitude=5.0, latitude=5.0, polygons=_POLYGONS) is None


def test_find_pc4_by_point_missing_coordinate() -> None:
    """Returns None when either coordinate is missing, rather than raising."""
    assert find_pc4_by_point(longitude=None, latitude=0.5, polygons=_POLYGONS) is None
    assert find_pc4_by_point(longitude=0.5, latitude=None, polygons=_POLYGONS) is None


def test_load_postcode_polygons(tmp_path: Path) -> None:
    """Loads polygons and their pc4_code from a GeoJSON file, matching the reference format."""
    geojson_path = tmp_path / "post_codes.geojson"
    geojson_path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"pc4_code": "1052"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    polygons = load_postcode_polygons(str(geojson_path))

    assert len(polygons) == 1
    assert polygons[0].pc4_code == "1052"
    assert polygons[0].geometry.contains(polygons[0].geometry.centroid)
