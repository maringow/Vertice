import operator
import numpy as np
import matplotlib as mpl
import datetime as dt
import pandas as pd


##----------------------------------------------------------------------
## READ USER INPUT
# Placeholders, to be potentially replaced by inputs
model_type = 'BWAC'



##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)




##----------------------------------------------------------------------
## DEFINE ANALOG TABLES
# Placeholder, likely to be replaced by pointing to Excel reference file

# Set up analogs by Number of Gx Players



##----------------------------------------------------------------------
## SET UP DATA STRUCTURE
df_gfm = pd.DataFrame()
df_gfm['Year'] = list(range(2015, 2030, 1))
df_gfm = df_gfm.set_index('Year')


##----------------------------------------------------------------------
## DEFINE FORECAST ASSUMPTIONS
# Scratch calcs... some of these will likely be replaced by user input
df_gfm['Total Market Growth Rate'] = 0.10
df_gfm['Gx Penetration'] = 0.50
df_gfm['N Gx Players'] = 3
df_gfm['WAC Increase Rate'] = 0.05
df_gfm.at[2015,'N Gx Players'] = 2
df_gfm['GTN Chargebacks'] = 0.25
df_gfm['GTN Other'] = 0.10

# Calculations on Forecast Assumptions
df_gfm['Vertice Gx Market Share'] =



##----------------------------------------------------------------------
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



##----------------------------------------------------------------------
## GENERATE OUTPUT

