"""Data integration -  daily table for Q2.

Combines the cleaned spending data with the regional holiday share. The result is
the table used for the Q2 analysis, with one row per date, Grossregion and spending
category.

Specifics:
- Left join on date and region, so every spending row is kept. Days without
  any holiday get holiday_share = 0.
- is_holiday is True if at least half of the region's population has the
  day off.
- weekday is converted from 0-6 to the day name as an ordered category.
- is_outlier, border_region and border_country are dropped because Q2 doesn't use them.
"""

import pandas as pd

from integration.population_holidays import get_population_holidays
from scripts import config
from spending.spending import get_spending


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the cleaned spending and the region holiday share.
        Returns:
            (spending, share): Spending without the columns not used in Q2,
            and the holiday share per date and region
        """
    spending = get_spending()
    if spending is None:
        raise FileNotFoundError("Cleaned spending missing, run the cleaning notebook first.")
    spending = spending.drop(columns=["is_outlier", "border_region", "border_country"])
    share = get_population_holidays()
    return spending, share


def merge_holidays(spending: pd.DataFrame, share: pd.DataFrame) -> pd.DataFrame:
    """Attach the holiday share to every spending row."""
    share["region"] = pd.Categorical(share["region"], categories=spending["region"].cat.categories)
    # left join: keep every spending row, also on days without holiday
    df = spending.merge(share, on=["date", "region"], how="left")
    df["holiday_share"] = df["holiday_share"].fillna(0.0)
    return df


def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Add the weekday name and the holiday flag.
        Args:
            df: Spending with holiday share; year, month, is_weekend and
                log_spending already come from the cleaning notebook
        Returns:
            DataFrame with weekday as ordered category and is_holiday
        """
    # the notebook stores the weekday as 0-6
    df["weekday"] = pd.Categorical(df["date"].dt.day_name(),
                                   categories=config.WEEKDAYS, ordered=True)
    # holiday if at least half of the region's population has the day off
    df["is_holiday"] = df["holiday_share"] >= config.HOLIDAY_THRESHOLD
    return df



def build_df_q2() -> pd.DataFrame:
    """Run the steps in order.
        Returns:
            Q2 table, sorted by date, region and category
        """
    spending, share = load_inputs()
    df = merge_holidays(spending, share)
    df = add_calendar(df)
    return df.sort_values(["date", "region", "category"]).reset_index(drop=True)


def get_build_df() -> pd.DataFrame:
    """Build the Q2 table and save it to data/processed/df_q2.parquet."""
    df = build_df_q2()
    print(f"Holiday rows (share >= {config.HOLIDAY_THRESHOLD}): {df['is_holiday'].sum()}")
    return df

