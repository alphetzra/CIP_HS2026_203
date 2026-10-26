from dotenv import load_dotenv
from scripts.acquisition import scrape_holidays
from scripts.cleaning import clean_holidays, clean_population


def main() -> None:
    load_dotenv()
    scrape_holidays()
    clean_holidays()
    clean_population()


if __name__ == "__main__":
    main()