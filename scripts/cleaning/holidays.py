import re
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from scripts import config

ROW_SELECTOR = "table.table tbody tr"
PERCENT_RE = re.compile(r"(<)?\s*([\d.]+)\s*%")

CLASS_LABELS = {   # Holiday categories of feiertagskalender.ch.
    1: "official holiday",
    2: "public holiday on a par with Sundays",
    3: "half-holiday",
    4: "legally not recognized holiday",
    5: "event day",
    "partial": "partially valid (only in some municipalities)",
}


def cached_files():
    """Generate (path, label) tuples for cached pages."""
    labels = {config.NATIONAL_GEO: "CH"}
    labels.update({geo: canton for canton, geo in config.CANTONS.items()})
    for year in config.YEARS:
        for geo, label in labels.items():
            path = Path(config.cache_path(geo, year))
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
    """"""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    rows = []
    for tr in soup.select(ROW_SELECTOR):
        cells = tr.find_all("td")
        if len(cells) < 5:  # month-header rows have a single colspan cell
            continue

        date = pd.to_datetime(cells[0].get_text(strip=True), format="%d.%m.%Y")
        holiday = " ".join(cells[2].get_text(" ", strip=True).split())

        badge = cells[4].select_one("span.badge")
        share_note = None
        is_below = False
        if badge is not None:
            holiday_class = int(badge.get_text(strip=True))
            canton_share = 1.0
        else:
            holiday_class = "partial"
            class_text = cells[4].get_text(" ", strip=True)
            canton_share, is_below = parse_percent(class_text)
            if canton_share is None:  # 'varies' / 'n.a.': share unknown, decided later
                canton_share = float("nan")
                share_note = class_text

        rows.append({"date": date, "holiday": holiday, "class": holiday_class,
                     "canton": canton, "canton_share": canton_share,
                     "is_below": is_below, "share_note": share_note})
    return rows


def parse_holidays() -> pd.DataFrame:
    """One row per (date, holiday, canton)."""
    rows = []
    for path, canton in cached_files():
        for row in parse_file(path, canton):
            rows.append(row)
    df = pd.DataFrame(rows, columns=["date", "holiday", "class", "canton",
                                     "canton_share", "is_below", "share_note"])
    return df.sort_values(["date", "holiday", "canton"]).reset_index(drop=True)


def main() -> None:
    df = parse_holidays()
    print(f"\n{len(df)} rows")

    output = Path("cleaned_holidays.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Saved to {output}")

if __name__ == "__main__":
    main()


#def compare_national_to_cantons(holidays):
#    """Report where canton lists differ from the national list."""
#    report = {}
#    for year in config.YEARS:
#        national = holidays.get(("CH", year), {})
#        for canton in config.CANTONS:
#            canton_days = holidays.get((canton, year), {})
#            missing = sorted(set(national) - set(canton_days))
#            extra = sorted(set(canton_days) - set(national))
#            if missing or extra:
#                report[(canton, year)] = {
#                    "missing": [(d, national[d]) for d in missing],
#                    "extra": [(d, canton_days[d]) for d in extra],
#                }
#    return report