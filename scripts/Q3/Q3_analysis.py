import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd  #https://pandas.pydata.org/docs/user_guide/index.html#user-guide
    import numpy as np  #https://numpy.org/doc/stable/user/index.html
    import matplotlib.pyplot as plt  #https://matplotlib.org/stable/users/index.html
    import statsmodels.formula.api as smf  #https://www.statsmodels.org/stable/example_formulas.html
    from matplotlib.patches import Patch  #used for the COVID period in the legend
    from pathlib import Path  #https://docs.python.org/3/library/pathlib.html
    import pyarrow #used to read the parquet file

    return Patch, Path, mo, np, pd, plt, smf


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Q3 - Analysis: exchange rate and spending in border regions

    ## 1. Introduction

    - Q3: _Is **spending** in border regions more strongly affected by a decrease in EUR/CHF exchange rate than **spending** in non-border regions, and does this effect differ between border regions?_

    **Hypothesis:** when the EUR/CHF rate decreases (the franc gets stronger), shopping in the neighbouring EUR countries gets cheaper.
        People living close to the border can easily shop there, so spending in Switzerland should drop more in border regions than in non-border regions.

    ## 2. Script description
    1. **Load** the merged Q3 dataset from `data/processed/`
    2. **Visualize** the exchange rate and the spending of border and non-border regions over time
    3. **Main regression:** spending on the exchange rate with an exchange rate x border-region interaction
    4. **Differences between border regions:** the same model with the neighbouring country
    5. **Robustness check:** the main model without the COVID period
    6. **Results:** coefficient table and coefficient plot

    All figures are saved in `output/figures/` and all tables in `output/tables/`.

    **Notes:**
    - The target is `log_spending`, so the coefficients can be read as (approximate) percentage changes.
    - The spending values are scaled, so only relative changes are interpreted.
    """)
    return


@app.cell
def _(plt):
    #Defining a list of global parameters for all the figures generated in this notebook

    #Disclamer: the list was provided from a LLMs but output was verified on matplotlib.com (https://matplotlib.org/stable/users/explain/customizing.html), parameters were personalised and corrected based on specific needs e.g. addition of pdf.fonttype 


    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.titleweight": "bold",
        "axes.labelsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.grid": True,
        "grid.color": "lightgrey",
        "grid.alpha": 0.6,
        "grid.linewidth": 0.6,
        "lines.linewidth": 1.3,
        "lines.markersize": 3.5,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,})

    colors = {"Border regions": "tab:blue",
              "Non-border": "tab:gray",
              "France": "tab:blue",
              "Germany": "tab:green",
              "Italy": "tab:purple",
              "EUR/CHF": "tab:orange",
              "Non-border higher": "tab:red",}
    return (colors,)


@app.cell
def _(Path, mo):
    input_file = Path("../../data/processed/q3_data.parquet")
 
    #output folders inside the analysis_Q3 folder
    #output folders inside the analysis_Q3 folder, built from the location of this notebook,
    #so they are always found, no matter from which folder marimo was started
    figures_folder = mo.notebook_dir() / "output" / "figures"
    tables_folder = mo.notebook_dir() / "output" / "tables"

    figures_folder.mkdir(parents=True, exist_ok=True)
    tables_folder.mkdir(parents=True, exist_ok=True)

    def save_figure(fig, name):
            fig.savefig(figures_folder / f"{name}.pdf")


    return input_file, save_figure, tables_folder


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load the data and prepare the exchange rate

    The exchange rate is **centered**: we subtract its mean, so the `border_region` coefficient is the difference between border and non-border regions at the **average** exchange rate (and not at a rate of 0, which never happens).

    The rate is also multiplied by 100, so one unit means a change of **0.01 CHF per EUR**. With `log_spending` as target, the coefficient x 100 is then the % change of spending when the rate goes up by 0.01 CHF.
    A **decrease** of the rate (stronger franc) has the opposite sign.
    """)
    return


@app.cell
def _(input_file, pd):
    #using pandas to read the main parquet file 
    q3_data = pd.read_parquet(input_file)

    #centering the data (exchange - mean(exchange)/100) --> %
    q3_data["eur_chf_c"] = (q3_data["eur_chf"] - q3_data["eur_chf"].mean()) * 100
 
    #update: group used in step 5: the neighbouring country, or "Non-border" for the non-border regions
    q3_data["border_group"] = q3_data["border_country"].fillna("Non-border")
 
    print(q3_data.info())
    return (q3_data,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Visualisation of border dynamics in relation to exchange over time

    Before the regression we look at the data:
    - **Figure 1:** the monthly EUR/CHF rate from 2019 to 2025
    - **Figure 2:** monthly spending of border and non-border regions as an index (average of 2019 = 100), so that both groups can be compared even if their level is different. The exchange rate is shown in a second panel below with the same time axis.

    In both figures the COVID period is shaded in grey.
    """)
    return


@app.cell
def _(colors, pd, plt, q3_data, save_figure):
    #one exchange rate per month, with a real date (first day of the month) for the x axis
    monthly_rate = q3_data.groupby(["year", "month"])["eur_chf"].first().reset_index()
    monthly_rate["month_date"] = pd.to_datetime(monthly_rate[["year", "month"]].assign(day=1))
 
    fig1, ax1 = plt.subplots(figsize=(9, 3.5))
    ax1.axvspan(pd.Timestamp("2020-03-16"), pd.Timestamp("2022-12-31"), color="grey", alpha=0.12, label="COVID period")
    ax1.plot(monthly_rate["month_date"], monthly_rate["eur_chf"], color=colors["EUR/CHF"], marker="o", label="EUR/CHF (monthly average)")
    ax1.axhline(1, color="grey", linewidth=0.8, linestyle=":")  #parity: 1 EUR = 1 CHF
 
    ax1.set_title("EUR/CHF exchange rate (2019-2025)")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("CHF per 1 EUR")
    fig1.legend(loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.14))
 
    save_figure(fig1, "fig1_eur_chf")
    fig1
    return (monthly_rate,)


@app.cell
def _(Patch, colors, monthly_rate, np, pd, plt, q3_data, save_figure):
    def spending_gap(data):

        #gap: change of border-region spending since 2019 compared with non-border regions, in %

        monthly_spending = data.groupby(["year", "month", "border_region"])["spending"].sum().unstack()

        spending_index = monthly_spending / monthly_spending.loc[2019].mean() * 100

        gap = (spending_index[True] / spending_index[False] - 1) * 100

        return gap.rolling(12, center=True, min_periods=6).mean().values  #12-month moving average removes the seasonal pattern


    #groceries are the category where cross-border shopping happens, all categories are shown for comparison

    gap_groceries = spending_gap(q3_data[q3_data["category"] == "Retail: Food, beverage, tobacco"])

    gap_all = spending_gap(q3_data)


    months = monthly_rate["month_date"]

    covid_start, covid_end = pd.Timestamp("2020-03-16"), pd.Timestamp("2022-12-31")


    fig2, (ax2_top, ax2_bottom) = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True, gridspec_kw={"height_ratios": [2.6, 1]})

    for ax in [ax2_top, ax2_bottom]:

        ax.axvspan(covid_start, covid_end, color="grey", alpha=0.10, linewidth=0)


    #top panel: gap around 0, blue when border regions spend relatively more than in 2019, red when relatively less

    ax2_top.fill_between(months, gap_groceries, 0, where=gap_groceries >= 0, interpolate=True, color=colors["Border regions"], alpha=0.30, linewidth=0)

    ax2_top.fill_between(months, gap_groceries, 0, where=gap_groceries < 0, interpolate=True, color=colors["Non-border higher"], alpha=0.30, linewidth=0)

    ax2_top.plot(months, gap_groceries, color=colors["Border regions"], linewidth=1.8, label="Grocery retail (food, beverage, tobacco)")

    ax2_top.plot(months, gap_all, color="dimgrey", linewidth=1, linestyle="--", label="All categories")

    ax2_top.axhline(0, color="black", linewidth=0.8)

    ax2_top.set_ylim(min(np.nanmin(gap_groceries), np.nanmin(gap_all)) - 1.5, max(np.nanmax(gap_groceries), np.nanmax(gap_all)) + 0.5)  #space for the labels


    ax2_top.set_ylabel("Border vs non-border spending,\nchange since 2019 (%)")

    #bottom panel: exchange rate on the same time axis

    ax2_bottom.plot(months, monthly_rate["eur_chf"], color=colors["EUR/CHF"], marker="o", markersize=2, label="EUR/CHF")

    ax2_bottom.set_title("EUR/CHF exchange rate")

    ax2_bottom.set_ylabel("CHF per 1 EUR")

    ax2_bottom.set_xlabel("Month")


    #one legend for both panels, centered below the figure

    handles = ax2_top.get_legend_handles_labels()[0] + ax2_bottom.get_legend_handles_labels()[0]

    handles.append(Patch(color="grey", alpha=0.2, label="COVID period"))

    fig2.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06))
    plt.tight_layout()


    save_figure(fig2, "fig2_spending_gap_border_vs_nonborder")

    fig2
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Main regression

    $$\log(\text{spending}) = \beta_1 \cdot \text{EUR/CHF} + \beta_2 \cdot \text{EUR/CHF} \times \text{border} + \text{region} \times \text{category} + \text{controls}$$

    - $\beta_1$: effect of the exchange rate in **non-border** regions
    - $\beta_2$: how much **stronger** (or weaker) the effect is in **border** regions. This is the answer to the first part of Q3.
    - **Region x category:** every combination of region and category gets its own level, because the spending values are scaled separately and their levels are very different (e.g. food retail in Zurich vs accommodation in Ticino). This also includes the difference in level between border and non-border regions, so `border_region` alone is not in the model, only its interaction with the exchange rate.
    - **Controls:** weekday, month (season), year (trend), COVID flag and holiday share.

    If the hypothesis is right, $\beta_2$ is **positive**: when the rate goes down, spending goes down more in border regions.

    **Step 4 **shows in the data why region x category is used instead of category only.

    Since the exchange rate is monthly, the year is used as a trend and not as a category: `C(month) + C(year)` together would pick out every single month and absorb the effect of the exchange rate.

    Robust standard errors (`HC1`) are used, because the spread of spending is very different between categories.
    """)
    return


@app.cell
def _(q3_data, smf, tables_folder):
    controls = "C(region):C(category) + C(weekday) + C(month) + year + covid_period + holiday_share"

    model_main = smf.ols(f"log_spending ~ eur_chf_c + eur_chf_c:border_region + {controls}", data=q3_data).fit(cov_type="HC1")
 
    #saving the full output as text file
    with open(tables_folder / "model_main_summary.txt", "w") as _f:
        _f.write(model_main.summary().as_text())
 
    print(f"R squared: {model_main.rsquared:.3f}")
    print(model_main.summary().tables[1])
    return controls, model_main


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Validation of the model

    The controls of the main model were chosen from theory (step 3). Here we check in the data that this choice is sensible, with three checks:

    **Nested models:** the model is built step by step, adding one group of controls at a time (M1 to M4).
    M5 replaces the category with the region x category levels, which is the main model of step 3.
    For each model we compare the R², the AIC (Akaike information criterion, lower = better model) and the interaction coefficient `eur_chf_c:border_region`.
    A control group belongs in the model if it improves R² and AIC. If the interaction stays similar when controls are added, the main result does not depend on the exact choice of the model.

    **Multicollinearity (VIF):** the variance inflation factor shows how strongly a variable can be explained by the other variables.
    Below 5 is fine, above 10 means that the effect of this variable can hardly be separated from the others.
    This is important for Q3, because the EUR/CHF rate decreases almost constantly from 2019 to 2025, while `year` increases.

    **Residuals:** a linear regression assumes that the residuals (observed minus predicted values) are spread around 0 without a clear pattern and roughly normally distributed.
    """)
    return


@app.cell
def _(pd, q3_data, smf, tables_folder):
    def build_nest_table():
        nested_formulas = {
                "M1: exchange rate x border only": "log_spending ~ eur_chf_c * border_region",
                "M2: + category": "log_spending ~ eur_chf_c * border_region + C(category)",
                "M3: + calendar (weekday, month, year)": "log_spending ~ eur_chf_c * border_region + C(category) + C(weekday) + C(month) + year",
                "M4: + COVID and holidays": "log_spending ~ eur_chf_c * border_region + C(category) + C(weekday) + C(month) + year + covid_period + holiday_share",
                "M5: region x category": "log_spending ~ eur_chf_c + eur_chf_c:border_region + C(region):C(category) + C(weekday) + C(month) + year + covid_period + holiday_share",
            }
 
        nested_results = []
        for model_name, formula in nested_formulas.items():
            model = smf.ols(formula, data=q3_data).fit(cov_type="HC1")
            nested_results.append({
                "model": model_name,
                "r_squared": model.rsquared,
                "aic": model.aic,
                "interaction_coef": model.params["eur_chf_c:border_region[T.True]"],
                "interaction_p_value": model.pvalues["eur_chf_c:border_region[T.True]"],})
 
        nested_table = pd.DataFrame(nested_results).round(4)

        nested_table.to_csv(tables_folder / "table_validation_nested_models.csv", index=False)
        return nested_table


    build_nest_table()


    #Every control group belongs in the model: R² rises and AIC falls at every step. Region × category (M5) gives by far the biggest improvement, which confirms that each region–category combination needs its own level.
    return


@app.cell
def _(model_main, pd, tables_folder):
    from statsmodels.stats.outliers_influence import variance_inflation_factor  #https://www.statsmodels.org/stable/generated/statsmodels.stats.outliers_influence.variance_inflation_factor.html
 
    print("4.2 MULTICOLLINEARITY (VIF) --> table above")
 
    #design matrix of the main model: one column per variable (the categories are already split into dummy columns)
    design_matrix = model_main.model.exog
    column_names = model_main.model.exog_names
 
    #VIF only for the main variables, the dummies of category, weekday and month are not of interest here
    vif_variables = ["eur_chf_c", "eur_chf_c:border_region[T.True]", "year", "covid_period[T.True]", "holiday_share"]
 
    vif_table = pd.DataFrame({"variable": vif_variables,"vif": [variance_inflation_factor(design_matrix, column_names.index(name)) for name in vif_variables],}).round(2)
 
    vif_table.to_csv(tables_folder / "table_validation_vif.csv", index=False)
    vif_table
    return


@app.cell
def _(colors, model_main, plt, save_figure):
    print("4.3 RESIDUALS:")
 
    residuals = model_main.resid
    fitted_values = model_main.fittedvalues
 
    fig_res, (ax_res_left, ax_res_right) = plt.subplots(1, 2, figsize=(9, 3.5))
 
    #left: residuals against fitted values, the points are rasterized so the pdf stays small (125,000 points)
    ax_res_left.scatter(fitted_values, residuals, s=2, alpha=0.15, color=colors["Border regions"], rasterized=True)
    ax_res_left.axhline(0, color="red", linewidth=1, linestyle="-")
    ax_res_left.set_title("Residuals vs fitted values")
    ax_res_left.set_xlabel("Fitted log spending")
    ax_res_left.set_ylabel("Residual")
 
    #right: distribution of the residuals
    ax_res_right.hist(residuals, bins=80, color=colors["Border regions"])
    ax_res_right.axvline(0, color="red", linewidth=1, linestyle="-")
    ax_res_right.set_title("Distribution of the residuals")
    ax_res_right.set_xlabel("Residual")
    ax_res_right.set_ylabel("Number of rows")
    plt.tight_layout()
 
    print(f"mean of residuals: {residuals.mean():.4f}, skewness: {residuals.skew():.2f}")
 
    save_figure(fig_res, "validation_residuals")
    fig_res
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ##Differences between border regions

    To answer the second part of Q3, the border flag is replaced with the neighbouring country (`border_group`): France (Lake Geneva), Germany (Northwestern, Eastern), Italy (Ticino) and Non-border as reference.
    Each interaction `eur_chf_c:border_group[...]` tells how much stronger the effect is in that group compared with the non-border regions.
    """)
    return


@app.cell
def _(controls, q3_data, smf, tables_folder):
    model_country = smf.ols(f"log_spending ~ eur_chf_c + eur_chf_c:C(border_group, Treatment('Non-border')) + {controls}", data=q3_data).fit(cov_type="HC1")
 
    with open(tables_folder / "model_country_summary.txt", "w") as _f:
        _f.write(model_country.summary().as_text())
 
    print(f"R squared: {model_country.rsquared:.3f}")
    print(model_country.params.filter(like="eur_chf_c"))
    return (model_country,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Robustness check without the COVID period

    During COVID shops were closed and for some time the borders too, so cross-border shopping was not possible.
    The `covid_period` flag only corrects part of it, therefore we run the main model again **without** the rows of the COVID period.

    If $\beta_2$ is similar, the result does not depend on COVID.
    """)
    return


@app.cell
def _(q3_data, smf, tables_folder):
    q3_no_covid = q3_data[~q3_data["covid_period"]]
 
    #covid_period is removed from the controls, since it is always False here
    controls_no_covid = "C(region):C(category) + C(weekday) + C(month) + year + holiday_share"
 
    model_no_covid = smf.ols(f"log_spending ~ eur_chf_c + eur_chf_c:border_region + {controls_no_covid}", data=q3_no_covid).fit(cov_type="HC1")
 
    with open(tables_folder / "model_no_covid_summary.txt", "w") as _f:
        _f.write(model_no_covid.summary().as_text())
 
    print(f"rows used: {len(q3_no_covid)} of {len(q3_data)}")
    print(f"R squared: {model_no_covid.rsquared:.3f}")
    print(model_no_covid.params.filter(like="eur_chf_c"))
    return (model_no_covid,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Results

    **Table 1** collects the exchange-rate coefficients of all three models, converted into % change of spending for an increase of the rate by 0.01 CHF, with 95% confidence intervals and p-values.

    **Figure 3** shows the effect of the exchange rate for each group (non-border regions and each neighbouring country) from the model of step 5.

    The effect of a group is the base effect plus its interaction, and its confidence interval is calculated with `t_test`, which also takes the correlation between the two coefficients into account.
    """)
    return


@app.cell
def _(model_country, model_main, model_no_covid, np, pd, tables_folder):
    def coefficient_table(model, model_name):
        #keep only the exchange rate coefficients
        names = [name for name in model.params.index if "eur_chf_c" in name]
        ci = model.conf_int().loc[names]
 
        table = pd.DataFrame({"model": model_name,
                              "coefficient": names,
                              "effect_%": (np.exp(model.params[names]) - 1) * 100,
                              "ci_low_%": (np.exp(ci[0]) - 1) * 100,
                              "ci_high_%": (np.exp(ci[1]) - 1) * 100,
                              "p_value": model.pvalues[names],})
        return table
 
    results_table = pd.concat([coefficient_table(model_main, "Main"),
                               coefficient_table(model_country, "By country"),
                               coefficient_table(model_no_covid, "Without COVID"),
                              ]).round(4).reset_index(drop=True)
 
    results_table.to_csv(tables_folder / "table1_exchange_rate_effects.csv", index=False)

    results_table
    return


@app.cell
def _(colors, model_country, np, pd, plt, q3_data, save_figure, tables_folder):
    group_name = "C(border_group, Treatment('Non-border'))"
    group_labels = {
        "France": "Lake Geneva (France)",
        "Germany": "Northwestern + Eastern (Germany)",
        "Italy": "Ticino (Italy)",
    }

    #actual change of the exchange rate: average of 2025 minus average of 2019, in Rappen (same unit as eur_chf_c)
    yearly_rate = q3_data.groupby("year")["eur_chf"].mean()
    rate_change = (yearly_rate[2025] - yearly_rate[2019]) * 100
    print(f"change of EUR/CHF from 2019 to 2025: {rate_change:.1f} Rappen")

    effects = []
    for group in group_labels:
        #interaction = how much more (or less) this border region reacts than the non-border regions
        name = f"eur_chf_c:{group_name}[T.{group}]"
        coefficient = model_country.params[name]
        ci_low, ci_high = model_country.conf_int().loc[name]

        #converted into the % change of spending caused by the actual change of the rate
        effect_values = [(np.exp(value * rate_change) - 1) * 100 for value in [coefficient, ci_low, ci_high]]
        effects.append({"group": group,
                        "extra_change_%": effect_values[0],
                        "ci_low_%": min(effect_values[1:]),   #min and max, since the rate change is negative and switches the order
                        "ci_high_%": max(effect_values[1:]),
                        "p_value": model_country.pvalues[name],})

    #sorted from the biggest loss to the smallest
    effects_table = pd.DataFrame(effects).sort_values("extra_change_%").reset_index(drop=True)

    fig3, ax3 = plt.subplots(figsize=(7, 2.8))
    ax3.axvline(0, color="dimgrey", linestyle="--", linewidth=1.2, label="Non-border regions (reference)")

    for i, row in effects_table.iterrows():
        error = [[row["extra_change_%"] - row["ci_low_%"]], [row["ci_high_%"] - row["extra_change_%"]]]
        ax3.errorbar(row["extra_change_%"], i, xerr=error, fmt="o", markersize=8, capsize=4, linewidth=1.6, color=colors[row["group"]])
        ax3.text(row["ci_high_%"] + 0.6, i, f"{row['extra_change_%']:+.1f}%", va="center", fontsize=9, fontweight="bold",
                 color=colors[row["group"]], bbox=dict(facecolor="white", edgecolor="none", pad=1))

    ax3.set_yticks(range(len(effects_table)))
    ax3.set_yticklabels([group_labels[group] for group in effects_table["group"]])
    ax3.set_ylim(len(effects_table) - 0.5, -0.5)  #biggest loss on top
    ax3.grid(axis="y", visible=False)

    #symmetric x axis, so that 0 is in the middle
    limit = max(effects_table["ci_low_%"].abs().max(), effects_table["ci_high_%"].abs().max()) + 2
    ax3.set_xlim(-limit, limit)

    ax3.set_xlabel(f"Change in spending (border vs non-border) due to CHF/EUR exch. change (e.g.{rate_change:+.0f} Rappen) [%]")
    fig3.legend(loc="lower center", bbox_to_anchor=(0.5, -0.15))


    save_figure(fig3, "fig3_extra_effect_by_border_region")
    effects_table.round(4).to_csv(tables_folder / "table2_extra_effect_by_border_region.csv", index=False)
    fig3
    return


if __name__ == "__main__":
    app.run()
