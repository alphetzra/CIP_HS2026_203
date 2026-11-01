from pathlib import Path
import pandas as pd
from scripts import config


def clean_population(raw: Path = config.POP_FILE) -> pd.DataFrame:
    """Turn the BFS population export into one row per canton and year."""
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