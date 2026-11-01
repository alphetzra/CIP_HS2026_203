"""How does a regional holiday change spending, compared with regions where the
same date is a normal working day?"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
from scripts import config

TARGET = "log_scaled_value"


def load_df() -> pd.DataFrame:
    """Read df_q2 and drop days without a log value (spending 0)."""
    df = pd.read_parquet(config.DF_Q2)
    df = df.dropna(subset=[TARGET]).copy()
    df["region"] = df["region"].astype(str)     # panel index needs plain text, not category
    return df


def fit_category(cat_df: pd.DataFrame):
    """Panel regression for one category with region and date effects."""
    # PanelOLS needs a two-level index: (entity, time) = (region, date)
    panel = cat_df.set_index(["region", "date"])
    model = PanelOLS(panel[TARGET], panel[["holiday_share"]],
                     entity_effects=True,     # region effect
                     time_effects=True)       # date effect
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
    return pd.DataFrame(rows).T.round(3).sort_values("effect_pct")


def plot_effects(regional: pd.DataFrame, all_holidays: pd.DataFrame) -> None:
    """Coefficient plot: both estimates per category with 95% confidence intervals."""
    order = regional.index
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(9, 5))
    for table, label, shift, color in [(all_holidays, "All holidays (calendar model)", 0.15, "#4C72B0"),
                                       (regional, "Regional holidays only (same-date comparison)", -0.15, "#C44E52")]:
        t = table.loc[order]
        errors = [t["effect_pct"] - t["ci_low"], t["ci_high"] - t["effect_pct"]]
        ax.errorbar(t["effect_pct"], y + shift, xerr=errors, fmt="o", capsize=3,
                    color=color, label=label)
    ax.axvline(0, color="grey", linewidth=1)
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
    regional.to_csv(config.TABLES_DIR / "holiday_effect_regional.csv")
    print("Regional holiday effect per category (% change on a full holiday):\n", regional)

    all_holidays = pd.read_csv(config.TABLES_DIR / "holiday_effect_all.csv", index_col=0)
    plot_effects(regional, all_holidays)
    print(f"Figure saved to {config.FIGURES_DIR / 'holiday_effects.png'}")


if __name__ == "__main__":
    run()