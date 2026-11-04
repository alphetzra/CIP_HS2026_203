"""Holiday data cleaning.

The scraped holiday pages are turned into one table with one row per date,
holiday and canton/CH.

Specifics:
- Full holidays are valid in the whole canton and come with a legal class
  (e.g. 2 = on a par with Sundays), so their canton_share is 1.0.
- Partial holidays are only valid in part of a canton. canton_share is the
  share of the population that has the day off. "< x %" is stored as x with
  is_below=True. When the page gives no number, the share is NaN and the
  original text is kept in share_note.
"""

import re
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from scripts import config



def cached_files():
    """Yield every cached holiday page and report missing ones.
    Yields:
        (path, label): Path to the cached HTML file and its label
        (CH/canton abbreviation).
    """

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
    """Extract a population share from text like "35 %" or "< 5 %".
        Args:
            text: Text from the class column of partial holiday
        Returns:
            (share, is_below): Share as a fraction (0.35) or None if the text
                has no number ("varies", "na"); is_below is True for "< x %"
        """

    # matches e.g. "35 %", "12.5%" or "< 5 %"
    percent_regex = re.compile(r"(<)?\s*([\d.]+)\s*%")
    percent_match = percent_regex.search(text)
    if percent_match is None:
        return None, False
    is_below = percent_match.group(1) is not None
    number = percent_match.group(2)
    return round(float(number) / 100, 4), is_below


def parse_file(path: Path, canton: str) -> list[dict]:
    """Parse one cached holiday page into a list of holiday rows.
        Args:
            path: Path to the cached HTML file
            canton: Label
        Returns:
            List of dicts, one per holiday, with date, holiday, holiday_class,
            is_partial, canton, canton_share, is_below and share_note
        """

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    rows_list = []
    for tr in soup.select(config.ROW_SELECTOR):
        # One <tr> is one holiday. Its rows:
        #   rows[0]: date (dd.mm.yyyy)
        #   rows[1]: weekday ("Sa"), not used
        #   rows[2]: holiday name, surrounded by tabs/line breaks in the HTML
        #   rows[3]: calendar week, not used
        #   rows[4]: class badge (full holiday) or population share ("7.5 %")
        rows = tr.find_all("td")
        # skip rows that are not holiday rows
        if len(rows) < 5:
            continue

        date = pd.to_datetime(rows[0].get_text(strip=True), format="%d.%m.%Y")
        holiday = " ".join(rows[2].get_text(" ", strip=True).split())
        badge = rows[4].select_one("span.badge")
        share_note = None
        is_below = False
        if badge is not None:
            # full holiday: valid in the whole canton
            holiday_class = int(badge.get_text(strip=True))
            is_partial = False
            canton_share = 1.0
        else:
            # partial holiday
            holiday_class = None
            is_partial = True
            class_text = rows[4].get_text(" ", strip=True)
            canton_share, is_below = parse_percent(class_text)

            if canton_share is None:
                # website gives no number
                canton_share = float("nan")
                share_note = class_text
        rows_list.append({"date": date, "holiday": holiday, "holiday_class": holiday_class,
                     "is_partial": is_partial, "canton": canton,
                     "canton_share": canton_share, "is_below": is_below,
                     "share_note": share_note})
    return rows_list


def missing_national_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Consistency check: find full national holidays that are missing from a canton's calendar.
    Args:
        df: Cleaned holiday table with a "level" column (canton/national)
    Returns:
        DataFrame with date, holiday and canton for every missing entry
    """

    national = df.loc[(df["level"] == "national") & (~df["is_partial"]),
               ["date", "holiday"]].drop_duplicates("date")
    cantonal = df.loc[df["level"] == "canton", ["date", "canton"]].drop_duplicates()

    expected = national.merge(pd.DataFrame({"canton": list(config.CANTONS)}), how="cross")
    merged = expected.merge(cantonal, on=["date", "canton"], how="left", indicator=True)
    return merged.loc[merged["_merge"] == "left_only"].drop(columns="_merge")


def get_preprocessed_cleaned_holidays() -> pd.DataFrame:
    """Build the cleaned holiday table from all cached pages.
        Returns:
            DataFrame with one row per date, holiday and canton/CH, sorted by
            date, holiday and canton; prints how many national dates are missing
        """
    rows = []
    for path, canton in cached_files():
        for row in parse_file(path, canton):
            rows.append(row)
    df = pd.DataFrame(rows, columns=["date", "holiday", "holiday_class", "is_partial",
                                     "canton", "canton_share", "is_below",
                                     "share_note"])
    df["holiday_class"] = df["holiday_class"].astype("Int64")
    df["date"] = pd.to_datetime(df["date"])
    df["level"] = df["canton"].eq("CH").map({True: "national", False: "canton"})
    df = df.sort_values(["date", "holiday", "canton"]).reset_index(drop=True)

    missing = missing_national_dates(df)
    print(f"\n{len(missing)} national dates missing in canton level.")
    return df