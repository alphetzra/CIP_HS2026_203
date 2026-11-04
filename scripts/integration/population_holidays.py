"""Holiday data integration - holiday share per Grossregion and day.

1. Introduction

Holidays are defined per canton, but the spending data is only available per Grossregion.
This script converts the cantonal holidays into one number per region and day: the share
of the region's population that has a holiday on that day (0 = nobody, 1 = everybody).

2. Data

-------------------------------------------------------------------------------------
| Input                                   | Output                                   |
|-----------------------------------------|------------------------------------------|
| data/processed/cleaned_holidays.csv     | data/processed/region_holiday_share.csv  |
| data/processed/cleaned_population.csv   |                                          |
-------------------------------------------------------------------------------------

Output columns: date, region, holiday_share (0-1).
Only region/days with at least one cantonal holiday are included.

3. Script description

1. Per canton and day: share of the canton's population that has the day off.
   - only cantonal calendars are used, since they already include national holidays.
   - class 4 (legally not recognized holiday) is dropped and treated as a normal working day.
   - full holidays get the weight of their class; partial holidays get their population share
     from the website; if no share is given, it is set to 0.
   - if a canton has several holidays on the same day, the highest share is kept.
2. Add the canton's population of that year and its Grossregion.
3. Per region and day: people with a holiday divided by the region's total population.

4. Notes

- Weighting by population: each canton's contribution to the regional share is
  proportional to its population size.
- Shares given as "< x %" are used as x % (considering the upper bound).
"""

import pandas as pd
from scripts import config


def canton_off_share() -> pd.DataFrame:
    """Share of each canton's population that has the day off."""
    hol = pd.read_csv(config.CLEANED_HOLIDAYS, parse_dates=["date"])
    hol = hol.loc[hol["level"] == "canton"].copy()
    hol = hol.loc[~hol["holiday_class"].isin(config.EXCLUDED_CLASS)].copy()
    hol["off_share"] = hol["holiday_class"].map(config.HOLIDAY_WEIGHTS)
    partial = hol["is_partial"]
    hol.loc[partial, "off_share"] = (hol.loc[partial, "canton_share"]
                                     .fillna(config.UNKNOWN_PARTIAL_SHARE))
    return hol.groupby(["date", "canton"], as_index=False)["off_share"].max()


def add_population(hol: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    """Add the canton's population of that year and its Grossregion."""
    hol["year"] = hol["date"].dt.year
    hol = hol.merge(pop, on=["canton", "year"], how="left")
    if hol["population"].isna().any():
        raise ValueError("Holiday rows without population (canton/year mismatch).")
    hol["region"] = hol["canton"].map(config.CANTON_TO_REGION)
    return hol


def region_share(hol: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    """Compute the share of population with holiday in each region"""
    hol["people_off"] = hol["off_share"] * hol["population"]
    people_off = hol.groupby(["date", "region"], as_index=False)["people_off"].sum()
    pop = pop.assign(region=pop["canton"].map(config.CANTON_TO_REGION))
    region_pop = pop.groupby(["region", "year"], as_index=False)["population"].sum()
    people_off["year"] = people_off["date"].dt.year
    # check: each region/year has exactly one population value
    share = people_off.merge(region_pop, on=["region", "year"], validate="many_to_one")
    share["holiday_share"] = (share["people_off"] / share["population"]).round(4)
    # outlier check: share is between 0 and 1
    if not share["holiday_share"].between(0, 1).all():
        raise ValueError("holiday_share outside 0-1.")
    return share[["date", "region", "holiday_share"]]


def holiday_share_by_region() -> pd.DataFrame:
    """Run the steps in order: canton share -> population -> region share."""
    pop = pd.read_csv(config.CLEANED_POPULATION)
    hol = canton_off_share()
    hol = add_population(hol, pop)
    share = region_share(hol, pop)
    return share.sort_values(["date", "region"]).reset_index(drop=True)


def get_holidays() -> pd.DataFrame:
    """Compute the region holiday share and save it to data/processed."""
    df = holiday_share_by_region()
    output = config.REGION_HOLIDAY_SHARE
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"{len(df)} region/day holiday rows saved to {output}")
    return df