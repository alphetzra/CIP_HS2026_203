"""Analysis Q2 - how much of the daily variation in spending do calendar effects explain?

1. Introduction

Answers the first part of Q2 with linear regressions (OLS), one per merchant
category: log_spending ~ region + weekday + month + year + COVID + holiday_share
and estimates the holiday effect (all holidays, national and regional).

2. Data

------------------------------------------------------------------------------
| Input                        | Output                                       |
|------------------------------|----------------------------------------------|
| data/processed/df_q2.parquet | results/tables/r2_by_category.csv            |
|                              | results/tables/holiday_effect_all.csv        |
|                              | results/tables/holiday_effect_by_region.csv  |
|                              | results/figures/r2_by_category.png           |
|                              | results/figures/holiday_heatmap.png          |
------------------------------------------------------------------------------

3. Script description

1. Read df_q2 and add a COVID flag (config.COVID_PERIOD).
2. Explained variation: per category, add the variable groups one by one
   (region, weekday, month, year, COVID, holiday) and store the R² after
   each step. The increase in R² is the part explained by that group.
   Region is added first and only removes the level differences between
   regions; the shares are expressed as % of the remaining (within-region)
   variation.
3. Holiday effect per category: full model with all groups; the
   coefficient of holiday_share is converted to a % change.
4. Holiday effect per region x category: same model without region,
   estimated separately for each region and category -> heatmap.

4. Notes

- holiday_share goes from 0 (normal day) to 1 (whole region off), so its
  coefficient is the effect of a full holiday. Log points are converted to
  % change with (exp(b) - 1) * 100.
- Weekday, month and year are categorical (one dummy per value), so no
  shape (e.g. linear trend) is assumed.
- COVID is flagged and controlled for instead of deleted.
- Robust standard errors (HC1) are used for the holiday effects, because
  the variance of spending is not the same on all days.
- The R² shares depend on the order in which the groups are added: a group
  added earlier also gets the variation it shares with later groups
  (e.g. year and COVID).
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scripts import config

# variable groups in the order they are added to the model;
# C(...) = treat as categorical (one dummy per value)
STEPS = {
    "region": "C(region)",
    "weekday": "C(weekday)",
    "month": "C(month)",
    "year": "C(year)",
    "COVID": "is_covid",
    "holiday": "holiday_share",
}

# ======================= data =======================

def add_covid_flag(df: pd.DataFrame) -> pd.DataFrame:
    """is_covid = True on days inside the COVID period."""
    df["is_covid"] = False
    for start, end in config.COVID_PERIOD:
        df.loc[df["date"].between(start, end), "is_covid"] = True
    return df


def load_df() -> pd.DataFrame:
    """Read df_q2 and add the COVID flag."""
    df = pd.read_parquet(config.DF_Q2)
    return add_covid_flag(df)

# ======================= 1. explained variation =======================

def r2_groups(cat_df: pd.DataFrame) -> dict:
    """R² after each variable group, for one category."""
    r2 = {}
    parts = []
    for group, part in STEPS.items():
        parts.append(part)
        formula = f"{config.TARGET} ~ " + " + ".join(parts)
        r2[group] = smf.ols(formula, data=cat_df).fit().rsquared
    return r2     # cumulative R²


def within_region_shares(r2: dict) -> dict:
    """Turn cumulative R² into the share of within-region variation each group explains."""
    r2_region = r2["region"]
    # variation that is left after removing the region level differences
    within_total = 1 - r2_region
    shares = {}
    previous = r2_region
    for step in list(STEPS)[1:]:     # all groups except region
        # increase in R² by this group, as share of the within-region variation
        shares[step] = (r2[step] - previous) / within_total
        previous = r2[step]
    # rest = not explained by any calendar group
    shares["not explained"] = 1 - (previous - r2_region) / within_total
    return shares


def explained_variation(df: pd.DataFrame) -> pd.DataFrame:
    """Table: one row per category, one column per variable group."""
    rows = {}
    for category, cat_df in df.groupby("category", observed=True):
        rows[category] = within_region_shares(r2_groups(cat_df))
    # .T: categories as rows, groups as columns
    return pd.DataFrame(rows).T.round(3)


def plot_r2(shares: pd.DataFrame) -> None:
    """Stacked horizontal bars: which calendar group explains how much, per category."""
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
    """Coefficient of holiday_share as % change, with 95% confidence interval."""
    b = model.params["holiday_share"]
    low, high = model.conf_int().loc["holiday_share"]
    to_pct = lambda x: (np.exp(x) - 1) * 100     # log points -> % change
    return {"effect_pct": to_pct(b), "ci_low": to_pct(low), "ci_high": to_pct(high),
            "p_value": model.pvalues["holiday_share"], "n_obs": int(model.nobs)}


def full_formula(with_region: bool = True) -> str:
    """Formula with all variable groups (optionally without region)."""
    # without region: used when the model is fitted for one region only
    parts = list(STEPS.values()) if with_region else list(STEPS.values())[1:]
    return f"{config.TARGET} ~ " + " + ".join(parts)


def holiday_effect_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Full model per category -> holiday effect per category (all holidays, all regions)."""
    rows = {}
    for category, cat_df in df.groupby("category", observed=True):
        # HC1 = standard errors that allow the noise to differ between days
        model = smf.ols(full_formula(), data=cat_df).fit(cov_type="HC1")
        rows[category] = holiday_effect(model)
    return pd.DataFrame(rows).T.round(3).sort_values("effect_pct")

# ======================= 3. holiday effect per region x category =======================

def holiday_effect_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Full model (without region) per region x category -> table for the heatmap."""
    rows = []
    for (region, category), sub in df.groupby(["region", "category"], observed=True):
        model = smf.ols(full_formula(with_region=False), data=sub).fit(cov_type="HC1")
        rows.append({"region": region, "category": category, **holiday_effect(model)})
    return pd.DataFrame(rows).round(3)


def plot_heatmap(effects: pd.DataFrame) -> None:
    """Heatmap of the holiday effect (% change) by region and category."""
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


def run() -> None:
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


if __name__ == "__main__":
    run()
