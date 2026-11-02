# To-do Q2

## Acquisition
- set up env &rarr; ok
- reorganize holidays.py with functions &rarr; ok
- setup download html &rarr; ok
- download_spending: notebook rewritten  (functions, paths) &rarr; ok
- population.csv (manual BFS download) &rarr; ok

## Cleaning
- parse HTML data: date, holiday, class, canton,
  canton share, is below, share note &rarr; ok
- compare ch to canton level &rarr; ok
- parse population.csv: year, canton, population &rarr; ok
- cleaning_spending: rename columns, fix datatypes, filter 2019-2025 &rarr; ok
- drop code 9999 in region and category &rarr; ok
- checks: missing values, duplicates, negative/zero values, missing days &rarr; ok
- check missing days per region/category: none, all 7 x 7 combinations have 2557 days &rarr; ok

## Integration
- holiday share per region: canton holidays &times; population, summed per Grossregion &rarr; ok
  - class 1 and 2 = 1.0, class 3 (half-holiday) = 0.5, class 4 (not official) excluded
  - partial holidays use the scraped canton share; "varies"/"n.a." = 0
- build_df: merge spending + holiday share on date and region, no holiday = 0 &rarr; ok
- enrich: year, month, weekday, is_weekend, is_holiday (share &ge; 0.5),
  log_spending &rarr; ok
- output: data/processed/df_q2.parquet &rarr; ok

## Code structure
- change file names &rarr; ok
- merge requirements &rarr; ok
- move class labels to config &rarr; ok
- move settings and paths to config &rarr; ok
- one task per function, one pipeline stage per folder &rarr; ok
- fix main and inits &rarr; ok
- move outputs to processed &rarr; ok
- check pyarrow in requirements.txt &rarr; ok
- tell team to exclude requirements not used &rarr; open

## Analysis (Q2)
- add COVID flag &rarr; ok
- add map?
- regression: log spending on holiday share, weekday, month, year, region,
  holiday &times; category interaction &rarr; ok
- heatmap of holiday effect by region and category &rarr; ok
- weekday / month plots &rarr; ok

## Documentation
- methods: list cleaning steps and holiday choices (weights, class 4, threshold) &rarr; writing...
- README: my code contribution &rarr; open