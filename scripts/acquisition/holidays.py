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
    browser_dir = os.getenv("BROWSER_URL")
    if debug_port is None or browser_dir is None:
        print("Enter debugging port and browser_dir in env")
        return None
    return debug_port, browser_dir


def launch_browser(browser_dir: str, debug_port: str,
                   message: str = "Press enter when you closed all browser, "
                                  "so the script can start a browser with debug port."):
    """Start the browser with remote debugging."""
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
    """Open new tab."""
    context = browser.contexts[0]
    return context.new_page()


def open_url(page: Page, url: str) -> None:
    """Go to URL and wait for user confirmation."""
    page.goto(url)
    time.sleep(5)


ROW_SELECTOR = "table.table tbody tr"


def has_table(page: Page, timeout_ms: int = 3000) -> bool:
    """Wait up to timeout_ms for the holiday table to appear."""
    try:
        page.wait_for_selector(ROW_SELECTOR, timeout=timeout_ms)
        return True
    except Timeout:
        return False


def scrape(page: Page) -> bool:
    """Download holiday pages and cache them as HTML files."""
    pages = [(config.NATIONAL_GEO, "CH")] + [
        (geo, canton) for canton, geo in config.CANTONS.items()
    ]
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
        if page.locator(ROW_SELECTOR).count() > 0:
            with open(config.cache_path(geo, year), "w", encoding="utf-8") as f:
                f.write(html)
        else:
            debug_file = f"debug_{label}_{year}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"No table for {label} {year}, page saved to {debug_file}")

        time.sleep(2)
    return True


def main() -> None:
    load_dotenv()
    cfg = get_config()
    if cfg is None:
        return
    debug_port, browser_dir = cfg

    with sync_playwright() as p:
        browser = connect_browser(p, debug_port)  # is Browser already open?
        if browser is None:
            launch_browser(browser_dir, debug_port)
            time.sleep(2)

        def browse():
            local_browser = connect_browser(p, debug_port)
            if local_browser is None:
                print("Error: no browser")
                exit(1)
            page = get_page(local_browser)
            return scrape(page)


        error_counter = 0
        try:
            success =  browse()
            while not success and error_counter < 5:
                launch_browser(browser_dir, debug_port, "Error occurred. Please close the"
                                                        " browser and press enter so the script "
                                                        "can restart...")
                time.sleep(2)
                success = browse()
                error_counter+=1
            print("Total blocked/errors: ", error_counter)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
