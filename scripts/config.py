"""Shared settings for all pipeline scripts: years, IDs, regions and folder paths."""
from pathlib import Path

# ======================= paths =======================
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

HTML_CACHE_DIR = RAW_DIR / "raw_holidays" / "html_cache"
CLEANED_HOLIDAYS = PROCESSED_DIR / "cleaned_holidays.csv"
POP_FILE = RAW_DIR / "raw_population.csv"
CLEANED_POPULATION = PROCESSED_DIR / "cleaned_population.csv"
SPENDING_URL = "https://drive.switch.ch/index.php/s/yLISs3KVE7ASE68/download?path=/2_ACQUIRING%20DATA&files=ACQ_POS_Grossregion_NOGA.csv"
RAW_SPENDING = RAW_DIR / "raw_spending.parquet"
CLEANED_SPENDING = PROCESSED_DIR / "cleaned_spending.parquet" # cleaned spending
REGION_HOLIDAY_SHARE = PROCESSED_DIR / "region_holiday_share.csv"  # holiday share per region/day
DF_Q2 = PROCESSED_DIR / "df_q2.parquet"

# ======================= settings =======================
ROW_SELECTOR = "table.table tbody tr"
YEARS = range(2019, 2026)
CLASS = 4
LANG = "en"

CLASS_LABELS = {
    1: "official holiday",
    2: "public holiday on a par with Sundays",
    3: "half-holiday",
    4: "legally not recognized holiday",
    5: "event day",
    "partial": "partially valid (only in some municipalities)",
}

NATIONAL_GEO = 3056
CANTONS = {
    "AG": 1,    "AR": 245,  "AI": 266,  "BL": 273,  "BS": 365,  "BE": 369,
    "FR": 796,  "GE": 1026, "GL": 1072, "GR": 1102, "JU": 1323, "LU": 1410,
    "NE": 1523, "NW": 1592, "OW": 1604, "SH": 1612, "SZ": 1653, "SO": 1690,
    "SG": 1827, "TI": 1932, "TG": 2173, "UR": 2262, "VD": 2283, "VS": 2685,
    "ZG": 2860, "ZH": 2872,
}
CANTON_NO = {
    1: "ZH",  2: "BE",  3: "LU",  4: "UR",  5: "SZ",  6: "OW",  7: "NW",
    8: "GL",  9: "ZG", 10: "FR", 11: "SO", 12: "BS", 13: "BL", 14: "SH",
    15: "AR", 16: "AI", 17: "SG", 18: "GR", 19: "AG", 20: "TG", 21: "TI",
    22: "VD", 23: "VS", 24: "NE", 25: "GE", 26: "JU",
}
REGIONS = {
    "Central":           ["LU", "OW", "NW", "SZ", "UR", "ZG"],
    "Eastern":           ["AI", "AR", "GL", "GR", "SG", "SH", "TG"],
    "Espace Mittelland": ["BE", "FR", "JU", "NE", "SO"],
    "Lake Geneva":       ["GE", "VD", "VS"],
    "Northwestern":      ["AG", "BL", "BS"],
    "Ticino":            ["TI"],
    "Zurich":            ["ZH"],
}

CANTON_TO_REGION = {}
for region, cantons_in_region in REGIONS.items():
    for canton in cantons_in_region:
        CANTON_TO_REGION[canton] = region


HOLIDAY_WEIGHTS = {1: 1.0, 2: 1.0, 3: 0.5}
EXCLUDED_CLASS = [4]
UNKNOWN_PARTIAL_SHARE = 0.0
HOLIDAY_THRESHOLD = 0.5

SPENDING_COLUMNS = {
    "Date": "date",
    "Region": "region",
    "Merchant category": "category",
    "Scaled Value": "scaled_value",
    "Scaled Number of Transactions": "n_transactions",
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def cache_path(geo, year):
    """Where the raw HTML of one raw_holidays page is stored."""
    return HTML_CACHE_DIR / f"{geo}_{year}_{CLASS}_{LANG}.html"