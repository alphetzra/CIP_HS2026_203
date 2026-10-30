import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _(mo):
    import sys
    import pandas as pd

    sys.path.insert(0, str(mo.notebook_dir().parent))
    from scripts import config

    return config, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Exploration of the spending data

    Before writing `scripts/cleaning/cleaning_spending.py` we looked at the raw export of Monitoring Consumption Switzerland to decide which cleaning steps are needed. This notebook documents what we checked and what we found.

    1. Structure of the raw data
    2. Date range
    3. Code 9999 in region and category
    4. Check of the final table `df_q2`
    """)
    return


@app.cell
def _(config, pd):
    raw = pd.read_parquet(config.RAW_SPENDING)
    raw["Date"] = pd.to_datetime(raw["Date"])
    return (raw,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Structure of the raw data

    Columns, datatypes and the values of the text columns.
    """)
    return


@app.cell
def _(raw):
    print(raw.shape)
    print(raw.dtypes)
    for _col in ["Region", "Merchant category"]:
        print(f"\n{_col}: {raw[_col].nunique()} values")
        print(sorted(raw[_col].astype(str).unique()))
    raw.head(10)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. Date range

    The study period is 2019-2025. The export goes further, so
    `cleaning_spending` keeps only the years in `config.YEARS`.
    """)
    return


@app.cell
def _(raw):
    print("First day:", raw["Date"].min().date())
    print("Last day: ", raw["Date"].max().date())
    raw["Date"].dt.year.value_counts().sort_index().rename("rows")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Code 9999

    9999 appears in both columns:

    - Region 9999 = transactions in Liechtenstein and Campione d'Italia (documented in the source), not part of any Grossregion
    - Category 9999 = not documented in the source, which lists only seven categories. It is different from the existing category "Other", so we treat it as unassigned.

    Both are dropped in `cleaning_spending.drop_9999`.
    """)
    return


@app.cell
def _(raw):
    for _col in ["Region", "Merchant category"]:
        _n = (raw[_col].astype(str).str.strip() == "9999").sum()
        print(f"{_col} 9999: {_n} rows ({_n / len(raw):.1%})")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4. Check of the final table

    A complete table has one row per day, region and category:
    7 regions x 7 categories x 2557 days = 125,293 rows.
    Combinations with fewer rows have missing days.
    """)
    return


@app.cell
def _(config, pd):
    df_q2 = pd.read_parquet(config.DF_Q2)
    print(f"{len(df_q2)} rows (expected 125,293)")
    print(f"{df_q2['region'].nunique()} regions, {df_q2['category'].nunique()} categories")
    df_q2.groupby(["region", "category"], observed=True).size().rename("days").sort_values()
    return


if __name__ == "__main__":
    app.run()
