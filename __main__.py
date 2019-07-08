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
import gui



##----------------------------------------------------------------------
## DEFINE ANALOG TABLES

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
## INGEST DATA (IMS, ProspectoRx)

# ingest IMS and price data
IMS = pd.read_csv('full_extract_6.26.csv')
prospectoRx = pd.read_csv('gleevec_prospectorx.csv')

# get valid brands from IMS file
# TODO remove NaNs from these lists
brands = sorted(IMS.loc[IMS['Brand/Generic'] == 'BRAND']['Product Sum'].unique())
molecules = IMS['Combined Molecule'].unique().tolist()

parameters = {}


##----------------------------------------------------------------------
## OPEN BRAND SELECTION AND SAVE PARAMETERS
window = Tk()
window1 = gui.BrandSelection(window, brands, molecules)
window.mainloop()

parameters.update(window1.w1_parameters)
print(parameters)

##----------------------------------------------------------------------
## FIND DOSAGE FORMS, OPEN DOSAGE FORM WINDOW AND SAVE SELECTIONS

try:
    if parameters['search_type'] == 'brand':
        parameters['combined_molecules'] = IMS.loc[IMS['Product Sum'] == parameters['brand_name']][
            'Combined Molecule'].unique()
        parameters['dosage_forms'] = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Prod Form2'].unique()
    elif parameters['search_type'] == 'molecule':
        parameters['combined_molecules'] = [parameters['molecule_name']]
        parameters['dosage_forms'] = IMS.loc[IMS['Combined Molecule'] == parameters['molecule_name']]['Prod Form2'].unique()
except KeyError:
    print('Please select a brand or molecule to run the model.')

print(parameters['dosage_forms'])

# if more than one dosage form is found, prompt user to select desired forms
if len(parameters['dosage_forms']) > 1:
    window = Tk()
    window2 = gui.DosageForms(window, parameters['dosage_forms'])
    window.mainloop()
    parameters['dosage_forms'] = window2.selected_dosage_forms

print(parameters['dosage_forms'])

##----------------------------------------------------------------------
## FIND THERAPEUTIC EQUIVALENTS

# find all IMS records that match the Combined Molecule and Prod Form2
df_equivalents = IMS.loc[(IMS['Combined Molecule'].isin(parameters['combined_molecules'])) &
                         (IMS['Prod Form2'].isin(parameters['dosage_forms']))]
parameters['count_eqs'] = len(df_equivalents)


##----------------------------------------------------------------------
## JOIN IMS AND PROSPECTO DATASETS

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
multiIndex = pd.MultiIndex.from_product(index_arrays, names=['year_index', 'ndc_index'])

# create df with multiindex
df_detail = pd.DataFrame(index=multiIndex, columns=['NDC', 'Units', 'Price', 'Sales', 'COGS'])
df_detail['NDC'] = df_detail.index.get_level_values('ndc_index')

# create list of Units columns from IMS data
columns = [[2016, '2016_Units'], [2017, '2017_Units'], [2018, '2018_Units'], [2019, '2019_Units'],
           [2020, '2020_Units'], [2021, '2021_Units'], [2022, '2022_Units']]

# map units and price into df_detail
for year in columns:
    if year[1] in df_merged_data.columns:
        df_detail['Units'].loc[year[0]][df_merged_data['NDC']] = pd.to_numeric(
            df_merged_data[year[1]].str.replace(',', ''))
        df_detail['Price'].loc[year[0]][df_merged_data['NDC']] = df_merged_data['WACPrice']
    else:
        break

# TODO add a check here that data has successfully populated df_detail Units and Price - this
#    will catch column name changes

# calculate Sales as Units * Price
df_detail['Sales'] = df_detail['Units'] * df_detail['Price']


##----------------------------------------------------------------------
## WINDOW2: OPEN ConfirmBrand WINDOW AND SAVE
window = Tk()
window3 = gui.ConfirmBrand(window, parameters)
window.mainloop()


##----------------------------------------------------------------------
## WINDOW3: OPEN EnterCOGS WINDOW AND SAVE VALUES
window = Tk()
window4 = gui.EnterCOGS(window, df_equivalents)
window.mainloop()

parameters['api_units'] = window4.COGS['units']
parameters['api_cost_per_unit'] = pd.to_numeric(window4.COGS['cost_per_unit'])
df_merged_data['API_units'] = 0

# map COGS into df_merged_data and df_detail
for key, value in window4.COGS['units_per_pack'].items():
    df_merged_data['API_units'].loc[df_merged_data['Pack'] == key] = pd.to_numeric(value)
df_merged_data['API_cost'] = df_merged_data['API_units'] * parameters['api_cost_per_unit']
df_detail = pd.merge(df_detail.reset_index(), df_merged_data[['NDC', 'API_cost']], on='NDC', how='left').set_index(['year_index', 'ndc_index'])
df_detail['COGS'] = df_detail['Units'] * df_detail['API_cost']
df_detail.drop(columns=['API_cost'])
print(df_detail)

##----------------------------------------------------------------------
## WINDOW4: OPEN EnterFilepath WINDOW AND SAVE VALUES
window = Tk()
window5 = gui.EnterFilepath(window, parameters)
window.mainloop()

parameters.update(window5.parameters)

##----------------------------------------------------------------------
## READ EXCEL

# read user input Excel file
# TODO parse filename - correct backslashes and add .xlsx if not already there

wb = xl.load_workbook(filename=parameters['excel_filepath'], read_only=True)
sheet = wb['Input']

# assign single-value variables from Excel cells into parameters dict
parameters.update({'brand_status': sheet['B6'].value,
                   'channel': sheet['B7'].value,
                   'channel_detail': sheet['B8'].value,
                   'vertice_filing_month': sheet['B9'].value,
                   'vertice_filing_year': sheet['B10'].value,
                   'vertice_launch_month': sheet['B11'].value,
                   'vertice_launch_year': sheet['B12'].value,
                   'indication': sheet['B13'].value,
                   'presentation': sheet['B14'].value,
                   'loe_year': sheet['B15'].value,
                   'competition_detail': sheet['B16'].value,
                   'pos': sheet['B17'].value,
                   'comments': sheet['B18'].value,
                   'volume_growth_rate': sheet['B22'].value,
                   'wac_increase': sheet['B23'].value,
                   'chargebacks': sheet['B24'].value,
                   'other_gtn': sheet['B25'].value,
                   'DIO': sheet['B43'].value,
                   'DSO': sheet['B44'].value,
                   'DPO': sheet['B45'].value,
                   'discount_rate': sheet['B49'].value,
                   'tax_rate': sheet['B50'].value,
                   'exit_multiple': sheet['B51'].value,
                   'cogs': {'excipients': sheet['B31'].value,
                            'direct_labor': sheet['B32'].value,
                            'variable_overhead': sheet['B33'].value,
                            'fixed_overhead': sheet['B34'].value,
                            'depreciation': sheet['B35'].value,
                            'cmo_markup': sheet['B36'].value,
                            'cost_increase': sheet['B37'].value,
                            'distribution': sheet['B38'].value,
                            'writeoffs': sheet['B39'].value}
                    })  # more to be added

# set up df_gfm data frame
df_gfm = pd.DataFrame()
df_gfm['Year'] = list(range(2015, 2030, 1))
df_gfm = df_gfm.set_index('Year')

# add excel parameters

df_gfm['N Gx Players'] = 3
df_gfm.at[2015, 'N Gx Players'] = 2
df_gfm.at[2020, 'N Gx Players'] = 4

# Look up market share using channel-specific analog table
col_name = [parameters['channel'] + ' Market Share']
df_gfm['Gx Market Share'] = df_analog.loc[df_gfm['N Gx Players'], col_name].values



# read Excel parameters - currently dummy data
df_gfm['Price Discount of Current Gx Net'] = np.repeat(0.25, 15)
df_gfm['Profit Share %'] = np.repeat(0.25,15)
df_gfm['Milestone Payments'] =  np.repeat(-0.1,15)
df_gfm['Gross Sales'] =  np.arange(3,6,.2)
df_gfm.at[2015, 'Gross Sales'] = 0
df_gfm['Net Sales'] =  np.arange(3,6,.2)
df_gfm.at[2015, 'Net Sales'] = 0
df_gfm['Standard COGS'] =  -np.arange(.2,1.7,.1)
df_gfm['SG&A'] =  np.repeat(-0,15)
df_gfm['R&D Project Expense'] =  np.repeat(-0.01,15)
df_gfm['Incremental R&D Headcount Expense'] =  np.repeat(-0.01,15)
df_gfm['R&D infrastructure cost'] =  np.repeat(-0.01,15)
df_gfm['Tax depreciation'] = 0
df_gfm['Net proceeds from Disposals'] = 0
df_gfm['Write-off of Residual Tax Value'] = 0
df_gfm['Other Income, Expenses, Except Items'] = 0
df_gfm['Additional Non-cash Effects'] = 0
df_gfm['Other Net Current Assets'] = 0
df_gfm['Capital Avoidance'] = 0
df_gfm['Capitalized Items - Item 1'] = 0
df_gfm['Capitalized Items - Item 2'] = 0
df_gfm['Capitalized Items - Item 3'] = 0
df_gfm['Capitalized Items - Item 4'] = 0
df_gfm['Other Expensed Items - Item 1'] = 0
df_gfm['Other Expensed Items - Item 2'] = 0
df_gfm['Other Expensed Items - Item 3'] = 0
df_gfm['Other Expensed Items - Item 4'] = 0
df_gfm['Other Impacts on P&L - Item 1'] = 0
df_gfm['Other Impacts on P&L - Item 2'] = 0
df_gfm['Other Impacts on P&L - Item 3'] = 0
df_gfm['Other Impacts on P&L - Item 4'] = 0

# Assign Vertice price as % of either BWAC or GWAC
if parameters['brand_status'] == 'BWAC':
    col_name = [parameters['channel'] + ' Net Price Pct BWAC']
    df_gfm['Vertice Price as Pct of WAC'] = df_analog.loc[df_gfm['N Gx Players'], col_name].values
else:
    df_gfm['Vertice Price as Pct of WAC'] = \
        (1 - parameters['chargebacks'] - parameters['other_gtn']) * \
        (1 - df_gfm['Price Discount of Current Gx Net'])

# Calculations for financials
df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
df_gfm['Profit Share'] = -(df_gfm['Net Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm['Profit Share %']
df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
df_gfm['R&D']  = df_gfm['R&D Project Expense'] + df_gfm['Incremental R&D Headcount Expense'] + df_gfm['R&D infrastructure cost']
df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS']/360
df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales']/360
df_gfm['Accounts Payable'] = - parameters['DPO'] * (df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments'] + df_gfm['SG&A'])/360
df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - df_gfm['Accounts Payable']
# df_gfm['Change in Working Capital'] = df_gfm['Working Capital'] - df_gfm['Working Capital'].shift(1)
# df_gfm['Change in Working Capital'] = df_gfm['Change in Working Capital'].fillna(0)
df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - df_gfm['Tax depreciation'] #essentially "adjusted EBIT" as it doesn't include other impacts, proceeds from disposals, write-offs of residual tax value, etc
df_gfm['Total Capitalized'] = df_gfm['Capitalized Items - Item 1'] + df_gfm['Capitalized Items - Item 2'] + df_gfm['Capitalized Items - Item 3'] +df_gfm['Capitalized Items - Item 4']
df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + df_gfm['Write-off of Residual Tax Value'] + df_gfm['Other Income, Expenses, Except Items'] + df_gfm['Other Expensed Items - Item 1'] + df_gfm['Other Expensed Items - Item 2'] + df_gfm['Other Expensed Items - Item 3'] + df_gfm['Other Expensed Items - Item 4'] + df_gfm['Other Impacts on P&L - Item 1'] + df_gfm['Other Impacts on P&L - Item 2'] + df_gfm['Other Impacts on P&L - Item 3'] + df_gfm['Other Impacts on P&L - Item 4']
df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + df_gfm['Other Net Current Assets'] #put in as positive numbers, different than excel
df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - df_gfm['Total Net Current Assets'].shift(1)
df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + df_gfm['Tax depreciation'] + df_gfm['Additional Non-cash Effects'] - df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + df_gfm['Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']

##----------------------------------------------------------------------
## PERFORM FINANCIAL CALCULATIONS
# For each year
#    Perform year-wise financial calculations
# Perform present-value calculations (NPV, IRR, etc.)

present_year = 2018 # Need to know base year to discount PV to

# IRR
irr = np.irr(df_gfm.FCF.loc[present_year:])

# NPV
x = 0
pv = []
for i in df_gfm.FCF.loc[present_year:]:
    pv.append(i/(1+parameters['discount_rate'])**x)
    x += 1
npv = sum(pv)

# Discounted Payback Period
df_gfm['FCF PV'] = 0
df_gfm['FCF PV'].loc[present_year:] = pv
df_gfm['Cummulative Discounted FCF'] = np.cumsum(df_gfm["FCF PV"].loc[present_year:])
df_gfm['Cummulative Discounted FCF'] = df_gfm['Cummulative Discounted FCF'].fillna(0)
idx = df_gfm[df_gfm['Cummulative Discounted FCF'] <= 0].index.max() #last full year for payback calc
discounted_payback_period = idx - present_year + 1- df_gfm['Cummulative Discounted FCF'].loc[idx]/df_gfm['FCF PV'].loc[idx+1]
V_weird_discount_payback_period_calc = idx - present_year + 3.5 - (df_gfm['Cummulative Discounted FCF'].loc[idx+1] / (df_gfm['Cummulative Discounted FCF'].loc[idx+1] - df_gfm['Cummulative Discounted FCF'].loc[idx]))

# Exit values (specificially saves value in 2021)
df_gfm['Exit Values'] = df_gfm['EBIT'] * parameters['exit_multiple']
exit_value_2021 = df_gfm['Exit Values'].loc[2021]

# MOIC in 2021
amt_invested = df_gfm['Total Capitalized'] + df_gfm['R&D'] + df_gfm['SG&A'] + df_gfm['Milestone Payments']
cum_amt_invested =np.cumsum(amt_invested)
MOIC = []
for i in range(len(df_gfm['Exit Values'])):
    if cum_amt_invested.iloc[i] == 0:
        MOIC.append(0)
    else:
        MOIC.append(-df_gfm['Exit Values'].iloc[i] / cum_amt_invested.iloc[i])
df_gfm["MOIC"] = MOIC
MOIC_2021 = df_gfm["MOIC"].loc[2021]

del x, pv, idx, amt_invested, cum_amt_invested, MOIC

##----------------------------------------------------------------------
## GENERATE OUTPUT
