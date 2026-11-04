import pandas as pd

from .acquire import acquire_population
from .cleaning import cleaning_population
from scripts import config


def get_raw_population() -> pd.DataFrame | None:
    """Download the raw population data, if it doesn't already exist.
        Returns:
            Raw BFS population export
        """

    if config.POP_FILE.exists():
        df = pd.read_csv(config.POP_FILE)
    else:
        df = acquire_population()
    return df


def get_population() -> pd.DataFrame | None:
    """Return the cleaned population table.
           Returns:
               Cleaned population table"""

    df = get_raw_population()
    if df is None:
        return None
    df = cleaning_population(df)
    return df

