"""Spending data acquisition - download from Monitoring Consumption Switzerland.

Source: Monitoring Consumption Switzerland (debit/credit card transactions,
daily, by region and spending category). The dataset is published as an open
CSV download, so pandas read it from the URL defined in config.SPENDING_URL.

Design choices:
- The raw data is stored *unchanged*, so the original data can always be
  inspected.
- Parquet instead of CSV: the file is large (daily rows x regions x
  categories); parquet is compressed, faster to read and keeps column dtypes.
- The download runs only once. If the raw file already exists it is skipped,
  so re-running the pipeline does not hit the server again and results stay
  reproducible even if the online dataset is updated later.
"""
import pandas as pd
from scripts import config  # central place for URLs and file paths


def download_spending(url: str = config.SPENDING_URL) -> pd.DataFrame:
    """Read the CSV directly from the download link into a DataFrame."""
    print("Downloading spending data ...")
    return pd.read_csv(url)


def save_raw(df: pd.DataFrame) -> None:
    """Store the data unchanged as parquet in data/raw."""
    output = config.RAW_SPENDING
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output, index=False)
    print(f"Saved {len(df)} rows to {output}")


def run(force: bool = False) -> None:
    """Download the spending data once; skip if the raw file already exists."""
    if config.RAW_SPENDING.exists():
        print(f"{config.RAW_SPENDING.name} already exists, download skipped.")
        return
    save_raw(download_spending())


if __name__ == "__main__":
    run()