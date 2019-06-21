import operator
import numpy as np
import matplotlib as mpl
import datetime as dt
import pandas as pd


## READ USER INPUT

# Placeholders, to be potentially replaced by inputs
model_type = 'BWAC'

## INGEST DATA (IMS, ProspectoRx)


## SET UP DATA STRUCTURE
df_gfm = pd.DataFrame()
df_gfm['Year'] = list(range(2015, 2030, 1))
df_gfm = df_gfm.set_index('Year')

## FORECAST ASSUMPTIONS
df_gfm['Total Market Growth'] = 0.1
df_gfm['Gx Penetration'] = 0.5
df_gfm['N Gx Players'] = 3
df_gfm.at[2015,'N Gx Players'] = 2



## PERFORM FINANCIAL CALCULATIONS
# For each year
#    Perform year-wise financial calculations
# Perform present-value calculations (NPV, IRR, etc.)


# Placeholder variables, to be replaced later
discount_rate = 0.15
tax_rate = 0.21


# Placeholder series, to be replaced later
years = list(range(2015, 2030, 1))
sales = pd.Series(index=years)



## GENERATE OUTPUT

