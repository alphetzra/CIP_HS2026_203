import pandas as pd
from scripts import config


def get_raw_events() -> pd.DataFrame | None:
    """Load the raw events data from local file.
        Returns:
            Raw events data or None if the file doesn't exist
        """
    if config.RAW_EVENTS.exists():
        return pd.read_csv(config.RAW_EVENTS)
    print(f"{config.RAW_EVENTS} is not existing, needs to start the scraping script.")
    return None

def get_events() -> pd.DataFrame | None:
    """Load the events data from local file.
        Returns:
            events data or None if the file doesn't exist
        """
    # TODO: Morteza currently it is not given that clean events exist please fix (check: spending/population)
    if config.CLEAN_EVENTS.exists():
        return pd.read_csv(config.CLEAN_EVENTS)
    print(f"{config.CLEAN_EVENTS} is not existing, needs to start the scraping script.")
    return None