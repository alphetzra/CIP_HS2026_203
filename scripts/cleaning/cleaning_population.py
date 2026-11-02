"""Population data cleaning - one row per canton and year.

1. Introduction

The BFS population export is reduced to the three columns that are needed:
canton, year and population.

2. Data

------------------------------------------------------------------------------------
| Input                                    | Output                                |
|------------------------------------------|---------------------------------------|
| data/raw/raw_population.csv (BFS export) | data/processed/cleaned_population.csv |
-----------------------------------------------------------------------------------


3. Script description

1. Read the export and keep canton number (KANT), year (TIME_PERIOD) and
   population (OBS_VALUE).
2. Translate the canton number into the canton abbreviation
   (config.CANTON_NO), so it matches the holiday data.
3. Check: no missing values, no duplicate canton/year rows, and one row for every
   canton and year.
4. Save as CSV.

4. Notes

- The checks raise an error instead of only printing a warning, so the
  script stops if the export is incomplete.
"""

from pathlib import Path
import pandas as pd
from scripts import config


def clean_population(raw: Path = config.POP_FILE) -> pd.DataFrame:
    """Turn the BFS population export into one row per canton and year."""
    # the export is downloaded manually, so give a clear message if it is missing
    if not raw.exists():
        raise FileNotFoundError(f"{raw} not found. Download the BFS export "
                                f"to {config.RAW_DIR} first.")

    df = pd.read_csv(raw)
    output = pd.DataFrame({"canton": df["KANT"].map(config.CANTON_NO),
                           "year": df["TIME_PERIOD"],
                           "population": df["OBS_VALUE"]})

    na_counts = output.isna().sum()
    if na_counts.sum() > 0:
        raise ValueError(f"Missing values:\n{na_counts[na_counts > 0]}")
    if output.duplicated(["canton", "year"]).any():
        raise ValueError("Duplicate canton/year rows.")

    if len(output) != len(config.CANTONS) * len(config.YEARS):
        raise ValueError("Missing canton/year combinations.")
    print("No missing values or duplicates, and all canton/year combinations.")

    return output.sort_values(["year", "canton"]).reset_index(drop=True)


def run() -> pd.DataFrame:
    """Clean the population export and save it to data/processed."""
    df = clean_population()
    output = config.CLEANED_POPULATION
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"{len(df)} population rows saved to {output}")
    return df


if __name__ == "__main__":
    run()