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





Columns created to keep the formation from the scraped pages:
- date, holiday:   date and English name of the holiday
- holiday_class:   class shown on the website for full holidays (badge number);
                   empty for partial holidays
- is_partial:      True if the holiday only applies in part of the canton
- canton:          canton abbreviation, or "CH" for the national calendar
- canton_share:    share of the canton's population where the holiday applies
                   (1.0 for full holidays, NaN if the website gives no number)
- is_below:        True if the website gives the share as "< x %"
                   (the stored value is then an upper bound)
- share_note:      original text when no share is given ("varies", "n.a.")
- level:           "national" or "canton"

I put this already in the script (holiday processing_cleaning.py) specifics:
Partial holidays are only valid in part of a canton. canton_share is the
  share of the population that has the day off. "< x %" is stored as x with
  is_below=True. When the page gives no number, the share is NaN and the 
  original text is kept in share_note.

No rows are dropped. Partial holidays without a number keep
  canton_share = NaN and the original text in share_note, so this
  information is not lost.

Why population data:
The population data is needed to weight the cantons  and calculate which share of the Swiss 
population has a holiday on a given day.

When not the whole region is in holiday, what is the threshold to consider it is in holiday?
Because the Grossregion are composed by many cantons, decided to count as holiday when at least 
half of the region has holiday, so 0.6 was chosen as the threshold.

when computing holiday shares in population_holidays.py:
Full holidays get the weight of their class; partial holidays get the population 
share from the website or 0 if none is given. Shares given as "< x %" are used as 
x % (upper bound). Why? Because...

why i chose to add year before covid in the regression?