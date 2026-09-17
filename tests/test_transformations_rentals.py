"""Tests for the Kamernet rentals silver transformation."""

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    ArrayType,
    StringType,
    StructField,
    StructType,
)

from revodata_assessment.transformations.rentals import clean_rentals

_BRONZE_RENTALS_SCHEMA = StructType(
    [
        StructField("_id", ArrayType(StringType()), nullable=True),
        StructField("city", StringType(), nullable=True),
        StructField("propertyType", StringType(), nullable=True),
        StructField("postalCode", StringType(), nullable=True),
        StructField("rent", StringType(), nullable=True),
        StructField("areaSqm", StringType(), nullable=True),
        StructField("latitude", StringType(), nullable=True),
        StructField("longitude", StringType(), nullable=True),
        StructField("furnish", StringType(), nullable=True),
        StructField("roommates", StringType(), nullable=True),
    ]
)


def _bronze_rentals(spark: SparkSession) -> DataFrame:
    # Rows are built as dicts, not `Row(**kwargs)`, because PySpark silently
    # reorders keyword-constructed Row fields alphabetically -- which would
    # misalign against `_BRONZE_RENTALS_SCHEMA`'s declared column order.
    rows = [
        {
            "_id": ["abc123"],
            "city": "Amsterdam",
            "propertyType": "Room",
            "postalCode": "1052ab",
            "rent": "€ 950,-  Utilities incl.",
            "areaSqm": "14 m2",
            "latitude": "52.37302064",
            "longitude": "4.868460923",
            "furnish": "Furnished",
            "roommates": "3",
        },
        {
            "_id": ["def456"],
            "city": "Rotterdam",
            "propertyType": "Room",
            "postalCode": "3074HN",
            "rent": "€ 500,-",
            "areaSqm": "14 m2",
            "latitude": "51.8966010000",
            "longitude": "4.5149930000",
            "furnish": "Unfurnished",
            "roommates": "5",
        },
    ]
    return spark.createDataFrame(rows, schema=_BRONZE_RENTALS_SCHEMA)


def test_clean_rentals_scopes_to_city(spark: SparkSession) -> None:
    """Only listings in the requested city survive, e.g. the Rotterdam row is dropped."""
    result = clean_rentals(_bronze_rentals(spark), city="Amsterdam").collect()
    assert len(result) == 1
    assert result[0]["city"] == "Amsterdam"


def test_clean_rentals_parses_and_derives_fields(spark: SparkSession) -> None:
    """Rent, area and postal code fields are parsed, cast and derived correctly."""
    result = clean_rentals(_bronze_rentals(spark), city="Amsterdam").collect()[0]

    assert result["rental_id"] == "abc123"
    assert result["postal_code"] == "1052AB"
    assert result["postcode4"] == "1052"
    assert result["monthly_rent_eur"] == 950.0
    assert result["area_sqm"] == 14.0
    assert result["roommates"] == 3
