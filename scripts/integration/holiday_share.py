"""Convert canton holidays into a holiday share per Grossregion and day."""

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