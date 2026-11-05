import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

from scripts.Q2.analysis.calendar_regression import run_calendar_regression
from scripts.Q2.analysis.regional_holiday_effect import run_regional_holiday_effect
from scripts import config
from scripts.Q2.exploration.calendar_index import run_calendar_index
from scripts.Q2.integration.build_df import get_build_df
from scripts.Q2.population.population import get_population, get_raw_population
from scripts.Q2.population.acquire import acquire_population
from scripts.Q2.holidays.scrape import scrape_holidays
from scripts.Q3.spending.download_spending import app as acquire_spending_app
from scripts.Q3.Q3_analysis import app as q3_analysis_app
from scripts.Q3.exchange.api_SNB import app as acquire_exchange_app
from scripts.Q2.spending.spending import get_raw_spending, get_spending
from scripts.Q2.exchange.exchange import get_raw_exchange
from scripts.Q2.events.events import get_events, get_raw_events

from scripts.Q2.exploration.explore_spending import app as explore_spending_app

from scripts.Q3.Q3_merge import app as q3_merge_app

# raw
def raw_population(args):
    print(get_raw_population().head())

def raw_spending(args):
    print(get_raw_spending().head())

def raw_exchange(args):
    print(get_raw_exchange().head())

def raw_events(args):
    print(get_raw_events().head())

# data
def population(args):
    print(get_population().head())

def spending(args):
    print(get_spending().head())

def exchange(args):
    print(get_raw_exchange().head())  # raw is already cleaned

def events(args):
    print(get_events().head) # TODO: Morteza please test it after the other fixes

# scrape

def scrape_h(args):
    scrape_holidays() # TODO: Laura please test holiday scrape

def scrape_population(args):
    acquire_population()

def scrape_spending(args):
    acquire_spending_app.run()

def scrape_exchange(args):
    acquire_exchange_app.run()

def scrape_events(args):
    nb = Path("scripts/Q1/code/01_event_web_scraping.ipynb")
    subprocess.run(
        [sys.executable, "-m", "IPython", nb.name],
        cwd=nb.parent,
        check=True,
    )

# exploration
def explore_spending(args):
    explore_spending_app.run()

def calendar_index(args):
    run_calendar_index()

# integration
def q2_merge(args):
    print(get_build_df().head())

def q1_merge(args):
    print() #TODO: Morteza add here the call for your integration merge

def q3_merge(args):
    q3_merge_app.run()
    df = pd.read_parquet(config.DF_Q3)
    print(df.head())

# analysis
def calendar_regression(args):
    run_calendar_regression()

def regional_holiday_effect(args):
    run_regional_holiday_effect()

def q3(args):
    q3_analysis_app.run()

def q1(args): # TODO: Morteza please test it after the other fixes
    nb = Path("scripts/Q1/code/03_data_analysis_visualization.ipynb")
    subprocess.run(
        [sys.executable, "-m", "IPython", nb.name],
        cwd=nb.parent,
        check=True,
    )


def build_parser():
    parser = argparse.ArgumentParser(description="My multi-purpose tool")
    commands = parser.add_subparsers(dest="command", required=True)

    raw = commands.add_parser("raw", help="Show raw head")
    raw_targets = raw.add_subparsers(dest="target", required=True)

    data = commands.add_parser("data", help="Show data head")
    data_targets = data.add_subparsers(dest="target", required=True)

    scrape = commands.add_parser("scrape", help="Run a scraper")
    scrape_targets = scrape.add_subparsers(dest="target", required=True)

    exploration = commands.add_parser("exploration", help="Run a Exploration")
    exploration_targets = exploration.add_subparsers(dest="target", required=True)

    integration = commands.add_parser("integration", help="Run a Integration")
    integration_targets = integration.add_subparsers(dest="target", required=True)

    analysis = commands.add_parser("analysis", help="Run a Analysis")
    analysis_targets = analysis.add_subparsers(dest="target", required=True)

    # raw
    p = raw_targets.add_parser("population", help="Raw Population data")
    p.set_defaults(func=raw_population)

    p = raw_targets.add_parser("spending", help="Raw Spending data")
    p.set_defaults(func=raw_spending)

    p = raw_targets.add_parser("exchange", help="Raw Exchange data")
    p.set_defaults(func=raw_exchange)

    p = raw_targets.add_parser("events", help="Events Exchange data")
    p.set_defaults(func=raw_events)

    # data
    p = data_targets.add_parser("population", help="Population data")
    p.set_defaults(func=population)

    p = data_targets.add_parser("spending", help="Spending data")
    p.set_defaults(func=spending)

    p = data_targets.add_parser("exchange", help="Exchange data")
    p.set_defaults(func=exchange)

    p = data_targets.add_parser("events", help="Events data")
    p.set_defaults(func=events)

    # scrape
    p = scrape_targets.add_parser("holidays", help="Scrape public holidays")
    p.set_defaults(func=scrape_h)

    p = scrape_targets.add_parser("population", help="Scrape population data")
    p.set_defaults(func=scrape_population)

    p = scrape_targets.add_parser("spending", help="Scrape spending data")
    p.set_defaults(func=scrape_spending)

    p = scrape_targets.add_parser("exchange", help="Scrape exchange data")
    p.set_defaults(func=scrape_exchange)

    p = scrape_targets.add_parser("events", help="Scrape event data")
    p.set_defaults(func=scrape_events)

    # exploration
    p = exploration_targets.add_parser("spending", help="Explore Spending")
    p.set_defaults(func=explore_spending)

    p = exploration_targets.add_parser("calendar", help="Explore Calendar Index")
    p.set_defaults(func=calendar_index)

    # integration
    p = integration_targets.add_parser("q2", help="Final Q2 DataFrame which will be analysed")
    p.set_defaults(func=q2_merge)

    p = integration_targets.add_parser("q1", help="Final Q1 DataFrame which will be analysed")
    p.set_defaults(func=q1_merge)

    p = integration_targets.add_parser("q3", help="Final Q3 DataFrame which will be analysed")
    p.set_defaults(func=q3_merge)

    # analysis
    p = analysis_targets.add_parser("calendar", help="Analyse Calendar Regression (output: scripts/Q2/output)")
    p.set_defaults(func=calendar_regression)

    p = analysis_targets.add_parser("region", help="Analyse Region Holiday Effect (output: scripts/Q2/output)")
    p.set_defaults(func=regional_holiday_effect)

    p = analysis_targets.add_parser("spending", help="Analyse Spending and Exchange Rate (output: scripts/Q3/output)")
    p.set_defaults(func=q3)

    p = analysis_targets.add_parser("events", help="Analyse Events (output: scripts/Q1/output)")
    p.set_defaults(func=q1)

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
