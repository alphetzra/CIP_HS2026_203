import pandas as pd
from scripts import config


def get_raw_exchange() -> pd.DataFrame | None:
    """Load the raw exchange data from local file.
        Returns:
            Raw exchange data or None if the file doesn't exist
        """

    if config.RAW_EXCHANGE.exists():
        return pd.read_parquet(config.RAW_EXCHANGE)
    print(f"{config.RAW_EXCHANGE} is not existing, needs to start the scraping script.")
    return None

