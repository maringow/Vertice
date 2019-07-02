import operator
import numpy as np
import matplotlib as mpl
import datetime as dt
import pandas as pd
import re
import openpyxl as xl
import tkinter
from tkinter import *
from tkinter import ttk

##----------------------------------------------------------------------
## READ USER INPUT
# Placeholders, to be potentially replaced by inputs

# model_type: {BWAC, GWAC}
input_model_type = 'BWAC'

# channel: {Retail, Hospital, Clinic}
input_channel = 'Retail'



# read user input Excel file
wb = xl.load_workbook(filename='Model Inputs.xlsx', read_only=True)
sheet = wb['Input']

# assign single-value variables from Excel cells into parameters dict
parameters = {'brand_name': sheet['B5'].value,
              'brand_status': sheet['B6'].value,
              'channel': sheet['B7'].value
              }  # more to be added


# assign year-based variables into df df_gfm
#df_gmf = pd.dataframe()










##----------------------------------------------------------------------
##  SET UP MAIN DATA STRUCTURES
# Main data structures
#   df_detail: Year-wise AND NDC-wise data frame, that reproduces Wes's detailed matrix calcs
#              The data frame starts with data from IMS, following Wes's approach
#   df_gfm: Year-wise data frame for "cross-molecule" assumptions and aggregated results

# Set up df_detail data frame


# Set up df_gfm data frame
df_gfm = pd.DataFrame()
df_gfm['Year'] = list(range(2015, 2030, 1))
df_gfm = df_gfm.set_index('Year')


##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx) AND FIND THERAPEUTIC EQUIVALENTS

# ingest IMS and price data
IMS = pd.read_csv('sample_8_molecules_w_product.csv')
prospectoRx = pd.read_csv('gleevec_prospectorx.csv')

# pull records that are therapeutic equivalents of selected brand name drug
# find Combined Molecule and Prod Form 3 of selected brand name drug; store in lists in case there are multiple
combined_molecules = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Combined Molecule'].unique()
dosage_forms = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Prod Form3'].unique()

# find all IMS records that match the Combined Molecule and Prod Form 3
df_equivalents = IMS.loc[(IMS['Combined Molecule'].isin(combined_molecules)) & (IMS['Prod Form3'].isin(dosage_forms))]
print(df_equivalents)

# parse NDC from equivalents dataframe (from IMS file)
df_equivalents.rename(index=str, columns={'NDC': 'NDC_ext'}, inplace=True)
df_equivalents['NDC'] = ''
for index, row in df_equivalents.iterrows():  ## split out anything after first space and remove non-numeric chars
    df_equivalents['NDC'][index] = re.sub('[^0-9]', '', re.split('\s', df_equivalents['NDC_ext'][index])[0])
df_equivalents['NDC'] = pd.to_numeric(df_equivalents['NDC'])
df_equivalents['NDC'].fillna(999, inplace=True)  ## if NDC is "NDC NOT AVAILABLE" or other invalid value, fill with 999

# join price and therapeutic equivalents on NDC
prospectoRx.rename(index=str, columns={'PackageIdentifier': 'NDC'}, inplace=True)
df_merged_data = df_equivalents.merge(prospectoRx[['NDC', 'WACPrice']], how='left', on='NDC')

# TODO if no price match on NDC is found, use the lowest price for the same strength and package units
#     if no record with the same strength and package units, use the lowest overall price

# build hierarchical index on Year and NDC
year_range = [int(i) for i in np.array(range(2016, 2030))]
NDCs = [int(i) for i in df_equivalents['NDC'].unique()]
index_arrays = [year_range, NDCs]
multiIndex = pd.MultiIndex.from_product(index_arrays, names=['Year', 'NDC'])

# create df with multiindex
df_detail = pd.DataFrame(index=multiIndex, columns=['Units', 'Price', 'Sales', 'COGS'])

# create list of Units columns from IMS data
columns = [[2016, '2016_Units'], [2017, '2017_Units'], [2018, '2018_Units'], [2019, '2019_Units'],
           [2020, '2020_Units'], [2021, '2021_Units'], [2022, '2022_Units']]

# iterate over columns list as long as they are found in the IMS data and map units and price into df_detail
for year in columns:
    if year[1] in df_merged_data.columns:
        df_detail['Units'].loc[year[0]][df_merged_data['NDC']] = pd.to_numeric(
            df_merged_data[year[1]].str.replace(',', ''))
        df_detail['Price'].loc[year[0]][df_merged_data['NDC']] = df_merged_data['WACPrice']
    else:
        break

# TODO add a check here that data has successfully populated df_detail Units and Price - this
#  will catch column name changes

# calculate Sales as Units * Price
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

# Dummy data (entering costs as negative numbers)
distribution_percent = .006
writeoff_percent = .012
DIO = 60
DSO = 60
DPO = 30
df_gfm['Profit Share %'] = np.repeat(0.25,15)
df_gfm['Milestone Payments'] =  np.repeat(-0.1,15)
df_gfm['Gross Sales'] =  np.arange(3,6,.2)
df_gfm.at[2015, 'Gross Sales'] = 0
df_gfm['Net Sales'] =  np.arange(3,6,.2)
df_gfm.at[2015, 'Net Sales'] = 0
df_gfm['Standard COGS'] =  -np.arange(.2,1.7,.1)
df_gfm['SG&A'] =  np.repeat(-0.01,15)
df_gfm['R&D Project Expense'] =  np.repeat(-0.01,15)
df_gfm['Incremental R&D Headcount Expense'] =  np.repeat(-0.01,15)
df_gfm['R&D infrastructure cost'] =  np.repeat(-0.01,15)

# Calculations for financials
df_gfm['Distribution'] = -df_gfm['Gross Sales'] * distribution_percent
df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * writeoff_percent
df_gfm['Profit Share'] = -(df_gfm['Gross Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm['Profit Share %']
df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
df_gfm['R&D']  = df_gfm['R&D Project Expense'] + df_gfm['Incremental R&D Headcount Expense'] + df_gfm['R&D infrastructure cost']
df_gfm['Inventory'] = - DIO * df_gfm['Standard COGS']/360
df_gfm['Accounts Receivable'] = DSO * df_gfm['Net Sales']/360
df_gfm['Accounts Payable'] = - DPO * (df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments'] + df_gfm['SG&A'])/360
df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - df_gfm['Accounts Payable']
df_gfm['Change in Working Capital'] = df_gfm['Working Capital'] - df_gfm['Working Capital'].shift(1)
df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] #doesn't deduct depreciation so technically EBITDA

##----------------------------------------------------------------------
## PERFORM FINANCIAL CALCULATIONS
# For each year
#    Perform year-wise financial calculations
# Perform present-value calculations (NPV, IRR, etc.)

# Dummy data
discount_rate = 0.15
tax_rate = 0.21
exit_multiple = 7
df_gfm['FCF'] = [0,0,0,0,-10.2,-0.1,3.3,4.3,5.2,6.1,6.3,7.3,7.2,7.1,7]
df_gfm['EBIT'] = [0,0,0,0,1.2,0.1,0.3,2.3,3.2,3.1,4.3,4.3,4.2,3.1,5]

# Need to know base year to discount PV to
present_year = 2018

# IRR
irr = np.irr(df_gfm.FCF.loc[present_year:])

# NPV
x = 0
pv = []
for i in df_gfm.FCF.loc[present_year:]:
    pv.append(i/(1+discount_rate)**x)
    x += 1
df_gfm['FCF PV'] = 0
df_gfm['FCF PV'].loc[present_year:] = pv
npv = df_gfm['FCF PV'].iloc[-1]

# Discounted Payback Period
df_gfm['Cummulative Discounted FCF'] = np.cumsum(df_gfm["FCF PV"].loc[present_year:])
idx = df_gfm[df_gfm['Cummulative Discounted FCF'] <= 0].index.max() #last full year for payback calc
discounted_payback_period = idx - present_year - df_gfm['Cummulative Discounted FCF'].loc[idx]/df_gfm['FCF PV'].loc[idx+1]

# Exit value in 2021
exit_value_2021 = df_gfm['EBIT'].loc[2021] * exit_multiple

del x, idx

# TODO need to calculate MOIC

##----------------------------------------------------------------------
## GENERATE OUTPUT
