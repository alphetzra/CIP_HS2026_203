"""Analysis Q2 - how much of the daily variation in spending do calendar effects explain?

Specifics:
- Explained variation: the variable groups are added one by one, and the
  increase in R² is the part explained by that group. Region comes first and
  only removes the level differences between regions, so the shares are
  expressed as % of the remaining (within-region) variation.
- The order a group is added matters because if it shares a variation with groups
  added later, it also gets the variation they share.
- holiday_share goes from 0 (normal day) to 1 (whole region off), so its
  coefficient is the effect of a full holiday. Log points are converted to
  % change with (exp(b) - 1) * 100.
- Robust standard errors (HC1) are used for the holiday effects, because
  the variance of spending is not the same on all days.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

from scripts.Q2.integration.build_df import get_build_df
from scripts import config

# variable groups in the order they are added to the model;
# C(...) = treat as categorical (one dummy per value)
STEPS = {
    "region": "C(region)",
    "weekday": "C(weekday)",
    "month": "C(month)",
    "year": "C(year)",
    "COVID": "covid_period",
    "holiday": "holiday_share",
}

# ======================= data =======================

def load_df() -> pd.DataFrame:
    """Load the Q2 table.
        Returns:
            Q2 table"""

    return get_build_df()

# ======================= 1. explained variation =======================

def r2_groups(cat_df: pd.DataFrame) -> dict:
    """Fit the model step by step and store the R² after each variable group.
            Args:
                cat_df: Q2 table for one category
            Returns:
                Dict {group: R²} (cumulative)
            """

    r2 = {}
    parts = []
    for group, part in STEPS.items():
        parts.append(part)
        formula = f"{config.TARGET} ~ " + " + ".join(parts)
        r2[group] = smf.ols(formula, data=cat_df).fit().rsquared
    return r2


def within_region_shares(r2: dict) -> dict:
    """Turn cumulative R² into the share of within-region variation each group explains.
        Args:
            r2: Cumulative R² per group (output of r2_groups())
        Returns:
            Dict {group: share} for all groups except region, plus "not explained"
            """

    r2_region = r2["region"]
    # variation that is left after removing the region level differences
    within_total = 1 - r2_region
    shares = {}
    previous = r2_region
    for step in list(STEPS)[1:]:
        # all groups except region
        # increase in R² by this group, relative to the within-region variation
        shares[step] = (r2[step] - previous) / within_total
        previous = r2[step]
    shares["not explained"] = 1 - (previous - r2_region) / within_total
    return shares


def explained_variation(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the explained variation for every category.
        Args:
            df: Q2 table
        Returns:
            DataFrame with one row per category and one column per variable group"""

    rows = {}
    for category, cat_df in df.groupby("category", observed=True):
        rows[category] = within_region_shares(r2_groups(cat_df))
    # .T: categories as rows, groups as columns
    return pd.DataFrame(rows).T.round(3)


def plot_r2(shares: pd.DataFrame) -> None:
    """Plot the explained variation as stacked horizontal bars and save it.
        Args:
            shares: Output of explained_variation()"""

    shares = shares.sort_values("not explained", ascending=False) * 100
    colors = sns.color_palette("colorblind", n_colors=len(shares.columns) - 1) + ["#DDDDDD"]
    ax = shares.plot.barh(stacked=True, figsize=(10, 5), color=colors, width=0.7)
    ax.set_xlabel("Share of daily variation within a region (%)")
    ax.set_ylabel("")
    ax.set_xlim(0, 100)
    ax.set_title("How much of the daily variation in spending do calendar effects explain?")
    ax.legend(title="Explained by", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(config.FIGURES_DIR / "r2_by_category.png", dpi=200)
    plt.close()

# ======================= 2. holiday effect per category =======================

def holiday_effect(model) -> dict:
    """Read coefficient of holiday_share as % change.
        Args:
            model: Fitted statsmodels OLS or linearmodels PanelOLS result containing holiday_share
        Returns:
            Dict with effect_pct, ci_low, ci_high (95% interval), p_value and n_obs"""

    b = model.params["holiday_share"]
    low, high = model.conf_int().loc["holiday_share"]
    to_pct = lambda x: (np.exp(x) - 1) * 100
    # log points -> % change
    return {"effect_pct": to_pct(b), "ci_low": to_pct(low), "ci_high": to_pct(high),
            "p_value": model.pvalues["holiday_share"], "n_obs": int(model.nobs)}


def full_formula(with_region: bool = True) -> str:
    """Build the formula with all variable groups.
        Args:
            with_region: False for models fitted on one region only
        Returns:
            Formula string for statsmodels"""

    parts = list(STEPS.values()) if with_region else list(STEPS.values())[1:]
    return f"{config.TARGET} ~ " + " + ".join(parts)


def holiday_effect_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Fit the full model per category and get the holiday effect.
        Args:
            df: Q2 table
        Returns:
            DataFrame with one row per category, sorted by effect_pct"""

    rows = {}
    for category, cat_df in df.groupby("category", observed=True):
        # HC1 = standard errors that allow the noise to differ between days
        model = smf.ols(full_formula(), data=cat_df).fit(cov_type="HC1")
        rows[category] = holiday_effect(model)
    return pd.DataFrame(rows).T.round(3).sort_values("effect_pct")

# ======================= 3. holiday effect per region x category =======================

def holiday_effect_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Fit the full model (without region) per region and category.
        Args:
            df: Q2 table
        Returns:
            DataFrame with region, category and the holiday effect columns"""

    rows = []
    for (region, category), sub in df.groupby(["region", "category"], observed=True):
        model = smf.ols(full_formula(with_region=False), data=sub).fit(cov_type="HC1")
        rows.append({"region": region, "category": category, **holiday_effect(model)})
    return pd.DataFrame(rows).round(3)


def plot_heatmap(effects: pd.DataFrame) -> None:
    """Plot the holiday effect (% change) by region and category as heatmap and save it.
        Args:
            effects: Output of holiday_effect_by_region()
        """

    table = effects.pivot(index="category", columns="region", values="effect_pct")
    table = table[list(config.REGIONS)]
    table = table.loc[table.mean(axis=1).sort_values().index]
    limit = np.nanmax(np.abs(table.values))
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(table, annot=True, fmt=".0f", cmap="RdBu", center=0, vmin=-limit, vmax=limit,
                linewidths=0.5, cbar_kws={"label": "% change on a full holiday"}, ax=ax)
    ax.set_title("Change in spending on a public holiday vs. a normal day, by region and category")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "holiday_heatmap.png", dpi=200)
    plt.close(fig)


def run_calendar_regression() -> None:
    """Fit all models, save tables and figures."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    df = load_df()

    # 1. explained variation
    shares = explained_variation(df)
    shares.to_csv(config.TABLES_DIR / "r2_by_category.csv")
    plot_r2(shares)
    print("Share of within-region variation explained:\n", shares, "\n")

    # 2. holiday effect per category
    effects = holiday_effect_by_category(df)
    effects.to_csv(config.TABLES_DIR / "holiday_effect_all.csv")
    print("Holiday effect per category (% change on a full holiday):\n", effects, "\n")

    # 3. holiday effect per region x category
    region_effects = holiday_effect_by_region(df)
    region_effects.to_csv(config.TABLES_DIR / "holiday_effect_by_region.csv", index=False)
    plot_heatmap(region_effects)
    print(f"Tables saved to {config.TABLES_DIR}, figures to {config.FIGURES_DIR}")

