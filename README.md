# CIP_HS2026_203

This repository contains the code for our group project in Data Collection, Integration and Preprocessing (CIP), part of the MSc in Applied Data Science and AI at HSLU, autumn semester 2026. We study how calendar effects, public holidays, major events and the EUR/CHF exchange rate relate to daily card spending in Switzerland.

We study how daily card spending in Switzerland relates to calendar effects, public holidays, major events and the EUR/CHF exchange rate. The project answers three research questions:

| | Research question |
|---|---|
| Q1 | How do major events (# of participants) in Canton Zürich affect daily POS spending across merchant categories compared with similar non-event days? |
| Q2 | How much of the daily variation in spending by category is explained by calendar effects (weekday, month, public holidays)? How does a regional public holiday change spending by category in regions where it applies, compared with regions where the same date is a normal working day? |
| Q3 | Is spending in border regions more strongly affected by a decrease in the EUR/CHF exchange rate than spending in non-border regions, and does this effect differ between border regions? |

All three questions use daily card-payment data from [Monitoring Consumption Switzerland](https://monitoringconsumption.com)(2019-2025)
The data-set contains seven Swiss Grossregionen and seven categories: 
1. Accommodation, 
2. Food and beverage services, 
3. Retail: Food, beverage and tobacco, 
4. Retail: Fuel stations, 
5. Retail: Other goods, 
6. Transport services, 
7. Other

Each question adds further sources:

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
│   │   ├── raw_exchange.parquet
│   │   ├── raw_holidays/  
│   │   ├── raw_population.csv 
│   │   └── ACQ_POS_Grossregion_NOGA.csv
│   └── processed/  # Cleaned single sources
│       ├── clean_spending.parquet
│       ├── cleaned_holidays.csv  
│       ├── cleaned_population.csv 
│       ├── q3_data.parquet
│       ├── region_holiday_share.csv
│       ├── q1_event_editions_clean.csv 
│       ├── q1_event_spending_integrated.csv 
│       ├── q1_spending_zurich_clean.csv 
│       ├── zurich_event_days.csv 
│       └── df_q2.parquet
├── scripts/
│   ├── Q1/ 
│   │    └── 01_event_web_scraping                          #Retrieveal event data via scraping
│   │    └── 02_data_cleaning_transformation_integration    #Preprocessing script (jupyter)
│   │    └── 03_data_analysis_visualization                 #Q1 final analysis (jupyter)
│   │    └── output/
│   │          ├── figures/                                 # Figures used in the report
│   │          └── tables/                                  # Tables used in the reports
│   ├── Q2/
│   │   ├── analysis/
│   │   │   ├── calendar_regression.py         # Calendar-effect regression models
│   │   │   └── regional_holiday_effect.py     # Regional holiday effect analysis
│   │   ├── events/
│   │   │   └── events.py                      # Loaders for raw and cleaned events
│   │   ├── exchange/
│   │   │   └── exchange.py                    # Loader for exchange data
│   │   ├── exploration/
│   │   │   ├── calendar_index.py              # Calendar index exploration
│   │   │   └── explore_spending.py            # Exploratory spending analysis
│   │   ├── holidays/
│   │   │   ├── holidays.py                    # Holiday cleaned
│   │   │   ├── preprocessing_cleaning.py      # Holiday data cleaning
│   │   │   └── scrape.py                      # Holiday data scraping
│   │   ├── integration/
│   │   │   ├── build_df.py                    # Builds the merged analysis dataset
│   │   │   └── population_holidays.py         # Joins population and holiday data
│   │   ├── output/
│   │   │   ├── figures/                       # Figures from exploration and report
│   │   │   └── tables/                        # Regression and diagnostic tables
│   │   ├── population/
│   │   │   ├── acquire.py                     # Population data download
│   │   │   ├── cleaning.py                    # Population data cleaning
│   │   │   └── population.py                  # Population cleaned
│   │   ├── spending/
│   │   │   └── spending.py                    # Loaders for raw and cleaned 
│   │   ├── .example.env                       # Template for environment variables
│   │   ├── ADR.md                             # Architecture decision records
│   └── Q3/ 
│       ├── spending
│       │      ├── download_spending.py       # MCS spending data download
│       │      └── preprocessing_spending.py  # MCS spending data preprocessing
│       ├── exchange
│       │      └── api_SNB.py                 # API data retrieval from SNB
│       ├── Q3_merge.py                       # Merging datasets for Q3
│       ├── Q3_analysis.py                    # Final data analysis for Q3
│       └── output/
│           ├── figures/                      # Figures used in the report
│           └── tables/                       # Regression and diagnostic tables
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

pip install -r dev_requirements.txt
playwright install chromium
jupyter lab
```

---

## How to run

All steps are run from the **repository root** through `main.py`

```bash
python main.py <command> <target>
```

To see all available commands and targets:

```bash
python main.py --help
python main.py <command> --help     # e.g. python main.py analysis --help
```

### Available commands

| Command       | Targets                                              | Description                                   |
|---------------|------------------------------------------------------|-----------------------------------------------|
| `scrape`      | `holidays`, `population`, `spending`, `exchange`, `events` | Download / scrape the source data        |
| `raw`         | `population`, `spending`, `exchange`, `events`       | Show the first rows of the raw data           |
| `data`        | `population`, `spending`, `exchange`, `events`       | Show the first rows of the cleaned data       |
| `exploration` | `spending`, `calendar`                               | Run exploratory analysis                      |
| `integration` | `q1`, `q2`, `q3`                                      | Build the merged dataset for each question    |
| `analysis`    | `events`, `calendar`, `region`, `spending`           | Run the final analysis and write the outputs |

### Q1 pipeline: events

```bash
python main.py scrape events        # -> data/processed/zurich_event_days.csv
python main.py integration q1       # -> data/processed/ (cleaned + integrated event-spending data)
python main.py analysis events      # -> figures/
```

### Q2 pipeline: holidays and calendar effects

```bash
python main.py scrape holidays
python main.py scrape population
python main.py scrape spending
python main.py exploration calendar     # optional: calendar index exploration
python main.py integration q2           # final Q2 DataFrame
python main.py analysis calendar        # -> scripts/Q2/output/
python main.py analysis region          # -> scripts/Q2/output/
```

### Q3 pipeline: spending and exchange rates

```bash
python main.py scrape spending      # -> data/raw/raw_spending.parquet
python main.py scrape exchange      # -> data/raw/raw_exchange.parquet
python main.py integration q3       # -> data/processed/q3_data.parquet
python main.py analysis spending    # -> scripts/Q3/output/
```

---

## Contributions

| Member | Research question | Code |
|---|---|---|
| **Morteza Nejati** | Q1: major events in Zürich | 01_event_web_scraping.ipynb, 02_data_cleaning_transformation_integration.ipynb, 03_data_analysis_visualization.ipynb |
| **Laura Da Silva Cunha** | Q2: population and public holidays | `scripts/Q2`, `main.py`, `config.py`, `README.md` |
| **Salvatore Nicolosi** | Q3: EUR/CHF and border regions + MCS spending data, Git repository | `scripts/Q3/spending/download_spending.py`, `scripts/Q3/spending/preprocesssing_spending.py`, `scripts/Q3/exchange/api_SNB.py`, `scripts/Q3/Q3_merge.py`, `scripts/Q3/Q3_analysis.py` , `requirements.txt`, `README.md`, `.gitignore`, `git repo management and structure` |


## Use of generative AI
 
| | Used for | Checked / decided by the team |
|---|---|---|
| Q1 | Improving and debugging Python code, refining data processing and visualizations, writing and improving Markdown documentation, and assisting with drafting, structuring, and polishing the project report. | checking the report and visual for accuracy and readibility |
| Q2 | Debugging the Playwright scraper; clarifying the syntax of both models (`statsmodels` OLS with HC1 standard errors and `linearmodels` PanelOLS with region and date effects); improving English wording on the report.| AI output was checked against documentation and tested |
| Q3 | Suggestions to improve and debug visualizations with matplotlib,  Debugging tips the marimo notebooks whenever necessary (e.g. shallow copy); clarifying `statsmodels` syntax for HC1 standard errors and VIF; polishing the English of the Q3 report to match style and repository structure section and the README.md | Collecting ideas for order-region classification, robustness check without COVID debug; every AI suggestion was reviewed by manually searching libraries and tested before committing | All research questions, methodological choices, analyses and conclusions were developed and checked by the team. |
 
