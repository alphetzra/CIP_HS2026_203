"""Describe how spending varies by weekday and month, per merchant category."""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scripts import config

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def swiss_daily_total(df: pd.DataFrame) -> pd.DataFrame:
    """Sum the seven regions -> one national value per date and category."""
    return (df.groupby(["date", "category", "weekday", "month"], observed=True, as_index=False)
              ["scaled_value"].sum())


def spending_index(daily: pd.DataFrame, by: str) -> pd.DataFrame:
    """Average spending per category and weekday/month as an index (100 = average day)."""
    mean = daily.groupby(["category", by], observed=True)["scaled_value"].mean().unstack(by)
    return (mean.div(mean.mean(axis=1), axis=0) * 100).round(1)


def plot_spending_index(weekday: pd.DataFrame, month: pd.DataFrame) -> None:
    """Heatmaps side by side: category x weekday and category x month."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 5), gridspec_kw={"width_ratios": [7, 12]})
    settings = dict(annot=True, fmt=".0f", cmap="RdBu_r", center=100, vmin=0, vmax=200,
                    cbar=False, linewidths=0.5)

    sns.heatmap(weekday, ax=axes[0], **settings)
    axes[0].set_title("By weekday")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Merchant category")

    sns.heatmap(month.set_axis(MONTH_LABELS, axis=1), ax=axes[1], yticklabels=False, **settings)
    axes[1].set_title("By month")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("")

    fig.suptitle("Spending index by weekday and month (100 = average day of the category), "
                 f"Switzerland {min(config.YEARS)}-{max(config.YEARS)}")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "spending_index.png", dpi=200)
    plt.close(fig)


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