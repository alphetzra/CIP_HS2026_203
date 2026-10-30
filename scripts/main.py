from dotenv import load_dotenv
from scripts.acquisition import scrape_holidays, download_spending
from scripts.cleaning import clean_holidays, clean_population, clean_spending
from scripts.integration import holiday_share, build_df


def main() -> None:
    load_dotenv()
    scrape_holidays()
    download_spending()
    clean_holidays()
    clean_population()
    clean_spending()
    holiday_share()
    build_df()

if __name__ == "__main__":
    main()