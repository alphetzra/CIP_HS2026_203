"""Holiday data integration - holiday share per Grossregion and day.

1. Introduction

Holidays are defined per canton, but the spending data is only available
per Grossregion (7 regions). This script converts the cantonal holidays into
one number per region and day: the share of the region's population that
has a holiday on that day (0 = nobody, 1 = everybody).

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
   - only cantonal calendars are used (they already include national holidays),
   - class 4 (legally not recognized holiday) is dropped and treated as a
     normal working day (config.EXCLUDED_CLASS),
   - full holidays get the weight of their class (config.HOLIDAY_WEIGHTS):
     class 1 (official holiday) and 2 (on a par with Sundays) = 1.0,
     class 3 (half-holiday) = 0.5,
   - partial holidays get their population share from the website; if no
     share is given ("varies", "n.a."), it is set to 0 = nobody off
     (config.UNKNOWN_PARTIAL_SHARE),
   - if a canton has several holidays on the same day, the highest share
     is kept.
2. Add the canton's population of that year and its Grossregion
   (config.CANTON_TO_REGION).
3. Per region and day: people with a holiday (share x population, summed
   over the cantons) divided by the region's total population.

4. Notes

- Weighting by population: each canton's contribution to the regional share is
  proportional to its population size.
- Shares given as "< x %" are used as x % (upper bound).
- Partial holidays have no class on the website, so the class 4 filter can
  not be applied to them; they are included with their share.
"""

import pandas as pd
from scripts import config


def canton_off_share() -> pd.DataFrame:
    """Share of each canton's population that has the day off."""
    hol = pd.read_csv(config.CLEANED_HOLIDAYS, parse_dates=["date"])
    # cantonal calendars only (national rows would count twice)
    hol = hol.loc[hol["level"] == "canton"].copy()
    hol = hol.loc[~hol["holiday_class"].isin(config.EXCLUDED_CLASS)].copy()
    # full holidays: weight per holiday class
    hol["off_share"] = hol["holiday_class"].map(config.HOLIDAY_WEIGHTS)
    # partial holidays: population share from the website;
    # if the website gives no share = 0
    partial = hol["is_partial"]
    hol.loc[partial, "off_share"] = (hol.loc[partial, "canton_share"]
                                     .fillna(config.UNKNOWN_PARTIAL_SHARE))
    # several holidays on the same day in one canton -> keep highest share
    return hol.groupby(["date", "canton"], as_index=False)["off_share"].max()


def add_population(hol: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    """Add the canton's population of that year and its Grossregion."""
    hol["year"] = hol["date"].dt.year
    hol = hol.merge(pop, on=["canton", "year"], how="left")
    # every holiday row needs a population, otherwise the share would be wrong
    if hol["population"].isna().any():
        raise ValueError("Holiday rows without population (canton/year mismatch).")
    hol["region"] = hol["canton"].map(config.CANTON_TO_REGION)
    return hol


def region_share(hol: pd.DataFrame, pop: pd.DataFrame) -> pd.DataFrame:
    """Compute the share of population with holiday in each region"""
    # number of people with the day off per canton, summed per region
    hol["people_off"] = hol["off_share"] * hol["population"]
    people_off = hol.groupby(["date", "region"], as_index=False)["people_off"].sum()
    # total population per region and year
    pop = pop.assign(region=pop["canton"].map(config.CANTON_TO_REGION))
    region_pop = pop.groupby(["region", "year"], as_index=False)["population"].sum()
    people_off["year"] = people_off["date"].dt.year
    # validate: each region/year has exactly one population value
    share = people_off.merge(region_pop, on=["region", "year"], validate="many_to_one")
    share["holiday_share"] = (share["people_off"] / share["population"]).round(4)
    return share[["date", "region", "holiday_share"]]


def holiday_share_by_region() -> pd.DataFrame:
    """Run the steps in order: canton share -> population -> region share."""
    pop = pd.read_csv(config.CLEANED_POPULATION)
    hol = canton_off_share()
    hol = add_population(hol, pop)
    share = region_share(hol, pop)
    return share.sort_values(["date", "region"]).reset_index(drop=True)


def run() -> pd.DataFrame:
    """Compute the region holiday share and save it to data/processed."""
    df = holiday_share_by_region()
    output = config.REGION_HOLIDAY_SHARE
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"{len(df)} region/day holiday rows saved to {output}")
    return df


if __name__ == "__main__":
    run()