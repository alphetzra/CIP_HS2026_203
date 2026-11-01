"""Build the daily table for Q2."""

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
    df = spending.merge(share, on=["date", "region"], how="left")
    df["holiday_share"] = df["holiday_share"].fillna(0.0)
    return df


def add_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar columns derived from the date (enrichment step)."""
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["weekday"] = pd.Categorical(df["date"].dt.day_name(),
                                   categories=config.WEEKDAYS, ordered=True)
    df["is_weekend"] = df["date"].dt.day_of_week >= 5
    df["is_holiday"] = df["holiday_share"] >= config.HOLIDAY_THRESHOLD
    return df


def add_log_value(df: pd.DataFrame) -> pd.DataFrame:
    """Log of spending, so regression coefficients read as percentage changes."""
    df["log_scaled_value"] = np.log(df["scaled_value"].where(df["scaled_value"] > 0))
    return df


def set_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Grouping columns as categories."""
    df["region"] = pd.Categorical(df["region"], categories=list(config.REGIONS))
    df["category"] = df["category"].astype("category")
    return df


def build_df_q2() -> pd.DataFrame:
    """Run the steps in order: load -> merge -> calendar -> log -> categories."""
    spending, share = load_inputs()
    df = merge_holidays(spending, share)
    df = add_calendar(df)
    df = add_log_value(df)
    df = set_categories(df)
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