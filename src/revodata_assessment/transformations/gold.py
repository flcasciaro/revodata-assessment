"""Gold-layer revenue estimates, per property and per postal code.

Neither source dataset includes booking history, so "revenue" here is a
simplifying, documented estimate rather than an observed figure:

- Kamernet (long-term lease): assumed continuously occupied, so annual
  revenue is just the monthly rent times twelve.
- Airbnb (short-term): annual revenue is the nightly price times an assumed
  number of occupied nights per year. This intentionally ignores Amsterdam's
  30-night regulatory cap on entire-home short-term rentals -- ignoring
  legal caps overstates Airbnb revenue for entire homes and unfairly favors
  it over Kamernet, so it is the natural next refinement rather than the
  granularity choice this module makes today.
"""

import pyspark.sql.functions as F
from pyspark.sql import DataFrame

DEFAULT_ASSUMED_OCCUPIED_NIGHTS_PER_YEAR = 180
MONTHS_PER_YEAR = 12
POSTCODE_COLUMN = "postcode4"


def rentals_property_revenue(silver_rentals: DataFrame) -> DataFrame:
    """Estimate potential annual revenue per Kamernet listing."""
    return silver_rentals.withColumn(
        "estimated_annual_revenue_eur",
        F.col("monthly_rent_eur") * F.lit(MONTHS_PER_YEAR),
    )


def airbnb_property_revenue(
    silver_airbnb: DataFrame,
    assumed_occupied_nights_per_year: int = DEFAULT_ASSUMED_OCCUPIED_NIGHTS_PER_YEAR,
) -> DataFrame:
    """Estimate potential annual revenue per Airbnb listing."""
    return silver_airbnb.withColumn(
        "estimated_annual_revenue_eur",
        F.col("nightly_price_eur") * F.lit(assumed_occupied_nights_per_year),
    )


def postcode_revenue(property_revenue: DataFrame) -> DataFrame:
    """Aggregate property-level revenue estimates up to postcode4 level."""
    return property_revenue.groupBy(POSTCODE_COLUMN).agg(
        F.count("*").alias("listing_count"),
        F.round(F.avg("estimated_annual_revenue_eur"), 2).alias("avg_estimated_annual_revenue_eur"),
        F.round(F.sum("estimated_annual_revenue_eur"), 2).alias(
            "total_estimated_annual_revenue_eur"
        ),
    )


def postcode_revenue_comparison(
    rentals_postcode_revenue: DataFrame,
    airbnb_postcode_revenue: DataFrame,
) -> DataFrame:
    """Join Kamernet and Airbnb per-postcode revenue estimates for a side-by-side comparison.

    This is the table that answers the assessment's core question: for a
    given Amsterdam postcode4, is a long-term Kamernet lease or a
    short-term Airbnb listing the more profitable way to rent out a
    property? A postcode with listings on only one side is still reported,
    since that itself is a useful investment-potential signal.
    """
    rentals = rentals_postcode_revenue.select(
        POSTCODE_COLUMN,
        F.col("listing_count").alias("rental_listing_count"),
        F.col("avg_estimated_annual_revenue_eur").alias("rental_avg_estimated_annual_revenue_eur"),
    )
    airbnb = airbnb_postcode_revenue.select(
        POSTCODE_COLUMN,
        F.col("listing_count").alias("airbnb_listing_count"),
        F.col("avg_estimated_annual_revenue_eur").alias("airbnb_avg_estimated_annual_revenue_eur"),
    )
    rental_revenue_col = F.col("rental_avg_estimated_annual_revenue_eur")
    airbnb_revenue_col = F.col("airbnb_avg_estimated_annual_revenue_eur")

    return rentals.join(airbnb, on=POSTCODE_COLUMN, how="full").withColumn(
        "more_profitable_channel",
        # Column.when is built dynamically (pyspark.sql.column._bin_op) and lacks a
        # type stub, so ty misreads it as missing an argument.
        F.when(airbnb_revenue_col.isNull(), F.lit("rental"))  # ty: ignore[missing-argument]
        .when(rental_revenue_col.isNull(), F.lit("airbnb"))  # ty: ignore[missing-argument]
        .when(airbnb_revenue_col > rental_revenue_col, F.lit("airbnb"))
        .otherwise(F.lit("rental")),
    )
