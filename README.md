# CIP_HS2026_203

This repository contains the code for our group project in Data Collection, Integration and Preprocessing (CIP), part of the MSc in Applied Data Science and AI at HSLU, autumn semester 2026. We study how calendar effects, public holidays, major events and the EUR/CHF exchange rate relate to daily card spending in Switzerland.

We study how daily card spending in Switzerland relates to calendar effects, public holidays, major events and the EUR/CHF exchange rate. The project answers three research questions:

| | Research question |
|---|---|
| Q1 | How do major events (# of participants) in Canton Zürich affect daily POS spending across merchant categories compared with similar non-event days? |
| Q2 | How much of the daily variation in spending by category is explained by calendar effects (weekday, month, public holidays)? How does a regional public holiday change spending by category in regions where it applies, compared with regions where the same date is a normal working day? |
| Q3 | Is spending in border regions more strongly affected by a decrease in the EUR/CHF exchange rate than spending in non-border regions, and does this effect differ between border regions? |

All three questions use daily card-payment data from [Monitoring Consumption Switzerland](https://monitoringconsumption.com)
(MCS) for the seven Swiss Grossregionen, 2019-2025. Each question adds further sources:

- Q1: dates and attendance of major events in Zürich (Street Parade, Züri Fäscht), scraped from official and public web pages
- Q2: public holidays per canton, scraped from [feiertagskalender.ch](https://www.feiertagskalender.ch), and population per canton from the [Federal Statistical Office (BFS)](https://www.bfs.admin.ch) to aggregate holidays to Grossregion level
- Q3: EUR/CHF exchange rate from the [SNB data portal](https://data.snb.ch) via API

MCS publishes *scaled* transaction values, not CHF amounts, so all results are relative (indices or % changes).

---
## Repository structure


```
CIP_HS2026_203/
├── README.md
├── requirements.txt  # Python dependencies
│
├── data/
│   ├── raw/  # Unchanged downloads, API answers and scraped data
│   │   ├── raw_spending.parquet   
│   │   └── raw_exchange.parquet   
│   └── processed/  # Cleaned single sources
│       ├── clean_spending.parquet
│       └── Q3_spending.parquet
│
├── scripts/
│   ├── Q1/ 
│   │    └── Q1_scarping.py
│   │    └── Q1_preprocessing.py
│   │    └── Q1_data_analysis.py
│   │    └── output/
│   │          ├── figures/ # Figures used in the report
│   │          └── tables/  # Tables used in the reports
│   ├── Q2/
│   │    └── output/
│   │          ├── figures/           # Figures used in the report
│   │          └── tables/            # Regression and diagnostic tables
│   └── Q3/ 
│       ├── spending
│       │      ├── download_spending.py       # MCS spending data download
│       │      └── preprocessing_spending.py  # MCS spending data preprocessing
│       ├── exchange
│       │      └── api_SNB.py  # API data retrieval from SNB
│       ├── Q3_merge.py        # Merging datasets for Q3
│       ├── Q3_analysis.py     # Final data analysis for Q3
│       └── output/
│           ├── figures/  # Figures used in the report
│           └── tables/   # Regression and diagnostic tables
│
└── report/   # Final documentation (LaTeX) and feasibility study
```


---

## Setup

Python 3.10+ is required.

```bash
git clone https://github.com/alphetzra/CIP_HS2026_203.git
cd CIP_HS2026_203
python -m venv .venv
source .venv/bin/activate          
pip install -r requirements.txt
```

---

## How to run
 
### Q2 pipeline
 
```bash
python main.py  #CHANGED TO UPDATE
```
 
### Q3 pipeline
 
The Q3 scripts are [marimo] notebooks. 
They use relative paths (`../../data/...`), so run them from inside their own folder, in this order:
All commands are run from the repository root (use `python3` instead of `python` on macOS/Linux if needed).

```bash
cd scripts/Q3/spending
python download_spending.py          # Output: Spending -> data/raw/raw_spending.parquet
cd ../../..

cd scripts/Q3/exchange
python api_SNB.py                    # Output: EUR/CHF rates from the SNB API -> data/raw/raw_exchange.parquet
cd ../../..

cd scripts/Q3/spending
python preprocesssing_spending.py    # Output: Clean MCS data -> data/processed/clean_spending.parquet
cd ../../..

cd scripts/Q3
python Q3_merge.py                   # Output: Join rates and holiday share -> data/processed/q3_data.parquet
cd ../..

cd scripts/Q3
python Q3_analysis.py                # Output: Regressions, diagnostics, figures and tables -> scripts/Q3/output/
cd ../..
```
---

## Contributions

| Member | Research question | Code |
|---|---|---|
| **Morteza Nejati** | Q1: major events in Zürich | 01_event_web_scraping.ipynb, 02_data_cleaning_transformation_integration.ipynb, 03_data_analysis_visualization.ipynb |
| **Laura Da Silva Cunha** | Q2: population and public holidays + README.md | `main.py`, `scripts/config.py`, `scripts/acquisition/scrape_holidays.py`, `scripts/acquisition/download_spending.py`, `scripts/cleaning/cleaning_holidays.py`, `scripts/cleaning/cleaning_population.py`, `scripts/cleaning/cleaning_spending.py`, `scripts/integration/holiday_share.py`, `scripts/integration/build_df.py`, `scripts/analysis/calendar_index.py`, `scripts/analysis/calendar_regression.py`, `scripts/analysis/regional_holiday_effect.py` |
| **Salvatore Nicolosi** | `MCS data`,  `Q3: EUR/CHF and border regions`, `Git`, `README.md`, `requirements.txt` |


## Use of generative AI
 
| | Used for | Checked / decided by the team |
|---|---|---|
| Q1 | Improving and debugging Python code, refining data processing and visualizations, writing and improving Markdown documentation, and assisting with drafting, structuring, and polishing the project report. | checking the report and visual for accuracy and readibility |
| Q2 | *to be completed* | *to be completed* | 
| Q3 | Suggestions to improve and debug visualizations with matplotlib | Debugging tips the marimo notebooks whenever necessary (e.g. shallow copy); clarifying `statsmodels` syntax for HC1 standard errors and VIF; polishing the English of the Q3 report to match style and repository structure section and the README.md | Collecting ideas for order-region classification, robustness check without COVID debug; every AI suggestion was reviewed by manually searching libraries and tested before committing |
 
All research questions, methodological choices, analyses and conclusions were developed and checked by the team.
