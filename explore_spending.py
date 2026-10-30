import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return


@app.cell
def _():
    import pandas as pd
    from scripts import config

    spending = pd.read_parquet(config.RAW_DIR / "raw_spending.parquet")
    print(spending.shape)
    print(spending.dtypes)
    print(spending.head(10))
    for col in spending.select_dtypes(exclude="number").columns:
        print(col, spending[col].nunique(), spending[col].unique()[:10])
    return


if __name__ == "__main__":
    app.run()
