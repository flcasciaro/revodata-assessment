"""Tests for the gold-layer revenue estimate and postcode comparison transformations."""

from pyspark.sql import DataFrame, Row, SparkSession

from revodata_assessment.transformations.gold import (
    airbnb_property_revenue,
    postcode_revenue,
    postcode_revenue_comparison,
    rentals_property_revenue,
)


def _silver_rentals(spark: SparkSession) -> DataFrame:
    return spark.createDataFrame(
        [
            Row(postcode4="1052", monthly_rent_eur=1000.0),
            Row(postcode4="1052", monthly_rent_eur=800.0),
            Row(postcode4="1053", monthly_rent_eur=1200.0),
        ]
    )


def _silver_airbnb(spark: SparkSession) -> DataFrame:
    return spark.createDataFrame(
        [
            Row(postcode4="1052", nightly_price_eur=100.0),
            Row(postcode4="1099", nightly_price_eur=250.0),
        ]
    )


def test_rentals_property_revenue_multiplies_rent_by_twelve(spark: SparkSession) -> None:
    """A long-term lease's annual revenue is twelve times its monthly rent."""
    result = rentals_property_revenue(_silver_rentals(spark)).collect()
    assert {row["estimated_annual_revenue_eur"] for row in result} == {12_000.0, 9_600.0, 14_400.0}


def test_airbnb_property_revenue_uses_assumed_occupied_nights(spark: SparkSession) -> None:
    """Annual revenue is the nightly price times the configured occupied-nights assumption."""
    result = airbnb_property_revenue(
        _silver_airbnb(spark), assumed_occupied_nights_per_year=100
    ).collect()
    assert {row["estimated_annual_revenue_eur"] for row in result} == {10_000.0, 25_000.0}


def test_postcode_revenue_aggregates_per_postcode4(spark: SparkSession) -> None:
    """Property-level revenue is averaged and summed per postcode4."""
    property_revenue = rentals_property_revenue(_silver_rentals(spark))
    result = {row["postcode4"]: row for row in postcode_revenue(property_revenue).collect()}

    assert result["1052"]["listing_count"] == 2
    assert result["1052"]["avg_estimated_annual_revenue_eur"] == 10_800.0
    assert result["1053"]["listing_count"] == 1


def test_postcode_revenue_comparison_flags_the_more_profitable_channel(spark: SparkSession) -> None:
    """Each postcode is labeled with whichever channel has the higher average revenue."""
    rentals_by_postcode = postcode_revenue(rentals_property_revenue(_silver_rentals(spark)))
    airbnb_by_postcode = postcode_revenue(airbnb_property_revenue(_silver_airbnb(spark)))

    result = {
        row["postcode4"]: row["more_profitable_channel"]
        for row in postcode_revenue_comparison(rentals_by_postcode, airbnb_by_postcode).collect()
    }

    # 1052 has both sources: airbnb's default 180-night assumption (100 * 180 = 18_000/yr)
    # beats the rental average (10_800/yr).
    assert result["1052"] == "airbnb"
    assert result["1053"] == "rental"  # rental-only postcode
    assert result["1099"] == "airbnb"  # airbnb-only postcode
