"""Download the daily card spending data of Monitoring Consumption Switzerland."""
import pandas as pd
from scripts import config


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