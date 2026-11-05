import pandas as pd

from scripts.Q2.holidays.preprocessing_cleaning import get_preprocessed_cleaned_holidays


def get_holidays() -> pd.DataFrame | None:
    """Return the cleaned holiday table."""

    return get_preprocessed_cleaned_holidays()

