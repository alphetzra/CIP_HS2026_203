import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd  #https://pandas.pydata.org/docs/user_guide/index.html#user-guide
    from pathlib import Path #https://docs.python.org/3/library/pathlib.html
    import pyarrow #used to read and write the parquet files
    from scripts import config
    from scripts.Q2.integration.build_df import get_build_df

    return config, get_build_df, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Q3 - Merging spending, exchange rate and holidays

    ## 1. Introduction


    This notebook is created to build the final dataset used to answer Q3:

    - Q3: _Is **spending** in border regions more strongly affected by a decrease in EUR/CHF exchange rate than **spending** in non-border regions, and does this effect differ between border regions?_

    ## 2. Data sources

    | File | Content | Level | Folder |
    | --- | --- | --- | --- |
    | `clean_spending.parquet` | Cleaned daily spending with calendar, COVID and border-region columns | date x region x category | `data/interim/` |
    | `raw_exchange.parquet` | Monthly average EUR/CHF rate from the SNB | month | `data/raw/` |
    | `region_holiday_sharein.csv` | Share of residents with a public holiday (0 to 1), only for holiday dates | date x region | `data/interim/` |

    ## 3. Script description
    1. **Load** the three files
    2. **Check and prepare the exchange rate:** it is only 84 values (which we verified during API request), so it is checked and converted here and not in a separate cleaning script
    3. **Check and prepare the holiday file**
    4. **Merge** the exchange rate on `year` and `month`, the holidays on `date` and `region` (never by row index, since the files have a different number of rows per date)
    5. **Validate** the merged dataset and save it into `data/processed/`
    """)
    return


@app.cell
def _(config):
    #Setting global variables
 
    spending_file = config.CLEAN_SPENDING

    exchange_file = config.RAW_EXCHANGE

    output_file = config.DF_Q3
    return exchange_file, output_file, spending_file


@app.cell
def _(exchange_file, get_build_df, pd, spending_file):
    #Now we load the all the data using pandas, respectively for csv and parquet, the csv file is fruit of a different retrieval and cleaning pipeline part of Q2 

    spending = pd.read_parquet(spending_file)
    raw_exchange = pd.read_parquet(exchange_file)
    raw_holiday = get_build_df()
    return raw_exchange, raw_holiday, spending


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Check exchange

    Exchange date was retrieved by REST API in a previous script, we didn't create a dedicate preprocessing file due to the simplicity of the data

    We do here a limited quality check to confirm our assumption
    """)
    return


@app.cell
def _(raw_exchange):
    #I do a quick quality check for the exchange rate file

    print("CHECKING EXCHANGE RATE:")
    print()

    #as we introduced previusly we except 82 rows (montly data from 2019 to 2025)
    print(f"- Number of rows: {len(raw_exchange)} (expected 84)")

    #check for NAs
    print(f"- Number of NaN: {raw_exchange['value'].isna().sum()}")

    #check for min/max
    print(f"- Minimum value: {raw_exchange['value'].min()}, Maximum value: {raw_exchange['value'].max()}")
    return


@app.cell
def _(pd, raw_exchange):
    #Working on columns (1. renaming, 2. convert to pd_datetime...)
 
    exchange = raw_exchange.rename(columns={"value": "eur_chf"})

    exchange["date"] = pd.to_datetime(exchange["date"])

    exchange["year"] = exchange["date"].dt.year

    exchange["month"] = exchange["date"].dt.month

    exchange = exchange[["year", "month", "eur_chf"]]
 
    print(exchange.head())
    return (exchange,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Holidays check

    This was building from Q2 from the cantonal holidays, and the share was calculated by weighting by population

    The file should be clean but we run the same pipeline we run for the 'exchange' file to let data speak for us
    """)
    return


@app.cell
def _(pd, raw_holiday, spending):
    print("CHECKING HOLIDAYS:")
    print()

    #check for NAs
    print(f"- Number of NaN: {raw_holiday['holiday_share'].isna().sum()}")

    #check for min/max
    print(f"- Minimum value: {raw_holiday['holiday_share'].min()}, / Maximum value: {raw_holiday['holiday_share'].max()}")

    #check for duplicated rows
    print(f"- Number of duplicated rows: {raw_holiday.duplicated(subset=['date', 'region']).sum()}")
 
    #region names that are in the holiday file but not in the spending data (should end up printing an empty set "set()")

    #Creating a set of regions from each dataframe, its a list of unique values and let me subtract, since unordered position does not matter in this operation. 

    unknown_regions = set(raw_holiday["region"]) - set(spending["region"])

    print(f"- Regions not found in spending: {unknown_regions}")
    print()
                          
    #creating a copy of raw_holiday (otherwise marimo gives an error as it doesn't allow us to re-define a variable previusly used)
    holiday = raw_holiday.copy()

    holiday["date"] = pd.to_datetime(holiday["date"])

    #we print the total range wich should be included from 01.01.2019 to 31.12.2025
    print(f"- Total period: {holiday['date'].min().date()} to {holiday['date'].max().date()}")
    return (holiday,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Merging

    In this part of the script the **exchange rate** is merged (left join) on **year** and **month** --> in this way every row of the spending file will get the exchange rate of that specific month

    Subsequently the **holiday** dataset is merged (left join) on **date** and *region**
    """)
    return


@app.cell
def _(exchange, holiday, spending):
    print("MERGING...")
 
    q3_merge = spending.copy()

    #we have to do this because if we don't convert the region into strings again they will be considered categories while in the holiyas region would be of str type
    q3_merge["region"] = q3_merge["region"].astype(str)

    #LEFT JOIN of exchange on the shallow copy of spending data
    q3_merge = q3_merge.merge(exchange, on=["year", "month"], how="left")

    #LEFT JOIN of exchange on the shallow copy of spending data (which was previusly joined with the exchange data)
    q3_merge = q3_merge.merge(holiday, on=["date", "region"], how="left")

    q3_merge["holiday_share"] = q3_merge["holiday_share"].fillna(0)

    #we reconvert region to category type again
    q3_merge["region"] = q3_merge["region"].astype("category")

    print("...")
    print("Done!")
    return (q3_merge,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Join quality check

    The # of rows should match the len of spending dataset and every row should have an exchange rate euro_chf
    """)
    return


@app.cell
def _(q3_merge, spending):
    print("CHECKING MERGE:")

    #Checking if we get the same number of rows
    print(f"- Number of rows before merging: {len(spending)}")
    print(f"- Number of rows after merging: {len(q3_merge)}")

    #Checking if echange rate also has 
    print(f"- Number of rows without exchange rate: {q3_merge['eur_chf'].isna().sum()}")

    print(f"- Number of rows with a holiday: {(q3_merge['holiday_share'] > 0).sum()}")

    print()


    #we can conveniently use .info to display an overall summary
    q3_merge.info()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Saving

    Just saving the output as parquet in the right folder
    """)
    return


@app.cell
def _(output_file, q3_merge):
    q3_merge.to_parquet(output_file, index=False)

    print(f"Saved {len(q3_merge)} rows to {output_file.resolve()}")
    return


if __name__ == "__main__":
    app.run()
