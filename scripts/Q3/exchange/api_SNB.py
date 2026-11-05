import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import sys
    import requests
    import json
    import pandas as pd #https://pandas.pydata.org/docs/user_guide/index.html#user-guide
    from pathlib import Path  #https://docs.python.org/3/library/pathlib.html

    #add the repo root (the folder that contains scripts/config.py) to the Python path,
    #so that the import below finds our own scripts folder and not a pip package
    _root = next(p for p in Path(__file__).resolve().parents if (p / "scripts" / "config.py").exists())
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

    from scripts import config

    return config, mo, pd, requests


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SNB Exchange rate data aquisition - API call

    This script handle the retrieval (using requests) and storage of EUR/CHF exchange rates from the Swiss National Bank (SNB) API.

    ### Workflow:
    1. **Slider:** Uses a `marimo` range slider (hidden script) to let the user dynamically select the start and end years, which is partially unrelevant for the project itself but allows further exploration if retained necessary.
    2. **API request** Fetches the targeted time-series data via a REST API request using `requests`.
    3. **Conversion to DataFrame:** Parses the nested JSON response and extracts the core observations into a pandas DataFrame.
    4. **Store data as parquet** Saves the DataFrame into `raw_exchange.parquet`.


    DISCLAMER: it is not necessary to save such file as a parquet due to the limited amout of rows and simplicity of the data, but we kept parquet to being aligned across the different datasets
    """)
    return


@app.cell(hide_code=True)
def slider_datarange(mo):
    date_range = mo.ui.range_slider(
        start=1970,
        stop=2025,
        step=1,
        value=[2019, 2025],
        label="Select the data range",
    )
    return (date_range,)


@app.cell
def _(date_range):
    date_range
    return


@app.cell
def _(date_range, pd, requests):
    from_date, to_date = date_range.value

    x = requests.get(f'https://data.snb.ch/api/cube/devkum/data/json/en?dimSel=D0(M0),D1(EUR1)&fromDate={from_date}-01&toDate={to_date}-12')
    print(x.status_code)

    #parse answer
    raw_exchange_json = x.json()
    print(type(raw_exchange_json))

    raw_exchange_pd = pd.DataFrame(raw_exchange_json["timeseries"][0]["values"])
    print(type(raw_exchange_pd))
    print(raw_exchange_pd)


    return (raw_exchange_pd,)


@app.cell
def _(config, raw_exchange_pd):
    output_folder = config.RAW_EXCHANGE

    raw_exchange_pd.to_parquet(output_folder, index=False)
    return


if __name__ == "__main__":
    app.run()
