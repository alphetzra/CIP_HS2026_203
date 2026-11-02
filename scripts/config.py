"""Shared settings for all pipeline scripts: paths, study period, regions
 and analysis choices."""

from pathlib import Path

# ======================= paths =======================
ROOT = Path(__file__).resolve().parents[1]           # repository root (parent of scripts/)
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"

# raw data
HTML_CACHE_DIR = RAW_DIR / "raw_holidays" / "html_cache"   # raw HTML of feiertagskalender.ch
POP_FILE = RAW_DIR / "raw_population.csv"                  # manual download from BFS
RAW_SPENDING = RAW_DIR / "raw_spending.parquet"            # Monitoring Consumption Switzerland

# processed data
CLEANED_HOLIDAYS = PROCESSED_DIR / "cleaned_holidays.csv"
CLEANED_POPULATION = PROCESSED_DIR / "cleaned_population.csv"
CLEANED_SPENDING = PROCESSED_DIR / "cleaned_spending.parquet"
REGION_HOLIDAY_SHARE = PROCESSED_DIR / "region_holiday_share.csv"
DF_Q2 = PROCESSED_DIR / "df_q2.parquet"

# ======================= study period and regions =======================
YEARS = range(2019, 2026)   # 2019 to 2025 inclusive

CANTON_NO = {       # canton numbers used by BFS (column KANT in the population export)
    1: "ZH",  2: "BE",  3: "LU",  4: "UR",  5: "SZ",  6: "OW",  7: "NW",
    8: "GL",  9: "ZG", 10: "FR", 11: "SO", 12: "BS", 13: "BL", 14: "SH",
    15: "AR", 16: "AI", 17: "SG", 18: "GR", 19: "AG", 20: "TG", 21: "TI",
    22: "VD", 23: "VS", 24: "NE", 25: "GE", 26: "JU",
}
REGIONS = {         # Grossregionen of Monitoring Consumption Switzerland (west to east)
    "Lake Geneva":       ["GE", "VD", "VS"],
    "Espace Mittelland": ["BE", "FR", "JU", "NE", "SO"],
    "Northwestern":      ["AG", "BL", "BS"],
    "Zurich":            ["ZH"],
    "Central":           ["LU", "OW", "NW", "SZ", "UR", "ZG"],
    "Eastern":           ["AI", "AR", "GL", "GR", "SG", "SH", "TG"],
    "Ticino":            ["TI"],
}
CANTON_TO_REGION = {}   # canton -> region (inverse of REGIONS)
for region, cantons_in_region in REGIONS.items():
    for canton in cantons_in_region:
        CANTON_TO_REGION[canton] = region

# ======================= acquisition =======================
# holidays: feiertagskalender.ch
ROW_SELECTOR = "table.table tbody tr"
CLASS = 4                   # class parameter is cumulative: classes 1 to 4
LANG = "en"                 # page language: en, de, fr, it
NATIONAL_GEO = 3056         # Switzerland ID on feiertagskalender.ch
CANTONS = {                 # canton IDs on feiertagskalender.ch
    "AG": 1,    "AR": 245,  "AI": 266,  "BL": 273,  "BS": 365,  "BE": 369,
    "FR": 796,  "GE": 1026, "GL": 1072, "GR": 1102, "JU": 1323, "LU": 1410,
    "NE": 1523, "NW": 1592, "OW": 1604, "SH": 1612, "SZ": 1653, "SO": 1690,
    "SG": 1827, "TI": 1932, "TG": 2173, "UR": 2262, "VD": 2283, "VS": 2685,
    "ZG": 2860, "ZH": 2872,
}

# spending: Monitoring Consumption Switzerland
SPENDING_URL = ("https://drive.switch.ch/index.php/s/yLISs3KVE7ASE68/download"
                "?path=/2_ACQUIRING%20DATA&files=ACQ_POS_Grossregion_NOGA.csv")

# ======================= cleaning =======================
SPENDING_COLUMNS = {
    "Date": "date",
    "Region": "region",
    "Merchant category": "category",
    "Scaled Value": "spending",
    "Scaled Number of Transactions": "n_transactions",
}
CLASS_LABELS = {            # holiday classes of feiertagskalender.ch
    1: "official holiday",
    2: "public holiday on a par with Sundays",
    3: "half-holiday",
    4: "legally not recognized holiday",
    5: "event day",
    "partial": "partially valid (only in some municipalities)",
}

# ======================= integration =======================
HOLIDAY_WEIGHTS = {1: 1.0, 2: 1.0, 3: 0.5}  # share of people off per class (3 = half day)
EXCLUDED_CLASS = [4]                         # legally not recognized -> normal working day
UNKNOWN_PARTIAL_SHARE = 0.0                  # partial holidays with "varies"/"n.a." -> nobody off
HOLIDAY_THRESHOLD = 0.5                      # is_holiday = at least half of the region off
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ======================= analysis =======================
TARGET = "log_spending"                      # dependent variable of the regressions

# COVID-19 period, flagged instead of deleted (controlled for in the regression).
# Defined from the weekly laboratory-confirmed SARS-CoV-2 cases reported to the
# FOPH (BAG): weeks with more than 50 cases per 100,000 inhabitants, extended
# slightly before and after, because consumer behaviour already changes before
# measures start and needs time to return to normal afterwards.
# Source: FOPH, https://www.idd.bag.admin.ch/en/diseases/covid/statistic
COVID_PERIOD = [("2020-03-16", "2022-12-31")]


# ======================= helper =======================
def cache_path(geo, year):
    """Where the raw HTML of one holiday page is stored."""
    return HTML_CACHE_DIR / f"{geo}_{year}_{CLASS}_{LANG}.html"