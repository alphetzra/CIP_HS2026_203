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

## Contributions

| Member | Research question | Code |
|---|---|---|
| Morteza Nejati | Q1: major events in Zürich | *to be completed* |
| **Laura Da Silva Cunha** | Q2: calendar and public holidays | `main.py`, `scripts/config.py`, `scripts/acquisition/scrape_holidays.py`, `scripts/acquisition/download_spending.py`, `scripts/cleaning/cleaning_holidays.py`, `scripts/cleaning/cleaning_population.py`, `scripts/cleaning/cleaning_spending.py`, `scripts/integration/holiday_share.py`, `scripts/integration/build_df.py`, `scripts/analysis/calendar_index.py`, `scripts/analysis/calendar_regression.py`, `scripts/analysis/regional_holiday_effect.py` |
| Salvatore Nicolosi | Q3: EUR/CHF and border regions | *to be completed* |
