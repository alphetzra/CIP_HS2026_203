import re
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from scripts import config

PERCENT_RE = re.compile(r"(<)?\s*([\d.]+)\s*%")

def cached_files():
    """Generate (path, label) tuples for cached pages."""
    labels = {config.NATIONAL_GEO: "CH"}
    labels.update({geo: canton for canton, geo in config.CANTONS.items()})
    for year in config.YEARS:
        for geo, label in labels.items():
            path = config.cache_path(geo, year)
            if path.exists():
                yield path, label
            else:
                print(f"Missing cache: {label} {year} ({path.name})")


def parse_percent(text: str) -> tuple[float | None, bool]:
    """Converts percentages in floats, 'varies'/'n.a.' -> None."""
    percent_match = PERCENT_RE.search(text)
    if percent_match is None:
        return None, False
    is_below = percent_match.group(1) is not None
    number = percent_match.group(2)
    return round(float(number) / 100, 4), is_below


def parse_file(path: Path, canton: str) -> list[dict]:
    """Parse one cached page into a list of holiday rows."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    rows = []
    for tr in soup.select(config.ROW_SELECTOR):
        cells = tr.find_all("td")
        if len(cells) < 5:
            continue

        date = pd.to_datetime(cells[0].get_text(strip=True), format="%d.%m.%Y")
        holiday = " ".join(cells[2].get_text(" ", strip=True).split())

        badge = cells[4].select_one("span.badge")
        share_note = None
        is_below = False
        if badge is not None:  # full holiday with a class
            holiday_class = int(badge.get_text(strip=True))
            is_partial = False
            canton_share = 1.0
        else:
            holiday_class = None
            is_partial = True
            class_text = cells[4].get_text(" ", strip=True)
            canton_share, is_below = parse_percent(class_text)
            if canton_share is None:
                canton_share = float("nan")
                share_note = class_text
        rows.append({"date": date, "holiday": holiday, "holiday_class": holiday_class,
                     "is_partial": is_partial, "canton": canton,
                     "canton_share": canton_share, "is_below": is_below,
                     "share_note": share_note})
    return rows


def parse_holidays() -> pd.DataFrame:
    """One row per date, holiday, canton/national."""
    rows = []
    for path, canton in cached_files():
        for row in parse_file(path, canton):
            rows.append(row)
    df = pd.DataFrame(rows, columns=["date", "holiday", "holiday_class", "is_partial",
                                     "canton", "canton_share", "is_below",
                                     "share_note"])
    df["holiday_class"] = df["holiday_class"].astype("Int64")
    df["level"] = df["canton"].eq("CH").map({True: "national", False: "canton"})
    return df.sort_values(["date", "holiday", "canton"]).reset_index(drop=True)


def missing_national_dates(df: pd.DataFrame) -> pd.DataFrame:
    """National holidays not in canton's list."""
    national = df.loc[(df["level"] == "national") & (~df["is_partial"]),
               ["date", "holiday"]].drop_duplicates("date")
    cantonal = df.loc[df["level"] == "canton", ["date", "canton"]].drop_duplicates()

    expected = national.merge(pd.DataFrame({"canton": list(config.CANTONS)}), how="cross")
    merged = expected.merge(cantonal, on=["date", "canton"], how="left", indicator=True)
    return merged.loc[merged["_merge"] == "left_only"].drop(columns="_merge")


def run() -> pd.DataFrame:
    df = parse_holidays()
    print(f"\n{len(df)} rows")

    output = config.CLEANED_HOLIDAYS
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Saved to {output}")

    missing = missing_national_dates(df)
    print(f"\n{len(missing)} national dates missing in canton level.")
    return df

if __name__ == "__main__":
    run()