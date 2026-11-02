"""Analysis Q2 - descriptive spending index by weekday and month.

1. Introduction

Descriptive overview of the calendar pattern in spending: for each
merchant category, how spending on each weekday and in each month
compares with the category's overall average.

2. Data

-----------------------------------------------------------------------------
| Input                        | Output                                      |
|------------------------------|---------------------------------------------|
| data/processed/df_q2.parquet | results/tables/weekday_index.csv            |
|                              | results/tables/month_index.csv              |
|                              | results/figures/spending_index_weekday.png  |
|                              | results/figures/spending_index_month.png    |
-----------------------------------------------------------------------------

3. Script description

1. Sum the 7 regions per date and category -> one Swiss value per day.
2. Average spending per category and weekday/month.
3. Divide by the average over all weekdays/months of that category and
   multiply by 100 -> index (100 = average).
4. Save the tables and draw one heatmap each (category x weekday,
   category x month).

4. Notes

- The spending values are scaled, not CHF, so only relative values are compared.
- Indexing per category makes categories with very different spending
  levels comparable in one figure.
- Simple averages over all days: holidays and the COVID period are included, so
  the weekday and month values partly reflect these other effects. They are
  separated in the regression (calendar_regression.py).
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scripts import config

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def swiss_daily_total(df: pd.DataFrame) -> pd.DataFrame:
    """Sum the seven regions -> one national value per date and category."""
    # weekday and month are in the groupby only to keep them as columns
    return (df.groupby(["date", "category", "weekday", "month"], observed=True, as_index=False)
              ["spending"].sum())


def spending_index(daily: pd.DataFrame, by: str) -> pd.DataFrame:
    """Average spending per category and weekday/month as an index (100 = average day)."""
    mean = daily.groupby(["category", by], observed=True)["spending"].mean().unstack(by)
    return (mean.div(mean.mean(axis=1), axis=0) * 100).round(1)


def _plot_heatmap(index: pd.DataFrame, title: str, filename: str, cell_width: float) -> None:
    """Heatmap of category x period."""
    n_rows, n_cols = index.shape
    fig, ax = plt.subplots(figsize=(3 + n_cols * cell_width, 1.5 + n_rows * 0.5))
    # diverging colors centred on 100: blue = below average, red = above;
    # fixed scale 0-200 so both heatmaps use the same colors
    sns.heatmap(index, ax=ax, annot=True, fmt=".0f", cmap="RdBu_r", center=100,
                vmin=0, vmax=200, linewidths=0.5,
                cbar_kws={"label": "Index (100 = average day)", "shrink": 0.8})
    ax.set_title(f"{title}, Switzerland {min(config.YEARS)}-{max(config.YEARS)}")
    ax.set_xlabel("")
    ax.set_ylabel("Merchant category")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / filename, dpi=200)
    plt.close(fig)


def plot_spending_index(weekday: pd.DataFrame, month: pd.DataFrame) -> None:
    """Heatmaps: category x weekday and category x month."""
    _plot_heatmap(weekday, "Spending index by weekday", "spending_index_weekday.png",
                  cell_width=1.0)
    _plot_heatmap(month.set_axis(MONTH_LABELS, axis=1), "Spending index by month",
                  "spending_index_month.png", cell_width=0.8)


def run() -> None:
    """Compute the weekday and month spending index, save tables and figure."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)

    daily = swiss_daily_total(pd.read_parquet(config.DF_Q2))
    weekday = spending_index(daily, "weekday")
    month = spending_index(daily, "month")

    weekday.to_csv(config.TABLES_DIR / "weekday_index.csv")
    month.to_csv(config.TABLES_DIR / "month_index.csv")
    plot_spending_index(weekday, month)
    print(f"Spending index saved to {config.FIGURES_DIR}")


if __name__ == "__main__":
    run()