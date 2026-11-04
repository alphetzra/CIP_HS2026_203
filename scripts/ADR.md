Public holiday data is needed for Research Question 2:

How much of the daily variation in spending by category is explained by calendar effects
(weekday, month, public holidays)? Specifically, how does a regional public holiday change
spending by category in regions where it applies, compared with regions where the same date
is a normal working day?

feiertagskalender.ch was scrapped with Playright on 25/11/2026. Why scraping: feiertagskalender.ch lists the holidays of all 26 cantons
as HTML tables. Its API is a paid product, while the free website content
may be used for personal, non-commercial purposes, and the robots.txt does
not disallow the pages used.

Why Playwright with a real browser (instead of requests/BeautifulSoup):
the site shows a security check to automated clients. A plain HTTP request
only gets the check page, not the table. The script therefore attaches to a
normal browser started by the user (Chrome DevTools Protocol). When the check
appears, the user confirms it manually in the browser and the script continues.

Polite scraping:
- every page is cached as an HTML file and never downloaded twice.
- a pause of 2 seconds between requests.


# TODO: Change this and describe just what this file is doing and why it is here and it specifics