"""Shared settings for all pipeline scripts: years, IDs, regions and folder paths."""
from pathlib import Path

# ======================= paths =======================
ROOT = Path(__file__).resolve().parents[1]          # repository root (parent of scripts/)
RAW_DIR = ROOT / "data" / "raw"                     # gitignored: scraped HTML, downloaded files
PROCESSED_DIR = ROOT / "data" / "processed"         # cleaned and merged tables

HTML_CACHE_DIR = RAW_DIR / "feiertagskalender"      # raw HTML of feiertagskalender.ch
RAW_POP_FILE = RAW_DIR / "population_raw.csv"       # manual download from stats.swiss (BFS STATPOP)
POP_FILE = PROCESSED_DIR / "population_canton.csv"  # cleaned: canton;population;year

# ======================= settings =======================
YEARS = range(2019, 2026)   # 2019 to 2025 inclusive
CLASS = 4                   # feiertagskalender class parameter is cumulative: 1 to 4 inclusive
LANG = "en"                 # page language: en, de, fr, it

NATIONAL_GEO = 3056         # Switzerland ID used by feiertagskalender.ch
CANTONS = {    # canton geo IDs
    "AG": 1,    "AR": 245,  "AI": 266,  "BL": 273,  "BS": 365,  "BE": 369,
    "FR": 796,  "GE": 1026, "GL": 1072, "GR": 1102, "JU": 1323, "LU": 1410,
    "NE": 1523, "NW": 1592, "OW": 1604, "SH": 1612, "SZ": 1653, "SO": 1690,
    "SG": 1827, "TI": 1932, "TG": 2173, "UR": 2262, "VD": 2283, "VS": 2685,
    "ZG": 2860, "ZH": 2872,
}
CANTON_NO = {  # canton numbers used in BFS (column KANT in the stats.swiss export)
    1: "ZH",  2: "BE",  3: "LU",  4: "UR",  5: "SZ",  6: "OW",  7: "NW",
    8: "GL",  9: "ZG", 10: "FR", 11: "SO", 12: "BS", 13: "BL", 14: "SH",
    15: "AR", 16: "AI", 17: "SG", 18: "GR", 19: "AG", 20: "TG", 21: "TI",
    22: "VD", 23: "VS", 24: "NE", 25: "GE", 26: "JU",
}
REGIONS = {    # map regions to cantons according to Monitoring Consumption Switzerland
    "Central":           ["LU", "OW", "NW", "SZ", "UR", "ZG"],
    "Eastern":           ["AI", "AR", "GL", "GR", "SG", "SH", "TG"],
    "Espace Mittelland": ["BE", "FR", "JU", "NE", "SO"],
    "Lake Geneva":       ["GE", "VD", "VS"],
    "Northwestern":      ["AG", "BL", "BS"],
    "Ticino":            ["TI"],
    "Zurich":            ["ZH"],
}

CANTON_TO_REGION = {}   # map canton to region (inverse of previous dictionary REGIONS)
for region, cantons_in_region in REGIONS.items():
    for canton in cantons_in_region:
        CANTON_TO_REGION[canton] = region

# How much of a canton has the day off, by the value in the "Class" column of a canton page
CLASS_WEIGHT = {"1": 1.0, "2": 1.0, "3": 0.5, "4": 1.0}  # class 3 = half day off


def cache_path(geo, year):
    """Where the raw HTML of one feiertagskalender page is stored."""
    return HTML_CACHE_DIR / f"{geo}_{year}_{CLASS}_{LANG}.html"