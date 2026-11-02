import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np 
    from pathlib import Path
    import pyarrow
    import matplotlib.pyplot as plt


    return Path, mo, np, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    """)
    return


@app.cell
def _(Path, pd):
    input_file = Path("../../data/raw/raw_spending.parquet")

    raw_spending = pd.read_parquet(input_file)
    return (raw_spending,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    """)
    return


@app.cell
def _(raw_spending):
    print(raw_spending.columns)
    return


@app.cell
def _(raw_spending):
    #renaming columns to remove spaces in the columns names

    spending = raw_spending.rename(columns={
        "Date": "date",
        "Region": "region",
        "Merchant category": "category",
        "Scaled Value": "spending",
        "Scaled Number of Transactions": "transactions",
        })
    return (spending,)


@app.cell
def _(spending):
    # After loading te parquet file, we print head, type of data and a quick statistical description
    print(spending.info)
    return


@app.cell
def _(spending):
    print(spending.describe(include="all"))
    return


@app.cell
def _(pd, spending):
    def convert_columns (x):
        x["date"] = pd.to_datetime(x["date"])
        x["region"] = x["region"].astype("category")
        x["category"] = x["category"].astype("category")
        x["spending"] = x["spending"].astype(float)
        return x

    convert_columns(spending)
    return


@app.cell
def _(spending):
    #we print again the statistics, to see if our conversions fix the output of the old statistics, NaN now appear in categorical values as its impossible to calculate certain summary statistics using Region and Merchant category

    print(spending.describe(include="all"))
    return


@app.cell
def _(pd, spending):
    #currently not the whole period covered by the dataset in in scoper for our project, therefore we will filter the date columns 
    #we can see that some regions are marked as 9999, we need to exclude them as part of our preprocessing
    #to combine both processes I will attempt a for loop to iterate into each row of the affected columns and keep those that do not match the criteria 


    print("CHECKING VALUES:")
    for x in ["date","region", "category","spending","transactions"]:
        as_text = spending[x].astype(str).str.strip()
        print()
        print(f"----------------- checking {x} ------------------")
        print(f"total rows containing '9999' in {x}: {(as_text == '9999').sum()}")
        print(f"total rows containing 'NaN' in {x}: {(spending[x].isna().sum())}")
        print(f"total rows with empty text in {x}: {(as_text == '').sum()}")

        if pd.api.types.is_numeric_dtype(spending[x]):
            print(f"negative values in {x}: {(spending[x] < 0).sum()}")
            print(f"zero values in {x}: {(spending[x] == 0).sum()}")
            print(f"min: {spending[x].min()}, max: {spending[x].max()}")
        else:
            print(f"number of unique values in {x}: {spending[x].nunique()}")
    print()

    print(f"duplicated rows: {spending.duplicated(subset=['date', 'region', 'category']).sum()}")
    print()


    #The output of the first loop showed ustat only columns region and category show the presence of 9999 and none of the columns contain NaN, we filter the 9999 values and the date range with boolean masks, which is faster and simpler than a loop

    print("FILTERING 9999:")
    # Filter out 9999 from both columns at once without a loop
    spending_filtered = spending[
        (spending["region"] != '9999') & 
        (spending["category"] != '9999')]

    # Calculate and print how many rows were removed
    rows_removed = len(spending) - len(spending_filtered)
    print(f"Total rows removed: {rows_removed}")
    print(f"Total rows remaining: {len(spending_filtered)}")
    print()

    #validating results by counting values x category in columns
    print("CHECKING COLUMNS AFTER FILTERING 9999:")
    print(spending_filtered["region"].value_counts())
    print()
    print("...")
    print()
    #looks like that 9999 is still within the dataframe, but with a count of 0, we use cat to remove the category 9999 that no rows use anymore in both region and category colums 
    print("REMOVING 9999 USING CAT:")
    spending_filtered["region"] = spending_filtered["region"].cat.remove_unused_categories()
    spending_filtered["category"] = spending_filtered["category"].cat.remove_unused_categories()
    print("...done")
    print()


    #validating results by counting values x category in columns
    print("CHECKING COLUMNS AGAIN:")
    print(spending_filtered["region"].value_counts())
    print()
    #As anticipated we do not need the total range of date, we define globally 2 variables start_date and end_date to correctly filter all the dates outside the hardcoded range

    print("FILTERING OUT OF DATA RANGE (2019-2025):")
    n_rows = len(spending_filtered)

    start_date = pd.to_datetime("2019-01-01")
    end_date = pd.to_datetime("2025-12-31")

    spending_filtered = spending_filtered[
        (spending_filtered["date"] >= start_date) & 
        (spending_filtered["date"] <= end_date)]

    rows_removed = n_rows - len(spending_filtered)
    print(f"Total rows removed: {rows_removed}")
    print(f"Total rows remaining: {len(spending_filtered)}")
    print()

    #Quick check on te new dataset info
    print(spending_filtered.info())
    return (spending_filtered,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    """)
    return


@app.cell
def _(spending_filtered):
    #Outliers are searched within each region and category with a standard IQR rule ( +- 1.5IQR)

    print("CHECKING OUTLIERS:")
    print()

    group = spending_filtered.groupby(["region", "category"], 
                                      observed=True)["spending"]

    q1 = group.transform(lambda x: x.quantile(0.25))
    q3 = group.transform(lambda x: x.quantile(0.75))
    iqr = q3 - q1

    lower_limit = q1 - 1.5 * iqr
    upper_limit = q3 + 1.5 * iqr

    spending_filtered["is_outlier"] = (spending_filtered["spending"] < lower_limit) | (spending_filtered["spending"] > upper_limit)

    print(f"Sum of the outliers found: {spending_filtered['is_outlier'].sum()} of {len(spending_filtered)} rows")
    print()

    print(spending_filtered.groupby("category", observed=True)["is_outlier"].sum())
    print()


    print("CHECKING INFO AGAIN:")
    spending_filtered.info()
    print()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The outlier detection phase is now concluded, we move on to build features to subsequent anaylses


    - adding more granularity by adding a single columns for year, month, weekday and weekend

    - flag COVID period (hardcoded)

    - creating a dict of regions with cantons at the border

    - we
    """)
    return


@app.cell
def _(spending_filtered):
    print("ADDING NEW COLUMNS:")

    #Calendar columns (calendar effects for the regressions)
    spending_filtered["year"] = spending_filtered["date"].dt.year
    spending_filtered["month"] = spending_filtered["date"].dt.month
    spending_filtered["weekday"] = spending_filtered["date"].dt.weekday   #0 = Monday, 6 = Sunday
    spending_filtered["is_weekend"] = spending_filtered["weekday"] >= 5

    #COVID flag: from the first lockdown until the end of most measures
    spending_filtered["covid_period"] = spending_filtered["date"].between("2020-03-16", "2022-12-31")

    #Border regions: Grossregions containing a canton with a main cross-border shopping area
    border_countries = {
        "Lake Geneva": "France",     #GE
        "Northwestern": "Germany",   #BS, BL
        "Eastern": "Germany",        #SH, TG
        "Ticino": "Italy",           #TI
    }

    spending_filtered["border_region"] = spending_filtered["region"].isin(border_countries.keys())
    spending_filtered["border_country"] = spending_filtered["region"].astype(str).map(border_countries)




    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now we simply create one plot for the distributions
    """)
    return


@app.cell
def _(spending_filtered):
    def _():
        import matplotlib.pyplot as plt

        print("CHECKING DISTRIBUTIONS PER CATEGORY:")
        columns = ["spending", "transactions"]
        categories = spending_filtered["category"].cat.categories
        colors = {"spending": "green", "transactions": "darkorange"}

        fig, axes = plt.subplots(
            len(columns), len(categories), figsize=(20, 8)
        )
        for row, x in enumerate(columns):
            for col, cat in enumerate(categories):
                data = spending_filtered[spending_filtered["category"] == cat][
                    x
                ]
                ax = axes[row, col]
                ax.hist(data, bins=50, color=colors[x])
                ax.set_title(
                    f"{cat}\n(skewness: {data.skew():.2f})", fontsize=9
                )
                ax.set_xlabel(f"{x} (scaled)", fontsize=8)
            axes[row, 0].set_ylabel("Number of rows")
        plt.tight_layout()
        return plt.show()

    _()
    return


@app.cell
def _(np, spending_filtered):
    spending_clean = spending_filtered.copy()


    #The data is right skewed, so we apply a log transformation to spending

    spending_clean["log_spending"] = np.log(spending_clean["spending"])


    #transactions is not used in any research question, so it is removed (delete this line if you want to use transactions in one of your analyses)

    spending_clean = spending_clean.drop(columns=["transactions"])


    spending_clean.info()
    return (spending_clean,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    now that we cleaned the data, detected our outliers (which we keep because are whitin scope of our analysis) and build all necessary features the data gets saved again in a parquet file in the folder interim, we will do a final merging for each research question that will subsequently be saved in processed
    """)
    return


@app.cell
def _(Path, spending_clean):
    output_file = Path("../../data/interim/clean_spending.parquet")

    spending_clean.to_parquet(output_file, index=False)

    return


if __name__ == "__main__":
    app.run()
