import os
import pandas as pd
from scripts import config

def clean_population(raw=config.POP_FILE):
    """Parse population.csv to df."""
    if not os.path.exists(raw):
        raise FileNotFoundError(f"{raw} not found. Download the BFS export to RAW_DIR first.")

    df = pd.read_csv(raw)
    output = pd.DataFrame({"canton": df["KANT"].map(config.CANTON_NO),
                           "year": df["TIME_PERIOD"],
                           "population": df["OBS_VALUE"]})
    na_counts = output.isna().sum()
    assert na_counts.sum() == 0, f"missing values:\n{na_counts[na_counts > 0]}"
    assert not output.duplicated(["canton", "year"]).any(), "duplicate canton/year rows"
    assert len(output) == len(config.CANTONS) * len(config.YEARS), "missing canton/year combinations"
    print("No missing values or duplicates, and all canton/year combinations.")

    output.sort_values(["year", "canton"]).to_csv(config.POP_FILE, sep=";", index=False, encoding="utf-8-sig")
    print(f"{len(output)} population rows saved to {config.POP_FILE}")