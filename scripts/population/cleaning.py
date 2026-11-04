"""Population data cleaning.

The BFS population export is reduced to one row per canton and year with the three columns
that are needed: canton, year and population.

Specifics:
- The canton number is translated into the canton abbreviation,
  so the table can be joined with the holiday data.
- The checks raise an error instead of only printing a warning, so the
  pipeline stops if the export is incomplete.
"""

from pathlib import Path
import pandas as pd
from narwhals import DataFrame

from scripts import config


def cleaning_population(df: DataFrame) -> pd.DataFrame:
    """Clean the population export and save it to data/processed."""

    output = pd.DataFrame({"canton": df["KANT"].map(config.CANTON_NO),
                           "year": df["TIME_PERIOD"],
                           "population": df["OBS_VALUE"]})

    na_counts = output.isna().sum()
    if na_counts.sum() > 0:
        raise ValueError(f"Missing values:\n{na_counts[na_counts > 0]}")
    if output.duplicated(["canton", "year"]).any():
        raise ValueError("Duplicate canton/year rows.")

    if len(output) != len(config.CANTONS) * len(config.YEARS):
        raise ValueError("Missing canton/year combinations.")
    print("No missing values or duplicates, and all canton/year combinations.")

    df = output.sort_values(["year", "canton"]).reset_index(drop=True)
    return df
