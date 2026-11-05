# To-do Q2

## Acquisition
- set up env &rarr; ok
- reorganize holidays.py with functions &rarr; ok
- setup download html &rarr; ok
- scrape with Playwright &rarr; ok
- cache every page as HTML, skip pages already downloaded &rarr; ok
- population.csv &rarr; ok

## Cleaning
- parse HTML data: date, holiday, class, canton,
  canton share, is below, share note &rarr; ok
- compare ch to canton level &rarr; ok
- parse population.csv: year, canton, population &rarr; ok
- check population: no missing values, duplicates, all canton/year combinations &rarr; ok

## Integration
- holiday share per region: canton holidays &times; population, summed per Grossregion &rarr; ok
  - class 1 and 2 = 1.0, 3 = 0.5, 4 excluded
  - partial holidays use the scraped canton share; "varies"/"n.a." = 0
  - several holidays on one day: maximum share
  - population of the same year
- build_df: merge spending + holiday share on date and region, no holiday = 0 &rarr; ok
- output: data/processed/df_q2.parquet &rarr; ok

## Code structure
- change file names &rarr; ok
- merge requirements &rarr; ok
- move class labels to config &rarr; ok
- move settings and paths to config &rarr; ok
- one task per function, one pipeline stage per folder &rarr; ok
- fix main &rarr; ok
- move outputs to processed &rarr; ok
- change requirements.txt &rarr; ok

## Analysis (Q2)
- weekday/month spending index (100 = average day) &rarr; ok
- weekday/month plots &rarr; ok
- regression per category: log spending on region, weekday, month, year,
  COVID, holiday share &rarr; ok
- R² step by step: share of within-region variation per group &rarr; ok
- robust standard errors (HC1) &rarr; ok
- heatmap of holiday effect by region and category &rarr; ok
- panel model with region and date effects (regional holidays only) &rarr; ok
- coefficient plot: all holidays vs. regional holidays &rarr; ok

## Documentation
- report Q2 &rarr; ok
- README &rarr; ok
- ADR &rarr; ok