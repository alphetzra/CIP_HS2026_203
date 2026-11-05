"""Analysis Q2 - effect of a regional holiday on spending, compared with regions where the
same date is a normal working day.

Specifics:
- The date effect absorbs everything that all regions share on a day,
  including national holidays. The holiday effect is therefore only
  estimated from regional holidays.
- Kernel standard errors are used, because spending on one day is
  correlated with nearby days and with other regions on the same day.
- The plot compares this estimate with "all holidays" from calendar_regression.py.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
from scripts.Q2.analysis.calendar_regression import holiday_effect
from scripts.Q2.integration.build_df import get_build_df
from scripts import config


def load_df() -> pd.DataFrame:
    """Load the Q2 table and prepare it for the panel index.
        Returns:
            Q2 table without missing log_spending, region as text
        """
    df = get_build_df()
    df = df.dropna(subset=[config.TARGET]).copy()
    df["region"] = df["region"].astype(str)
    return df


def fit_category(cat_df: pd.DataFrame):
    """Fit the panel regression with region and date effects for one category.
        Args:
            cat_df: Q2 table for one category
        Returns:
            Fitted PanelOLS result
        """

    panel = cat_df.set_index(["region", "date"])
    model = PanelOLS(panel[config.TARGET], panel[["holiday_share"]],
                     entity_effects=True,  # region effect: levels differences between regions
                     time_effects=True)       # date effect: everything common to all regions on a day
    return model.fit(cov_type="kernel")


def regional_effect_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate the regional holiday effect for every category.
        Args:
            df: Q2 table
        Returns:
            DataFrame with one row per category, sorted by effect_pct
        """

    rows = {}
    for category, cat_df in df.groupby("category", observed=True):
        rows[category] = holiday_effect(fit_category(cat_df))
    # .T: categories as rows
    return pd.DataFrame(rows).T.round(3).sort_values("effect_pct")


def plot_effects(regional: pd.DataFrame, all_holidays: pd.DataFrame) -> None:
    """Plot both holiday effects per category with 95% intervals and save it.
        Args:
            regional: Output of regional_effect_by_category()
            all_holidays: Holiday effect per category from calendar_regression.py
        """

    order = regional.index
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(9, 5))
    # shift: the two estimates are drawn slightly above/below each other
    for table, label, shift, color in [(all_holidays, "All holidays (calendar model)", 0.15, "#4C72B0"),
                                       (regional, "Regional holidays only (same-date comparison)", -0.15, "#C44E52")]:
        t = table.loc[order]
        # error bar = distance from the estimate to the lower/upper CI bound
        errors = [t["effect_pct"] - t["ci_low"], t["ci_high"] - t["effect_pct"]]
        ax.errorbar(t["effect_pct"], y + shift, xerr=errors, fmt="o", capsize=3,
                    color=color, label=label)
    ax.axvline(0, color="grey", linewidth=1)     # 0 = no effect
    ax.set_yticks(y, order)
    ax.set_xlabel("% change in spending on a full holiday (95% confidence interval)")
    ax.set_title("Effect of a public holiday on spending by merchant category")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "holiday_effects.png", dpi=200)
    plt.close(fig)


def run_regional_holiday_effect() -> None:
    """Fit the panel models and save the table and the coefficient plot."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)

    regional = regional_effect_by_category(load_df())
    regional.to_csv(config.TABLES_DIR / "holiday_effect_regional_only.csv")
    print("Regional holiday effect per category (% change on a full holiday):\n", regional)

    # estimate from calendar_regression.py, for comparison in the plot
    all_holidays = pd.read_csv(config.TABLES_DIR / "holiday_effect_all.csv", index_col=0)
    plot_effects(regional, all_holidays)
    print(f"Figure saved to {config.FIGURES_DIR / 'holiday_effects.png'}")

