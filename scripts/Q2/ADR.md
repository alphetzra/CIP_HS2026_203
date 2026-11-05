# Architecture Decision Record

### Why the study period 2019–2025?
2019 is a full year before COVID, so it is a normal reference period. 2025 is the last
complete year.

### Why scraping?
feiertagskalender.ch lists the holidays of all 26 cantons as HTML tables. Its API is a
paid product, while the free website content may be used for personal, non-commercial
purposes, and the robots.txt does not disallow the pages used. For that reason,
feiertagskalender.ch was scrapped with Playwright on 25/10/2026. Every page was cached as
an HTML file with a pause of 2 seconds between requests.

### Why Playwright with a real browser (instead of requests/BeautifulSoup)?
The website shows a security check to automated users. A plain HTTP request only gets the
check page, not the table. The script therefore attaches to a normal browser started by
the user (Chrome DevTools Protocol). When the check appears, the user confirms it manually
in the browser and the script continues.

### Why drop rows with code 9999?
9999 is not a real region or category, so these rows cannot be matched to cantons,
holidays or population.

### Why the population of each year and not one fixed year?
Population changes over 2019-2025 and not at the same speed in every canton. Using the
population of the same year keeps the weights correct.

### Why 0.5 to consider a region is in holiday?
A Grossregion has several cantons, so it is often only partly on holiday. A day is flagged
as is_holiday when at least half of the region’s population is off.

### When computing holiday shares, why these weights?
* Full holidays get the weight of their class: classes 1 and 2 (official holiday, holiday
on a par with Sundays) = 1.0. Class 3 (half-holiday) = 0.5, because only half of the day
is off. Class 4 (legally not recognized) is excluded and treated as a normal working day.
* Partial holidays use the population share from the website. Shares given as “< x %” are
used as x % (upper bound) because it is the only number the website gives. These shares
are small, so after weighting by population the error at region level stays small. This
case is frequent (620 of 1489 partial rows), so dropping these rows would lose too much
information. Partial holidays without a number (“varies”, “n.a.”, 166 rows) get 0 because
we cannot know how many people are off, so they are not counted.
* If many holidays fall on the same day in one canton, the maximum share is used so the
share stays between 0 and 1.

### Why put year before COVID in the regression
The R² is computed step by step. Variation shared by two groups goes to the group added
first. Year is added first because it captures long-term changes that are not caused by
COVID, such as the growth of card payments, inflation and population growth. COVID then
only gets the extra effect that the year level cannot explain.

* Limitation: the COVID period (16.03.2020–31.12.2022) covers all of 2021 and 2022. In
those years the year dummy and the COVID flag are identical, so the COVID effect can only
be estimated from 2020. That is why the COVID share is small. A narrower definition (only
the lockdown periods) would give COVID a larger share. We still chose the long period
because consumer behavior did not return to normal immediately after the lockdowns ended
(e.g. more home office, fewer business trips). The effect of these years is not lost: it
is captured by the year dummies, so in the R² table it appears under "year" instead of
"COVID".

### Why one regression per merchant category?
Categories react in opposite directions: retail falls on a holiday, while accommodation
rises. One model with all categories would mix these effects. Separate models are also
easier to read than many interaction terms.

### Why region first, and R² as share of within-region variation?
Regions differ mostly in size, which is not a calendar effect. Region is added first, and
every other group is shown as a share of the variation left inside a region. So the figure
answers: “within a region, how much of the day-to-day change is calendar?”

### Why holiday last in the R² steps?
This is the conservative choice. Holiday only gets the variation that weekday, month and
year cannot explain. Part of the Christmas or Easter effect is already taken by month, so
the holiday share is a lower bound.

### Why robust standard errors (HC1)?
The variance of spending is not the same on all days (it is larger in December or during
lockdowns). HC1 gives confidence intervals that stay valid when the variance differs
between days.

### Why a second model with region and date fixed effects (regional_holiday_effect.py)?
The calendar model also uses national holidays, so the holiday effect can mix with
anything else that happens on those dates (e.g. Christmas shopping before 25.12. The panel
model (PanelOLS) adds one effect per date, which removes everything that is the same for
all regions on that day (e.g. national holidays, weekday, weather), so only differences
between regions on the same date remain.

* The results showed that for accommodation, the calendar model gives +22 %, but the
regional model gives −7 % and is not significant (p = 0.17). The positive effect came from
national holidays, not from the regional holiday itself.

### Why kernel standard errors in the panel model?
Spending on one day is correlated with the days around it. Kernel (HAC) standard errors
allow this correlation over time, so the confidence intervals are not too narrow.

### Why a spending index (100 = average day) for weekday and month (exploration)?
The regions are summed into one national value per day, and each category is scaled to its
own average. This makes categories of different size comparable and gives a simple
descriptive view before moving to the regressions.