"""Silver-layer cleaning for the Kamernet rentals source.

Row-level quality gates (e.g. dropping rows with no usable postal code) are
declared as Lakeflow expectations in the pipeline notebook that calls
`clean_rentals`, not here -- this module only parses, types and scopes the
data so those expectations stay visible in the pipeline's data quality UI.
"""

import pyspark.sql.functions as F
from pyspark.sql import DataFrame

from revodata_assessment.cleaning import extract_postcode4, parse_area_sqm, parse_currency

AMSTERDAM_CITY = "Amsterdam"


def clean_rentals(df: DataFrame, city: str = AMSTERDAM_CITY) -> DataFrame:
    """Clean raw Kamernet listings into a typed, city-scoped silver dataset.

    Kamernet's `rent` and `areaSqm` fields are scraped as free-text strings
    (e.g. "€ 950,-  Utilities incl.", "14 m2"), and several fields are
    wrapped in single-element arrays by the scraper, so this flattens,
    parses and casts them into their real types. The source dataset spans
    every Dutch city; scoping to `city` narrows it to the assessment's
    Amsterdam investment scenario, matching the Airbnb source.
    """
    parse_currency_udf = F.udf(parse_currency, "double")
    parse_area_sqm_udf = F.udf(parse_area_sqm, "double")
    extract_postcode4_udf = F.udf(extract_postcode4, "string")

    return df.filter(F.col("city") == city).select(
        F.element_at(F.col("_id"), 1).alias("rental_id"),
        F.col("city"),
        F.col("propertyType").alias("property_type"),
        F.upper(F.trim(F.col("postalCode"))).alias("postal_code"),
        extract_postcode4_udf(F.col("postalCode")).alias("postcode4"),
        parse_currency_udf(F.col("rent")).alias("monthly_rent_eur"),
        parse_area_sqm_udf(F.col("areaSqm")).alias("area_sqm"),
        F.col("latitude").cast("double").alias("latitude"),
        F.col("longitude").cast("double").alias("longitude"),
        F.col("furnish"),
        F.col("roommates").cast("int").alias("roommates"),
    )
