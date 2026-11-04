import pandas as pd
from scripts import config


def get_raw_spending() -> pd.DataFrame | None:
    """Load the raw spending data from local file.
        Returns:
            Raw spending data or None if the file doesn't exist
        """

    if config.RAW_SPENDING.exists():
        return pd.read_parquet(config.RAW_SPENDING)
    print(f"{config.RAW_SPENDING} is not existing, needs to start the scraping script.")
    return None

def get_spending() -> pd.DataFrame | None:
    """Return the cleaned spending table.
            Returns:
                Cleaned spending table or None if the raw file is missing"""

    if config.CLEAN_SPENDING.exists():
            return pd.read_parquet(config.CLEAN_SPENDING)
    print(f"{config.CLEAN_SPENDING} not found. Run the spending cleaning notebook first.")
    return None