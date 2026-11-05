"""Analysis Q2 - descriptive spending index by weekday and month.

Descriptive overview of the calendar pattern in spending: for each merchant
category, how spending on each weekday and in each month compares with the
category's average (index, 100 = average day). Tables are saved to
results/tables, heatmaps to results/figures.

Specifics:
- The seven regions are summed per date and category, so the index
  describes Switzerland as a whole.
- The spending values are scaled, not CHF, so only relative values are
  compared. Indexing per category makes categories with very different
  spending levels comparable in one figure.
- Simple averages over all days: holidays and the COVID period are included,
  so the weekday and month values partly reflect these effects. They are
  separated in the regression (calendar_regression.py).
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from scripts.Q2.integration.build_df import get_build_df
from scripts import config

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def swiss_daily_total(df: pd.DataFrame) -> pd.DataFrame:
    """Sum the seven regions into one Swiss value per date and category.
        Args:
            df: Q2 table
        Returns:
            DataFrame with date, category, weekday, month and spending
        """

    # weekday and month are in the groupby only to keep them as columns
    return (df.groupby(["date", "category", "weekday", "month"], observed=True, as_index=False)
              ["spending"].sum())


def spending_index(daily: pd.DataFrame, by: str) -> pd.DataFrame:
    """Compute the average spending per category and period as an index.
        Args:
            daily: Output of swiss_daily_total()
            by: "weekday" or "month"
        Returns:
            DataFrame with categories as rows and periods as columns
            (100 = average of that category)
        """

    mean = daily.groupby(["category", by], observed=True)["spending"].mean().unstack(by)
    return (mean.div(mean.mean(axis=1), axis=0) * 100).round(1)


def plot_heatmap(index: pd.DataFrame, title: str, filename: str, cell_width: float) -> None:
    """Plot an index table as heatmap (category x period) and save it.
        Args:
            index: Output of spending_index()
            title: Figure title, the period and years are added
            filename: File name in config.FIGURES_DIR
            cell_width: Width per column in inches
        """

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
    """Plot the weekday and the month index as heatmaps.
            Args:
                weekday: Weekday index from spending_index()
                month: Month index from spending_index()
            """

    plot_heatmap(weekday, "Spending index by weekday", "spending_index_weekday.png",
                  cell_width=1.0)
    plot_heatmap(month.set_axis(MONTH_LABELS, axis=1), "Spending index by month",
                  "spending_index_month.png", cell_width=0.8)


def run_calendar_index() -> None:
    """Compute the weekday and month spending index, save tables and figure."""

    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)

    daily = swiss_daily_total(get_build_df())
    weekday = spending_index(daily, "weekday")
    month = spending_index(daily, "month")

    weekday.to_csv(config.TABLES_DIR / "weekday_index.csv")
    month.to_csv(config.TABLES_DIR / "month_index.csv")
    plot_spending_index(weekday, month)
    print(f"Spending index saved to {config.FIGURES_DIR}")

