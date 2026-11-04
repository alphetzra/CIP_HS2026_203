from dotenv import load_dotenv

from holidays.holidays import get_holidays
from holidays.preprocessing_cleaning import get_preprocessed_cleaned_holidays
from population.population import get_raw_population, get_population
from spending.spending import get_raw_spending, get_spending


def main() -> None:
    new = get_spending()
    print(new.head())

    # df_holiday = get_holidays()
    # print(df_holiday)
    #     """Run all steps in order."""
#     load_dotenv()
#
#     # 1. acquisition -> data/raw
#     scrape_holidays()
#     download_spending()
#
#     # 2. cleaning -> data/processed
#     clean_holidays()
#     clean_population()
#     clean_spending()
#
#     # 3. integration -> data/processed
#     holiday_share()
#     build_df()
#
#     # 4. analysis -> results/tables, results/figures
#     plot_calendar_index()
#     fit_calendar_regression()
#     fit_regional_holiday_effect()
#
if __name__ == "__main__":
    main()