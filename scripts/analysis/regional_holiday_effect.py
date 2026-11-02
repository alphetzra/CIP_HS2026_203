"""Analysis Q2 - effect of a regional holiday on spending, compared with regions where the
same date is a normal working day.

1. Introduction

Answers the second part of Q2. Per merchant category, a panel regression
with region and date fixed effects: log_spending ~ holiday_share + region effect + date effect
The date effect compares the regions with each other on the same day.
Everything that affects all regions equally on that day (weekday, season,
COVID, national holidays, weather, ...) cancels out. The holiday effect
is therefore measured only on days when some regions have a holiday and
others do not.

2. Data

-------------------------------------------------------------------------------------------
| Input                                  | Output                                          |
|----------------------------------------|-------------------------------------------------|
| data/processed/df_q2.parquet           | results/tables/holiday_effect_regional_only.csv |
| results/tables/holiday_effect_all.csv  | results/figures/holiday_effects.png             |
-------------------------------------------------------------------------------------------

3. Script description

1. Read df_q2 and convert region to text (the panel index cannot use a
   categorical column).
2. Per category: panel regression (PanelOLS) with region and date effects.
3. Convert the holiday_share coefficient to a % change with 95% confidence
   interval.
4. Save the table and draw a coefficient plot comparing both estimates:
   all holidays (calendar model) vs. regional holidays only.

4. Notes

- holiday_share goes from 0 to 1, so the coefficient is the effect of a full
  holiday (whole region off). % change = (exp(b) - 1) * 100.
- Standard errors: cov_type="kernel" (Driscoll-Kraay), robust to correlation
  between regions on the same day and over time.
- Only 7 regions: the estimate relies on relatively few regional holidays.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
from scripts import config


def load_df() -> pd.DataFrame:
    """Read df_q2 and prepare the region column for the panel index."""
    df = pd.read_parquet(config.DF_Q2)
    df = df.dropna(subset=[config.TARGET]).copy()
    df["region"] = df["region"].astype(str)
    return df


def fit_category(cat_df: pd.DataFrame):
    """Panel regression for one category with region and date effects."""
    # PanelOLS needs a two-level index: (entity, time) = (region, date)
    panel = cat_df.set_index(["region", "date"])
    model = PanelOLS(panel[config.TARGET], panel[["holiday_share"]],
                     entity_effects=True,     # region effect: level differences between regions
                     time_effects=True)       # date effect: : everything common to all regions on a day
    return model.fit(cov_type="kernel")


def holiday_effect(result) -> dict:
    """Coefficient of holiday_share as % change, with 95% confidence interval."""
    b = result.params["holiday_share"]
    low, high = result.conf_int().loc["holiday_share"]
    to_pct = lambda x: (np.exp(x) - 1) * 100        # log points -> % change
    return {"effect_pct": to_pct(b), "ci_low": to_pct(low), "ci_high": to_pct(high),
            "p_value": result.pvalues["holiday_share"], "n_obs": int(result.nobs)}


def regional_effect_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Holiday effect per category, estimated from regional holidays only."""
    rows = {}
    for category, cat_df in df.groupby("category", observed=True):
        rows[category] = holiday_effect(fit_category(cat_df))
    # .T: categories as rows
    return pd.DataFrame(rows).T.round(3).sort_values("effect_pct")


def plot_effects(regional: pd.DataFrame, all_holidays: pd.DataFrame) -> None:
    """Coefficient plot: both estimates per category with 95% confidence intervals."""
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


def run() -> None:
    """Fit the panel models, save the table and the coefficient plot."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)

    regional = regional_effect_by_category(load_df())
    regional.to_csv(config.TABLES_DIR / "holiday_effect_regional_only.csv")
    print("Regional holiday effect per category (% change on a full holiday):\n", regional)

    # estimate from calendar_regression.py, for the comparison in the plot
    all_holidays = pd.read_csv(config.TABLES_DIR / "holiday_effect_all.csv", index_col=0)
    plot_effects(regional, all_holidays)
    print(f"Figure saved to {config.FIGURES_DIR / 'holiday_effects.png'}")


if __name__ == "__main__":
    run()