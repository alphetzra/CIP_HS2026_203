import os
from playwright.sync_api import sync_playwright

from dotenv import load_dotenv
import subprocess

load_dotenv()

if __name__ == "__main__":
    with sync_playwright() as p:
        debug_port = os.getenv("BROWSER_DEBUGGING_PORT")
        browser_dir = os.getenv("BROWSER_URL")
        if debug_port is None or browser_dir is None:
            print("Enter debugging port and browser_dir in env")
        else:
            input("Press enter when you closed all browsers...")

            proc = subprocess.Popen(
                [browser_dir, f"--remote-debugging-port={debug_port}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            input("Press enter when the browser opens...")

            browser = p.chromium.connect_over_cdp("http://localhost:" + debug_port)

            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            print(context.pages)

            page.goto("https://www.feiertagskalender.ch/index.php")
            input("Press enter when the website loads...")

            print(page.inner_text("h1"))

            browser.close()