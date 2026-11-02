"""Clean the daily card spending data of Monitoring Consumption Switzerland."""

import pandas as pd
from scripts import config

def read_spending(path=config.RAW_SPENDING) -> pd.DataFrame:
    """Read parquet file and rename columns"""
    df = pd.read_parquet(path)
    return df.rename(columns=config.SPENDING_COLUMNS)


def drop_unused(df: pd.DataFrame) -> pd.DataFrame:
    """Drop the unused transactions column and code 9999 in region/category."""
    df = df.drop(columns="n_transactions")
    for col in ["region", "category"]:
        df[col] = df[col].astype(str).str.strip()
        is_9999 = df[col] == "9999"
        print(f"Dropped {is_9999.sum()} rows with {col} 9999.")
        df = df.loc[~is_9999].copy()
    return df


def fix_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Dates as datetime and spending as numbers.
       errors="coerce" turns anything that is not a number into NaN."""
    df["date"] = pd.to_datetime(df["date"])
    df["region"] = pd.Categorical(df["region"], categories=list(config.REGIONS))
    df["category"] = df["category"].astype("category")
    df["spending"] = pd.to_numeric(df["spending"], errors="coerce")
    return df


def filter_years(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only study period."""
    in_period = df["date"].dt.year.isin(config.YEARS)
    print(f"Dropped {(~in_period).sum()} rows outside {min(config.YEARS)}-{max(config.YEARS)}.")
    return df.loc[in_period].reset_index(drop=True)


def check_spending(df: pd.DataFrame) -> None:
    """Report missing values, duplicates, impossible values and missing days."""
    na = df.isna().sum()
    print(f"Missing values per column: {na[na > 0] if na.sum() else 'none'}")

    duplicates = df.duplicated(["date", "region", "category"]).sum()
    if duplicates:
        raise ValueError(f"{duplicates} duplicate date/region/category rows.")

    print(f"Negative values: {(df['spending'] < 0).sum()}, "
          f"zero values: {(df['spending'] == 0).sum()}")

    all_days = pd.date_range(f"{min(config.YEARS)}-01-01", f"{max(config.YEARS)}-12-31")
    days_present = df.groupby(["region", "category"])["date"].nunique()
    gaps = (len(all_days) - days_present).loc[lambda s: s > 0]
    if gaps.empty:
        print("Every region/category has all days.")
    else:
        print(f"Missing days per region/category:\n{gaps.sort_values(ascending=False)}")


def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Flag (not drop) outliers with the IQR rule per region and category."""
    grouped = df.groupby(["region", "category"], observed=True)["spending"]
    q1 = grouped.transform(lambda s: s.quantile(0.25))
    q3 = grouped.transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    df["is_outlier"] = (df["spending"] < q1 - 1.5 * iqr) | (df["spending"] > q3 + 1.5 * iqr)
    print(f"Flagged {df['is_outlier'].sum()} outliers.")
    return df


def clean_spending() -> pd.DataFrame:
    """Run the cleaning steps in order."""
    df = read_spending()
    df = drop_unused(df)
    df = fix_dtypes(df)
    df = filter_years(df)
    check_spending(df)
    df = flag_outliers(df)
    return df.sort_values(["date", "region", "category"]).reset_index(drop=True)


def run() -> pd.DataFrame:
    """Clean the spending export and save it to data/processed."""
    df = clean_spending()
    output = config.CLEANED_SPENDING
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    print(f"{len(df)} spending rows saved to {output}")
    return df


if __name__ == "__main__":
    run()