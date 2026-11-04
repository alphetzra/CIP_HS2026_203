"""Holiday and population data integration - holiday share per Grossregion and day.

Holidays are defined per canton, but the spending data is only available per Grossregion.
This script converts the cantonal holidays into one number per region and day: the share
of the region's population that has a holiday on that day (0 = nobody, 1 = everybody).


Holidays are defined per canton, but the spending data is only available per
Grossregion. This file converts the cantonal holidays into one number per
region and day using the share of the region's population that has the day off
(0 = nobody, 1 = everybody).

Specifics:
- Only cantonal calendars are used, since they already include the national
  holidays.
- Class 4 (not legally recognized holiday) is treated as normal working days.
- Full holidays get the weight of their class; partial holidays get the population
  share from the website or 0 if none is given. Shares given as "< x %" are used as
  x % (upper bound).
- If a canton has several holidays on the same day, the highest share is kept.
- Each canton counts in proportion to its population in that year.
"""

import pandas as pd

from holidays.holidays import get_holidays
from population.population import get_population
from scripts import config


def canton_off_share() -> pd.DataFrame:
    """Compute share of each canton's population that has the day off.
        Returns:
            DataFrame with date, canton and off_share (0-1), one row per
            canton and holiday date
    """

    hol = get_holidays()
    hol = hol.loc[hol["level"] == "canton"].copy()
    hol = hol.loc[~hol["holiday_class"].isin(config.EXCLUDED_CLASS)].copy()
    hol["off_share"] = hol["holiday_class"].map(config.HOLIDAY_WEIGHTS)
    partial = hol["is_partial"]
    hol.loc[partial, "off_share"] = (hol.loc[partial, "canton_share"]
                                     .fillna(config.UNKNOWN_PARTIAL_SHARE))
    return hol.groupby(["date", "canton"], as_index=False)["off_share"].max()


def add_population(hol: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    """Add the canton's population of that year and its Grossregion.
        Args:
            hol: Output of canton_off_share()
            pop: Cleaned population table
        Returns:
            hol with year, population and region added
        Raises:
            ValueError: If a canton/year has no population
        """

    hol["year"] = hol["date"].dt.year
    hol = hol.merge(pop, on=["canton", "year"], how="left")
    if hol["population"].isna().any():
        raise ValueError("Holiday rows without population (canton/year mismatch).")
    hol["region"] = hol["canton"].map(config.CANTON_TO_REGION)
    return hol


def region_share(hol: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    """Compute the share of population with day off in each region.
        Args:
            hol: Output of add_population()
            pop: Cleaned population table, used for the region totals
        Returns:
            DataFrame with date, region and holiday_share
        Raises:
            ValueError: If a share lies outside 0-1
        """

    hol["people_off"] = hol["off_share"] * hol["population"]
    people_off = hol.groupby(["date", "region"], as_index=False)["people_off"].sum()
    pop = pop.assign(region=pop["canton"].map(config.CANTON_TO_REGION))
    region_pop = pop.groupby(["region", "year"], as_index=False)["population"].sum()
    # population is only available per year, so add the year to merge on
    people_off["year"] = people_off["date"].dt.year
    # check: each region/year has exactly one population value
    share = people_off.merge(region_pop, on=["region", "year"], validate="many_to_one")
    share["holiday_share"] = (share["people_off"] / share["population"]).round(4)
    # outlier check: share is between 0 and 1
    if not share["holiday_share"].between(0, 1).all():
        raise ValueError("holiday_share outside 0-1.")
    return share[["date", "region", "holiday_share"]]


def holiday_share_by_region() -> pd.DataFrame:
    """Run the steps in order: canton share -> population -> region share.
       Returns:
            Holiday share per date and region, sorted by date and region
    """
    pop = get_population()
    hol = canton_off_share()
    hol = add_population(hol, pop)
    share = region_share(hol, pop)
    share["date"] = pd.to_datetime(share["date"])
    return share.sort_values(["date", "region"]).reset_index(drop=True)


def get_population_holidays() -> pd.DataFrame:
    """Return the holiday share per Grossregion and day.
        Returns:
            Holiday share table, see holiday_share_by_region()
        """

    df = holiday_share_by_region()
    return df