from dotenv import load_dotenv
from scripts.acquisition import scrape_holidays, download_spending
from scripts.cleaning import clean_holidays, clean_population, clean_spending
from scripts.integration import holiday_share, build_df
from scripts.analysis import (plot_calendar_index, fit_calendar_regression,
                              fit_regional_holiday_effect)


def main() -> None:
    """Run all steps in order."""
    load_dotenv()

    # 1. acquisition -> data/raw
    scrape_holidays()
    download_spending()

    # 2. cleaning -> data/processed
    clean_holidays()
    clean_population()
    clean_spending()

    # 3. integration -> data/processed
    holiday_share()
    build_df()

    # 4. analysis -> results/tables, results/figures
    plot_calendar_index()
    fit_calendar_regression()
    fit_regional_holiday_effect()

if __name__ == "__main__":
    main()