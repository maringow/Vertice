import operator
import numpy as np
import matplotlib as mpl
import datetime as dt
import pandas as pd
import re

##----------------------------------------------------------------------
## READ USER INPUT
# Placeholders, to be potentially replaced by inputs

# model_type: {BWAC, GWAC}
input_model_type = 'BWAC'

# channel: {Retail, Hospital, Clinic}
input_channel = 'Retail'

##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)

# Fake molecule-level sales & units data (priced @ $100-150/100mg)
molecule_1 = 'abc 100mg'
molecule_2 = 'abc 200mg'
molecule_3 = 'abc 6x50mg'

molecule_1_sales_2015_2018 = [25.0e6, 26.0e6, 28.0e6, 29.5e6]
molecule_2_sales_2015_2018 = [8.5e6, 9.1e6, 7.2e6, 11.0e6]
molecule_3_sales_2015_2018 = [13.2e6, 13.1e6, 11.8e6, 14.0e6]

molecule_1_units_2015_2018 = [166.7e3, 167.7e3, 177.2e3, 182.1e3]
molecule_2_units_2015_2018 = [35.4e3, 36.7e3, 28.5e3, 43.1e3]
molecule_3_units_2015_2018 = [40.0e3, 39.7e3, 35.8e3, 42.4e3]


# ingest IMS and price data
IMS = pd.read_csv('gleevec_IMS.csv')
prospectoRx = pd.read_csv('gleevec_prospectorx.csv')

# pull records that are therapeutic equivalents to selected brand name
#   parse brand name, strength, dosage
#   select IMS records that match user brand name input, strength, and dosage form

# parse NDC from IMS file
IMS.rename(index=str, columns={'NDC': 'NDC_ext'}, inplace=True)
IMS['NDC'] = ''
for index, row in IMS.iterrows():
    IMS['NDC'][index] = re.split('\s', IMS['NDC_ext'][index])[0]
IMS['NDC'] = pd.to_numeric(IMS['NDC'])

# join price and IMS on NDC
prospectoRx.rename(index=str, columns={'PackageIdentifier': 'NDC'}, inplace=True)
merged_data = IMS.merge(prospectoRx[['NDC', 'WACPrice']], how='left', on='NDC')

# build MultiIndex on Year and NDC
year_range = [int(i) for i in np.array(range(2016, 2030))]
NDCs = [int(i) for i in IMS['NDC'].unique()]

index_arrays = [year_range, NDCs]
multiIndex = pd.MultiIndex.from_product(index_arrays, names=['Year', 'NDC'])
df_detail = pd.DataFrame(index=multiIndex, columns=['Units', 'Price', 'Sales', 'COGS'])

df_detail['Units'].loc[2016][merged_data['NDC']] = pd.to_numeric(merged_data['2016_Units'].str.replace(',', ''))
df_detail['Units'].loc[2017][merged_data['NDC']] = pd.to_numeric(merged_data['2017_Units'].str.replace(',', ''))
df_detail['Units'].loc[2018][merged_data['NDC']] = pd.to_numeric(merged_data['2018_Units'].str.replace(',', ''))
df_detail['Units'].loc[2019][merged_data['NDC']] = pd.to_numeric(merged_data['2019_Units'].str.replace(',', ''))
# need to allow for 2020 units so that code doesn't break in January
# also need to make this code more concise

df_detail['Price'].loc[2016][merged_data['NDC']] = merged_data['WACPrice']
df_detail['Price'].loc[2017][merged_data['NDC']] = merged_data['WACPrice']
df_detail['Price'].loc[2018][merged_data['NDC']] = merged_data['WACPrice']
df_detail['Price'].loc[2019][merged_data['NDC']] = merged_data['WACPrice']

df_detail['Sales'] = df_detail['Units'] * df_detail['Price']

##----------------------------------------------------------------------
## DEFINE ANALOG TABLES
# Placeholder, likely to be replaced by pointing to Excel reference file

# Set up analogs by Number of Gx Players, from 0 to 10
df_analog = pd.DataFrame(index=range(0, 11))
df_analog['Retail Net Price Pct BWAC'] = \
    [1.00, 0.60, 0.35, 0.25, 0.20, 0.10, 0.05, 0.02, 0.01, 0.01, 0.01]
df_analog['Retail Market Share'] = \
    [0.00, 1.00, 0.50, 0.30, 0.25, 0.20, 0.10, 0.08, 0.05, 0.04, 0.03]
df_analog['Clinic Net Price Pct BWAC'] = \
    [1.00, 0.70, 0.55, 0.40, 0.25, 0.15, 0.10, 0.04, 0.01, 0.01, 0.01]
df_analog['Clinic Market Share'] = \
    [0.00, 1.00, 0.50, 0.30, 0.25, 0.20, 0.10, 0.08, 0.05, 0.04, 0.03]
df_analog['Hospital Net Price Pct BWAC'] = \
    [1.00, 0.80, 0.65, 0.45, 0.35, 0.20, 0.10, 0.04, 0.01, 0.01, 0.01]
df_analog['Hospital Market Share'] = \
    [0.00, 1.00, 0.50, 0.30, 0.25, 0.20, 0.10, 0.08, 0.05, 0.04, 0.03]
df_analog['Pct Profit Share'] = \
    [0.50, 0.50, 0.50, 0.25, 0.25, 0.25, 0.20, 0.20, 0.20, 0.20, 0.20]

##----------------------------------------------------------------------
##  SET UP DATA STRUCTURE
# Proposed: Two data structures
#   df_detail: Year-wise AND molecule-wise data frame, that reproduces Wes's detailed matrix calcs
#              The data frame starts with data from IMS, following Wes's approach
#   df_gfm: Year-wise data frame for "cross-molecule" assumptions and aggregated results

# Set up df_detail data frame
# TODO Finish initializing data frame
df_detail = pd.DataFrame()
df_detail['Year'] = list(range(2015, 2030, 1))
df_detail = df_detail.set_index(['Year'])
df_detail['Molecule'] = molecule_1
# Multiindex... maybe...


# Set up df_gfm data frame
df_gfm = pd.DataFrame()
df_gfm['Year'] = list(range(2015, 2030, 1))
df_gfm = df_gfm.set_index('Year')

##----------------------------------------------------------------------
## DEFINE FORECAST ASSUMPTIONS
# Scratch calcs... some of these will likely be replaced by user input
df_gfm['Total Market Growth Pct'] = 0.10
df_gfm['Gx Penetration'] = 0.50
df_gfm['WAC Increase Pct'] = 0.05
df_gfm['GTN Chargebacks Pct'] = 0.25
df_gfm['GTN Other Pct'] = 0.10
df_gfm['Price Discount of Current Gx Net'] = 0.0

# Hard-coded # of Gx Players (for now)
df_gfm['N Gx Players'] = 3
df_gfm.at[2015, 'N Gx Players'] = 2
df_gfm.at[2020, 'N Gx Players'] = 4

# Look up market share using channel-specific analog table
col_name = [input_channel + ' Market Share']
df_gfm['Gx Market Share'] = df_analog.loc[df_gfm['N Gx Players'], col_name].values

# Assign Vertice price as % of either BWAC or GWAC
if input_model_type == 'BWAC':
    col_name = [input_channel + ' Net Price Pct BWAC']
    df_gfm['Vertice Price as Pct of WAC'] = df_analog.loc[df_gfm['N Gx Players'], col_name].values
else:
    df_gfm['Vertice Price as Pct of WAC'] = \
        (1 - df_gfm['GTN Chargebacks Pct'] - df_gfm['GTN Other Pct']) * \
        (1 - df_gfm['Price Discount of Current Gx Net'])

##----------------------------------------------------------------------
## PERFORM FINANCIAL CALCULATIONS
# For each year
#    Perform year-wise financial calculations
# Perform present-value calculations (NPV, IRR, etc.)


# Placeholder variables, to be replaced later
discount_rate = 0.15
tax_rate = 0.21





##----------------------------------------------------------------------
## GENERATE OUTPUT
