"""Holiday data acquisition - web scraping.

1. Introduction

Public holiday data is needed for Research Question 2:

How much of the daily variation in spending by category is explained by calendar effects
(weekday, month, public holidays)? Specifically, how does a regional public holiday change
spending by category in regions where it applies, compared with regions where the same date
is a normal working day?

To compare regions with and without a holiday on the same date, we need the
holidays of every canton.

2. Data source
---------------------------------------------------------------------------------------------------
| Source                | Content                                         | Method of acquisition  |
|-----------------------|-------------------------------------------------|------------------------|
| feiertagskalender.ch  | National and cantonal public holidays per year  | Web scraping           |
|                       | (one page per canton and year, see config.YEARS)| (Playwright)           |
---------------------------------------------------------------------------------------------------

Why scraping: feiertagskalender.ch lists the holidays of all 26 cantons
as HTML tables. Its API is a paid product, while the free website content
may be used for personal, non-commercial purposes, and the robots.txt does
not disallow the pages used.

3. Script description

The script opens one page per canton and year (plus one national page) and
saves the full HTML unchanged into data/raw/raw_holidays/.

Why Playwright with a real browser (instead of requests/BeautifulSoup):
the site shows a security check to automated clients. A plain HTTP request
only gets the check page, not the table. The script therefore attaches to a
normal browser started by the user (Chrome DevTools Protocol). When the check
appears, the user confirms it manually in the browser and the script continues.

Polite scraping:
- every page is cached as an HTML file and never downloaded twice
  (the script can be stopped and resumed; re-runs only fetch missing pages),
- a pause of 2 seconds between requests.

4. Notes

- Setup: copy .example.env to .env (not tracked in git) and fill in
  BROWSER_DEBUGGING_PORT and BROWSER_PATH (path to the Chrome executable).
- The script needs a person at the keyboard (browser restart, security
  check), so it is not fully automated.
- The HTML pages are stored unchanged.
- Data accessed: 25/11/2026.
"""

import os
import time
import subprocess
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Playwright, Browser, Page
from playwright.sync_api import TimeoutError as Timeout
from scripts import config


def get_config() -> tuple[str, str] | None:
    """Read the debugging port and browser path from the environment."""
    debug_port = os.getenv("BROWSER_DEBUGGING_PORT")
    browser_dir = os.getenv("BROWSER_PATH")
    if debug_port is None or browser_dir is None:
        print("Enter debugging port and browser_dir in env")
        return None
    return debug_port, browser_dir


def launch_browser(browser_dir: str, debug_port: str,
                   message: str = "Press enter when you closed all browser, "
                                  "so the script can start a browser with debug port."):
    """Start the browser with remote debugging."""
    # the browser must be fully closed first: if an instance is already
    # running, the new one ignores the --remote-debugging-port flag
    input(message)
    subprocess.Popen(
        [browser_dir, f"--remote-debugging-port={debug_port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # input("Press enter when the browser opens...")


def connect_browser(p: Playwright, debug_port: str) -> Browser | None:
    """Attach Playwright to the running browser via CDP"""
    try:
        ret = p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
    except Exception:
        ret = None
    return ret


def get_page(browser: Browser) -> Page:
    """Open a new tab in the existing browser window."""
    context = browser.contexts[0]
    return context.new_page()


def open_url(page: Page, url: str) -> None:
    """Go to URL and wait for user confirmation."""
    page.goto(url)
    time.sleep(5)


def has_table(page: Page, timeout_ms: int = 3000) -> bool:
    """Wait up to timeout_ms for the holiday table to appear."""
    try:
        page.wait_for_selector(config.ROW_SELECTOR, timeout=timeout_ms)
        return True
    except Timeout:
        return False


def scrape(page: Page) -> bool:
    """Download holiday pages and cache them as HTML files.

    Returns False if a page could not be loaded (e.g. browser closed or
    connection lost), so run() can restart the browser and try again.
    """
    # one national page ("CH") + one page per canton
    pages = [(config.NATIONAL_GEO, "CH")] + [
        (geo, canton) for canton, geo in config.CANTONS.items()
    ]
    # only pages that are not cached yet
    todo = [
        (geo, label, year)
        for year in config.YEARS
        for geo, label in pages
        if not os.path.exists(config.cache_path(geo, year))
    ]
    print(f"{len(todo)} pages to download")

    for geo, label, year in todo:
        # geo = canton id on the website, jahr = year,
        # klasse = holiday class, hl = language
        url = (f"https://www.feiertagskalender.ch/index.php"
               f"?geo={geo}&jahr={year}&klasse={config.CLASS}&hl={config.LANG}")
        print(f"Loading {label} {year}")
        try:
            page.goto(url)
        except Exception:
            return False

        if not has_table(page):
            input(f"[{label} {year}] No table found. If a security check is shown, "
                  "confirm it in the browser, then press Enter here.")
            has_table(page)

        html = page.content()
        if page.locator(config.ROW_SELECTOR).count() > 0:
            with open(config.cache_path(geo, year), "w", encoding="utf-8") as f:
                f.write(html)
        else:
            debug_file = f"debug_{label}_{year}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"No table for {label} {year}, page saved to {debug_file}")

        time.sleep(2)
    return True


def run() -> None:
    """Download all holiday pages into data/raw/raw_holidays."""
    cfg = get_config()
    if cfg is None:
        return
    debug_port, browser_dir = cfg

    with sync_playwright() as p:
        # reuse a browser that already runs with the debug port, else start one
        browser = connect_browser(p, debug_port)
        if browser is None:
            launch_browser(browser_dir, debug_port)
            time.sleep(2)

        def browse():
            # (re)connect every time because the browser may have been restarted
            local_browser = connect_browser(p, debug_port)
            if local_browser is None:
                raise RuntimeError("Could not connect to the browser.")
            return scrape(get_page(local_browser))

        # retry up to 5 times if the browser crashes or the connection is lost;
        # already downloaded pages are cached, so each retry continues where
        # the last stopped
        errors = 0
        try:
            success =  browse()
            while not success and errors < 5:
                launch_browser(browser_dir, debug_port, "Error occurred. Please close the"
                                                        " browser and press enter so the script "
                                                        "can restart.")
                time.sleep(2)
                success = browse()
                errors +=1
            print("Total blocked/errors: ", errors)
        finally:
            browser.close()


if __name__ == "__main__":
    load_dotenv()
    run()
