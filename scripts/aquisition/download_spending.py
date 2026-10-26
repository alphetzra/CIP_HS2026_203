import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Spending data aquisition

    ## 1. Introduction

    Spending data is essential for the project, in fact they are used to answer all the Research Questions part of it
    - Q1: _How do major events (# of participants) in Canton Zürich affect daily POS **spending** across different merchant categories compared with similar non-event days?_
    - Q2:	_How much of the daily variation in **spending** by category is explained by calendar effects (weekday, month, public raw_holidays)? Specifically, how does a regional public holiday change **spending** by category in regions where it applies, compared with regions where the same date is a normal working day?_
    - Q3:	_Is **spending** in border regions more strongly affected by a decrease in EUR/CHF exchange rate than **spending** in non-border regions, and does this effect differ between border regions?_


    ## 2. Data source

    For this project, spending data are:

    | Source | Content | Method of Acquisition |
    | --- | --- | --- |
    | Monitoring Consumption Switzerland | Daily scaled card spending by Grossregion and category, 2019-2025 | Download |

    ## 3. Script description
    This notebook downloads the daily card-payment data from **Monitoring Consumption Switzerland** and stores it unchanged in `data/raw/`

    **Notes:**
    - The spending values are scaled, not CHF amounts, so only relative changes are interpreted.
    - No cleaning is done here. Filtering (e.g. dropping region 9999), type conversion and handling of missing values happen in the cleaning notebook.
    """)
    return


@app.cell
def _():
    #Importing modules, this is used as a reference for which modules are exaclty used in this script

    import pandas as pd  #https://pandas.pydata.org/docs/user_guide/index.html#user-guide
    from pathlib import Path  #https://docs.python.org/3/library/pathlib.html
    import pyarrow #used to generate the parquet file

    return Path, pd


@app.cell
def _(Path):
    #Setting global variables

    url = ("https://drive.switch.ch/index.php/s/yLISs3KVE7ASE68/download?path=/2_ACQUIRING%20DATA&files=ACQ_POS_Grossregion_NOGA.csv")

    output_folder = Path("../../data/raw/raw_spending.parquet")
    return output_folder, url


@app.cell
def _(output_folder, pd, url):
    #Using pandas and 

    raw_spening = pd.read_csv(url)
    raw_spening.to_parquet(output_folder, index=False)
    print(f"Saved {len(raw_spening)} rows to {output_folder}")
    return


if __name__ == "__main__":
    app.run()
