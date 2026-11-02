"""Holiday data cleaning - parse the cached HTML pages into one table.

1. Introduction

The scraped holiday pages (one HTML file per canton/national calendar and
year) are turned into one tidy table with one row per date, holiday and
canton/CH for the national calendar.

2. Data

---------------------------------------------------------------------------------
| Input                                   | Output                              |
|-----------------------------------------|-------------------------------------|
| data/raw/raw_holidays/html_cache/*.html | data/processed/cleaned_holidays.csv |
--------------------------------------------------------------------------------

Output columns:
- date, holiday:   date and English name of the holiday
- holiday_class:   class shown on the website for full holidays (badge number);
                   empty for partial holidays
- is_partial:      True if the holiday only applies in part of the canton
- canton:          canton abbreviation, or "CH" for the national calendar
- canton_share:    share of the canton's population where the holiday applies
                   (1.0 for full holidays, NaN if the website gives no number)
- is_below:        True if the website gives the share as "< x %"
                   (the stored value is then an upper bound)
- share_note:      original text when no share is given ("varies", "n.a.")
- level:           "national" or "canton"

3. Script description

1. Loop over all expected cache files (config.YEARS x national + cantons)
   and report missing ones.
2. Parse each table row with BeautifulSoup: date, holiday name and the
   class column. Full holidays have a numbered badge; partial holidays show
   a population share instead.
3. Combine all rows, sort them and save as CSV.
4. Check: list national holidays that are missing in a canton's calendar.

4. Notes

- No rows are dropped. Partial holidays without a number keep
  canton_share = NaN and the original text in share_note, so this
  information is not lost.
- The parser depends on the current HTML structure of feiertagskalender.ch
  (row selector in config.ROW_SELECTOR, class in the 5th column).
"""

import re
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from scripts import config

# matches e.g. "35 %", "12.5%" or "< 5 %"; group 1 = "<", group 2 = number
PERCENT_RE = re.compile(r"(<)?\s*([\d.]+)\s*%")

def cached_files():
    """Generate (path, label) tuples for cached pages."""
    # map website geo id to label (CH for national, else canton abbreviation)
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
    """Converts percentages in floats, 'varies'/'n.a.' -> None.
    Also returns whether the value was given as "< x %"."""
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
        # skip rows that are not holiday rows
        if len(cells) < 5:
            continue

        # column 1: date, column 3: holiday name
        date = pd.to_datetime(cells[0].get_text(strip=True), format="%d.%m.%Y")
        # join the text parts and collapse multiple spaces/breaks
        holiday = " ".join(cells[2].get_text(" ", strip=True).split())

        # column 5: badge with class number (full holiday)
        # or population share as text (partial holiday)
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
                # no number: keep NaN and the original text
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
    """Consistency check: a full national holiday is expected on every cantonal page."""

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