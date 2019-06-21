import operator
import numpy as np
import matplotlib as mpl
import datetime as dt
import pandas as pd

# import user excel
# 


##----------------------------------------------------------------------
## READ USER INPUT
# Placeholders, to be potentially replaced by inputs
model_type = 'BWAC'



##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)

# idea - we should get the list of brand names from IMS to populate the user's input selections (Excel dropdown?)

# ingest IMS
# df_IMS = pd.read_csv('')

# parse NDC, dosage, and

# volume = pd.read_csv(xxx)

# parse NDC
# join price and volume on NDC

price = pd.read_csv('C:\\Users\\mgow\\Documents\Clients\\5. Vertice\\Model Inputs\\gleevec_prospectorx.csv')

##----------------------------------------------------------------------
## DEFINE ANALOG TABLES
# Placeholder, likely to be replaced by pointing to Excel reference file

# Set up analogs by Number of Gx Players, from 1 to 10
df_analog = pd.DataFrame(index=range(0,11))
df_analog['Retail Net Price Pct BWAC'] = \
     [1.00, 0.60, 0.35, 0.25, 0.20, 0.10, 0.05, 0.02, 0.01, 0.01, 0.01]
df_analog['Retail Pct Market Share'] = \
     [0.00, 1.00, 0.50, 0.30, 0.25, 0.20, 0.10, 0.08, 0.05, 0.04, 0.03]
df_analog['Clinic Net Price Pct BWAC'] = \
     [1.00, 0.70, 0.55, 0.40, 0.25, 0.15, 0.10, 0.04, 0.01, 0.01, 0.01]
df_analog['Clinic Pct Market Share'] = \
     [0.00, 1.00, 0.50, 0.30, 0.25, 0.20, 0.10, 0.08, 0.05, 0.04, 0.03]
df_analog['Hospital Net Price Pct BWAC'] = \
     [1.00, 0.80, 0.65, 0.45, 0.35, 0.20, 0.10, 0.04, 0.01, 0.01, 0.01]
df_analog['Hospital Pct Market Share'] = \
     [0.00, 1.00, 0.50, 0.30, 0.25, 0.20, 0.10, 0.08, 0.05, 0.04, 0.03]
df_analog['Pct Profit Share'] = \
     [0.50, 0.50, 0.50, 0.25, 0.25, 0.25, 0.20, 0.20, 0.20, 0.20, 0.20]



##----------------------------------------------------------------------
##  SET UP DATA STRUCTURE
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
#df_gfm['Vertice Gx Market Share'] =



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

