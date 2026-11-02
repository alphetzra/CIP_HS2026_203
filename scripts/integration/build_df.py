"""Data integration - build daily table for Q2.

1. Introduction

Combines the cleaned spending data with the regional holiday share and adds
calendar variables. The result is the table used for the Q2 analysis:
one row per date, Grossregion and spending category.

2. Data

------------------------------------------------------------------------------
| Input                                    | Output                          |
|------------------------------------------|---------------------------------|
| data/processed/cleaned_spending.parquet  | data/processed/df_q2.parquet    |
| data/processed/region_holiday_share.csv  |                                 |
-----------------------------------------------------------------------------

Added columns:
- holiday_share: share of the region's population with a holiday (0-1)
- year, month, weekday, is_weekend: derived from the date
- is_holiday:    True if holiday_share >= 0.5, i.e. at least half of the
                 region's population has the day off (config.HOLIDAY_THRESHOLD)
- log_spending:  natural log of spending

3. Script description

1. Read the cleaned spending and the region holiday share.
2. Left join the holiday share on date and region; days without any holiday
   get holiday_share = 0.
3. Add calendar columns from the date.
4. Add the log of spending.
5. Sort and save as parquet.

4. Notes

- Left join: all spending rows are kept.
- Log spending is used so that differences can be read as percentage changes,
  independent of the spending level of a category.
"""

import numpy as np
import pandas as pd
from scripts import config

def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the cleaned spending and the region holiday share."""
    spending = pd.read_parquet(config.CLEANED_SPENDING)
    share = pd.read_csv(config.REGION_HOLIDAY_SHARE, parse_dates=["date"])
    return spending, share


def merge_holidays(spending: pd.DataFrame, share: pd.DataFrame) -> pd.DataFrame:
    """Attach the holiday share to every spending row."""
    share["region"] = pd.Categorical(share["region"], categories=spending["region"].cat.categories)
    # left join: keep every spending row, also on days without holiday
    df = spending.merge(share, on=["date", "region"], how="left")
    df["holiday_share"] = df["holiday_share"].fillna(0.0)
    return df


def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar columns derived from the date."""
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["weekday"] = pd.Categorical(df["date"].dt.day_name(),
                                   categories=config.WEEKDAYS, ordered=True)
    df["is_weekend"] = df["date"].dt.day_of_week >= 5
    # holiday if at least half of the region's population has the day off
    df["is_holiday"] = df["holiday_share"] >= config.HOLIDAY_THRESHOLD
    return df


def add_log_value(df: pd.DataFrame) -> pd.DataFrame:
    """Log of spending, so regression coefficients read as percentage changes."""
    # safeguard: log is only defined for values > 0 (the data has no zero or
    # negative spending
    df["log_spending"] = np.log(df["spending"].where(df["spending"] > 0))
    return df


def build_df_q2() -> pd.DataFrame:
    """Run the steps in order: load -> merge -> calendar -> log."""
    spending, share = load_inputs()
    df = merge_holidays(spending, share)
    df = add_calendar(df)
    df = add_log_value(df)
    return df.sort_values(["date", "region", "category"]).reset_index(drop=True)


def run() -> pd.DataFrame:
    """Build the Q2 table and save it to data/processed/df_q2.parquet."""
    df = build_df_q2()
    output = config.DF_Q2
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    print(f"{len(df)} rows saved to {output}")
    print(f"Holiday rows (share >= {config.HOLIDAY_THRESHOLD}): {df['is_holiday'].sum()}")
    return df


if __name__ == "__main__":
    run()