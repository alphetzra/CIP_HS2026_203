"""Population data acquisition from BFS (STATPOP)"""

import pandas as pd
import config


def acquire_population():
    """Download the permanent resident population per canton.
            Contains the 26 cantons, from 2019-2025, with totals of residence permit,
            place of birth, sex and age, and saves the raw data to config.POP_FILE.
            Returns:
                DataFrame with the downloaded data
            """
    url = "https://disseminate.stats.swiss/rest/data/CH1.STATPOP,DF_STATPOP_KANT_AUT_ORT_SEX_AGE,1.0.0/1+2+3+4+5+6+7+8+9+10+11+12+13+14+15+16+17+18+19+20+21+22+23+24+25+26._T._T._T._T.A?startPeriod=2019&endPeriod=2025&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
    df =  pd.read_csv(url)
    df.to_csv(config.POP_FILE)
    print(f"Saved {len(df)} rows to {config.POP_FILE}")
    return df