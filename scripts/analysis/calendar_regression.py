"""How much of the daily variation in spending is explained by calendar effects?

Method (one regression per merchant category, ordinary least squares):
    log_spending ~ region + weekday + month + year + COVID + holiday_share"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scripts import config

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
    """Read df_q2, remove days without a log value (spending 0) if any, add the COVID flag."""
    df = pd.read_parquet(config.DF_Q2)
    n_missing = df[config.TARGET].isna().sum()
    print(f"Days without log value: {n_missing}")
    if n_missing > 0:
        df = df.dropna(subset=[config.TARGET]).copy()
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
    return r2


def within_region_shares(r2: dict) -> dict:
    """Turn cumulative R² into the share of within-region variation each group explains."""
    r2_region = r2["region"]
    within_total = 1 - r2_region
    shares = {}
    previous = r2_region
    for step in list(STEPS)[1:]:
        shares[step] = (r2[step] - previous) / within_total
        previous = r2[step]
    shares["not explained"] = 1 - (previous - r2_region) / within_total
    return shares


def explained_variation(df: pd.DataFrame) -> pd.DataFrame:
    """Table: one row per category, one column per variable group."""
    rows = {}
    for category, cat_df in df.groupby("category", observed=True):
        rows[category] = within_region_shares(r2_groups(cat_df))
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
    to_pct = lambda x: (np.exp(x) - 1) * 100  # log points -> % change
    return {"effect_pct": to_pct(b), "ci_low": to_pct(low), "ci_high": to_pct(high),
            "p_value": model.pvalues["holiday_share"], "n_obs": int(model.nobs)}


def full_formula(with_region: bool = True) -> str:
    """Formula with all variable groups (optionally without region)."""
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

    shares = explained_variation(df)
    shares.to_csv(config.TABLES_DIR / "r2_by_category.csv")
    plot_r2(shares)
    print("Share of within-region variation explained:\n", shares, "\n")

    effects = holiday_effect_by_category(df)
    effects.to_csv(config.TABLES_DIR / "holiday_effect_all.csv")
    print("Holiday effect per category (% change on a full holiday):\n", effects, "\n")

    region_effects = holiday_effect_by_region(df)
    region_effects.to_csv(config.TABLES_DIR / "holiday_effect_region.csv", index=False)
    plot_heatmap(region_effects)
    print(f"Tables saved to {config.TABLES_DIR}, figures to {config.FIGURES_DIR}")


if __name__ == "__main__":
    run()
