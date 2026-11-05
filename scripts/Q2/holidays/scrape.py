"""Holiday data acquisition - web scraping from feiertagskalender.ch.

The script opens one page per canton and year and one national page and
saves the full HTML into data/raw/raw_holidays/. The script automates most
of the scrapping but needs a user to restart browser and go through the security check.

Setup: copy .example.env to .env (not tracked in git) and fill in
  BROWSER_DEBUGGING_PORT and BROWSER_PATH (path to the Chrome executable).
"""
import asyncio
import os
import sys
import time
import subprocess
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Playwright, Browser, Page
from playwright.sync_api import TimeoutError as Timeout
from scripts import config

load_dotenv()



def get_config() -> tuple[str, str] | None:
    """Gets necessary configuration from env and returns it or informs user to fill the env file.
        Returns:
            Tuple[0] debug port Tuple[1] browser executable
        """

    debug_port = os.getenv("BROWSER_DEBUGGING_PORT")
    browser_exe = os.getenv("BROWSER_PATH")
    if debug_port is None or browser_exe is None:
        print("Enter debugging port and browser_exe in env")
        return None
    return debug_port, browser_exe


def launch_browser(browser_exe: str, debug_port: str, message: str = "Press enter when you closed "
                                                                     "all browser, so the script can "
                                                                     "start a browser with debug port."):
    """Start the browser with remote debugging.
        Args:
            browser_exe: Path to the browser executable which will be opened
            debug_port: Debug Port
            message: Message
        """

    input(message)
    subprocess.Popen(
        [browser_exe, f"--remote-debugging-port={debug_port}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def connect_browser(p: Playwright, debug_port: str) -> Browser | None:
    """Attach Playwright to the running browser via CDP.
        Args:
            p: Instance of Playwright
            debug_port: Debug Port
        Returns:
            Browser or None
        """

    try:
        ret = p.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
    except Exception:
        ret = None
    return ret


def get_page(browser: Browser) -> Page:
    """Open a new tab in the existing browser window.
        Args:
            browser: instance of an open browser
        Returns:
            New open tab
        """

    context = browser.contexts[0]
    return context.new_page()


def open_url(page: Page, url: str) -> None:
    """Go to URL and wait for user confirmation.
        Args:
            page: Page where the url is opened
            url: Url which will be opened
        Returns:
            None
    """

    page.goto(url)
    time.sleep(5)


def has_table(page: Page, timeout_ms: int = 3000) -> bool:
    """Wait up to timeout_ms for the holiday table to appear and confirms
    if it appears or not.
        Args:
            page: Website which will be searched for tables
            timeout_ms: Time which when exceeded will return False
        Returns:
            True or False
    """

    try:
        page.wait_for_selector(config.ROW_SELECTOR, timeout=timeout_ms)
        return True
    except Timeout:
        return False


def scrape(page: Page) -> bool:
    """Download holiday pages and cache them as HTML files.
        Args:
            page: Website page that will be scraped
        Returns:
            True or False.

        Returns False if a page could not be loaded.
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

def ensure_browser(p, browser_exe, debug_port, message, timeout_s=20) -> Browser:
    """Connect to a browser over CDP, launching it first if necessary.
            Args:
                p: Instance of Playwright
                browser_exe: Path to the browser executable to launch
                debug_port: Debug Port
                message: Message
                timeout_s: Seconds to wait for the launched browser to accept a connection
            Returns:
                Browser
            Raises:
                RuntimeError: If no connection could be made within timeout_s
        """
    browser = connect_browser(p, debug_port)
    if browser is not None:
        return browser
    launch_browser(browser_exe, debug_port, message)
    for _ in range(timeout_s):
        time.sleep(1)
        browser = connect_browser(p, debug_port)
        if browser is not None:
            return browser
    raise RuntimeError("Could not connect to the browser.")


def scrape_holidays() -> None:
    """Scrape the holiday pages over CDP, retrying if it fails.

    Returns early if no debug port and browser executable is found or when scrape succeeds.
    """

    max_retries = 10
    cfg = get_config()
    if cfg is None:
        return
    debug_port, browser_exe = cfg
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    with sync_playwright() as p:
        message = "Close all browsers and press Enter."
        for attempt in range(max_retries):
            browser = ensure_browser(p, browser_exe, debug_port, message)
            try:
                if scrape(get_page(browser)):
                    return
            finally:
                browser.close()
            message = "Error occurred. Close the browser and press Enter to restart."
        print("Gave up after", max_retries, "attempts.")
