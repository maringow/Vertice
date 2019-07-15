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
import sqlite3
from sqlite3 import Error
import output
#import warnings
#warnings.filterwarnings('ignore')
import fincalcs
import readinputs
import mergedatasets


##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)

# ingest IMS and price data
IMS = pd.read_csv('full_extract_6.26.csv')
prospectoRx = pd.read_csv('prospecto_all_one_year_20190708.csv')

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
        parameters['dosage_forms'] = IMS.loc[IMS['Combined Molecule'] ==
                                             parameters['molecule_name']]['Prod Form2'].unique()
except KeyError:
    print('Please select a brand or molecule to run the model.')

print(parameters['dosage_forms'])



##----------------------------------------------------------------------
## OPEN DOSAGE FORM SELECTION IF MORE THAN ONE DOSAGE FORM IS FOUND

if len(parameters['dosage_forms']) > 1:
    window = Tk()
    window2 = gui.DosageForms(window, parameters['dosage_forms'])
    window.mainloop()
    parameters['dosage_forms'] = window2.selected_dosage_forms

print(parameters['dosage_forms'])

##----------------------------------------------------------------------
## FIND THERAPEUTIC EQUIVALENTS AND JOIN IMS AND PROSPECTO DATASETS

# find all IMS records that match the Combined Molecule and Prod Form2
df_equivalents = mergedatasets.get_equiv(IMS, parameters)
parameters['count_eqs'] = len(df_equivalents)

df_merged_data, df_detail = mergedatasets.merge_ims_prospecto(df_equivalents, prospectoRx)

##----------------------------------------------------------------------
## WINDOW2: OPEN ConfirmBrand WINDOW AND SAVE

# TODO maybe add volume and price numbers to this - could help user forecast growth and confirm code is working
# TODO make count_competitors work past 2019

# set parameters to display in confirmation window
parameters['count_competitors'] = len(df_equivalents.loc[pd.isnull(df_equivalents['2018_Units']) == False]
                                      ['Manufacturer'].unique())
parameters['historical_growth_rate'] = fincalcs.get_growth_rate(df_detail)
print(parameters['historical_growth_rate'])

# open window
window = Tk()
window3 = gui.ConfirmBrand(window, parameters)
window.mainloop()


##----------------------------------------------------------------------
## WINDOW4: OPEN EnterFilepath WINDOW AND SAVE VALUES
window = Tk()
window5 = gui.EnterFilepath(window)
window.mainloop()

parameters.update(window5.parameters)


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
#df_detail['COGS'] = df_detail['Units'] * df_detail['API_cost']
#df_detail.drop(columns=['API_cost'])
print(df_detail)

##----------------------------------------------------------------------
## READ EXCEL

# Read user input Excel file
parameters, df_gfm, df_analog = readinputs.read_model_inputs(parameters)

#Financial Calcs
irr, npv, discounted_payback_period, mkt_size, mkt_vol, yearly_data = fincalcs.financial_calculations(parameters, df_gfm, df_detail, df_analog)
df_analog = pd.DataFrame(index=range(0, 10))
df_analog['Retail Net Price Pct BWAC'] = pull_analog_data(2)
#df_analog['Retail Market Share'] = pull_analog_data(3)
df_analog['Clinic Net Price Pct BWAC'] = pull_analog_data(4)
#df_analog['Clinic Market Share'] = pull_analog_data(5)
df_analog['Hospital Net Price Pct BWAC'] = pull_analog_data(6)
#df_analog['Hospital Market Share'] = pull_analog_data(7)
df_analog.index.name = "Number of Gx Players"
df_analog = df_analog.fillna(0)

# Assign Vertice price as % of either BWAC or GWAC
if parameters['brand_status'] == 'Brand':
    col_name = [parameters['channel'] + ' Net Price Pct BWAC']
    df_gfm['Vertice Price as % of WAC'] = df_analog.loc[df_gfm['Number of Gx Players'], col_name].values
else:
    df_gfm['Vertice Price as % of WAC'] = (1 - parameters['gtn_%']) * (1 - df_gfm['Price Discount of Current Gx Net Price'])

# df_detail calcs currently doesn't account for wac growth, cogs growth, volume growth, and change in penetration rate
# Keep market unit sales for reference
df_gfm['Market Volume'] = df_detail['Units'].groupby(level=[0]).sum()  # TODO somehow annualize the volumes???

# Calculating volume of market in future
for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
    df_detail.loc[i]['Units'] = df_detail.loc[i - 1]['Units'] * (1 + parameters['volume_growth_rate'])

# Adjust volumes for launch year and if there is a partial year
vol_adj = []
for i in range(2016, parameters['last_forecasted_year'] + 1):
    if i < parameters['vertice_launch_year']:
        vol_adj.append(0)
    elif i == parameters['vertice_launch_year']:
        vol_adj.append((13 - parameters['vertice_launch_month']) / 12)
    else:
        vol_adj.append(1)

df_vertice_ndc_volumes = df_detail['Units'].mul(vol_adj * df_gfm['Gx Penetration'], level=0,
                                                 fill_value=0).mul(df_gfm['Vertice Gx Market Share'], level=0,
                                                                   fill_value=0)
df_vertice_ndc_volumes = df_vertice_ndc_volumes * parameters['pos']
print(df_vertice_ndc_volumes)


# Calculating price (WAC) in future
for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
    df_detail.loc[i]['Price'] = df_detail.loc[i - 1]['Price'] * (1 + parameters['wac_increase'])

df_vertice_ndc_prices = df_detail['Price'].mul(df_gfm['Vertice Price as % of WAC'], level=0, fill_value=0)
print(df_vertice_ndc_prices)

df_gfm['Net Sales'] = (df_vertice_ndc_prices * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

# Calculating API_cost in future
for i in range(parameters['present_year'] + 1, parameters['last_forecasted_year'] + 1):
    df_detail.loc[i]['API_cost'] = df_detail.loc[i - 1]['API_cost'] * (1 + parameters['cogs']['cost_increase'])

df_gfm['Standard COGS'] = -(df_detail['API_cost'] * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000
print(df_gfm['Standard COGS'])

df_gfm['Other Unit COGS'] = -((parameters['cogs']['excipients'] + parameters['cogs']['direct_labor'] + parameters['cogs']['variable_overhead'] + parameters['cogs']['fixed_overhead'] + parameters['cogs']['depreciation'] + parameters['cogs']['cmo_markup']) * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

# Financial statement calculations
df_gfm['Gross Sales'] =  df_gfm['Net Sales'] / (1-parameters['gtn_%'])
df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
df_gfm['Profit Share'] = -(df_gfm['Net Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm['Profit Share %']
df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Other Unit COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
# df_gfm['R&D']  = df_gfm['R&D Project Expense'] + df_gfm['Incremental R&D Headcount Expense'] + df_gfm['R&D infrastructure cost']
df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS']/360
df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales']/360
df_gfm['Accounts Payable'] = - parameters['DPO'] * (df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments'] + df_gfm['SG&A'])/360
df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - df_gfm['Accounts Payable']
# df_gfm['Change in Working Capital'] = df_gfm['Working Capital'] - df_gfm['Working Capital'].shift(1)
# df_gfm['Change in Working Capital'] = df_gfm['Change in Working Capital'].fillna(0)
df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - df_gfm['Tax depreciation'] #essentially "adjusted EBIT" as it doesn't include other impacts, proceeds from disposals, write-offs of residual tax value, etc
# df_gfm['Total Capitalized'] = df_gfm['Capitalized Items - Item 1'] + df_gfm['Capitalized Items - Item 2'] + df_gfm['Capitalized Items - Item 3'] +df_gfm['Capitalized Items - Item 4']
df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + df_gfm['Write-off of Residual Tax Value'] + df_gfm['Other Income, Expenses, Except Items'] + df_gfm['Additional Impacts on P&L']
df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + df_gfm['Other Net Current Assets'] #put in as positive numbers, different than excel
df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - df_gfm['Total Net Current Assets'].shift(1)
df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + df_gfm['Tax depreciation'] + df_gfm['Additional Non-cash Effects'] - df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + df_gfm['Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']

# print('COGS: \n]', df_gfm['Standard COGS'])
# print('Gross Sales: \n', df_gfm['Gross Sales'])
# print('Price \n', df_gfm)
# print('Net Sales \n', df_gfm['Net Sales'])
# print('FCF \n', df_gfm['FCF'])

##----------------------------------------------------------------------
## PERFORM FINANCIAL CALCULATIONS
#TODO delete the 4 hard coded 2030 numbers, just there so it will match the excel

# IRR
irr = np.irr(df_gfm.FCF.loc[parameters['present_year']:2030])

# NPV
x = 0
pv = []
for i in df_gfm.FCF.loc[parameters['present_year']:2030]:
    pv.append(i/(1+parameters['discount_rate'])**x)
    x += 1
npv = sum(pv)

# Discounted Payback Period
df_gfm['FCF PV'] = 0
df_gfm['FCF PV'].loc[parameters['present_year']:] = pv
df_gfm['Cummulative Discounted FCF'] = np.cumsum(df_gfm["FCF PV"].loc[parameters['present_year']:])
df_gfm['Cummulative Discounted FCF'] = df_gfm['Cummulative Discounted FCF'].fillna(0)
idx = df_gfm[df_gfm['Cummulative Discounted FCF'] <= 0].index.max() #last full year for payback calc
if idx == parameters['last_forecasted_year']:
    discounted_payback_period = np.nan
else:
    discounted_payback_period = idx - parameters['present_year'] + 1- df_gfm['Cummulative Discounted FCF'].loc[idx]/df_gfm['FCF PV'].loc[idx+1]
if idx == parameters['last_forecasted_year']:
    discounted_payback_period = np.nan
else:
    V_weird_discount_payback_period_calc = idx - parameters['present_year'] + 3.5 - (df_gfm['Cummulative Discounted FCF'].loc[idx+1] / (df_gfm['Cummulative Discounted FCF'].loc[idx+1] - df_gfm['Cummulative Discounted FCF'].loc[idx]))

# Exit values (specificially saves value in 2023)
df_gfm['Exit Values'] = df_gfm['EBIT'] * parameters['exit_multiple']
exit_value_2021 = df_gfm['Exit Values'].loc[2023]

# MOIC in 2023
amt_invested = df_gfm['Total Capitalized'] + df_gfm['R&D'] + df_gfm['SG&A'] + df_gfm['Milestone Payments']
cum_amt_invested =np.cumsum(amt_invested)
MOIC = []
for i in range(len(df_gfm['Exit Values'])):
    if cum_amt_invested.iloc[i] == 0:
        MOIC.append(0)
    else:
        MOIC.append(-df_gfm['Exit Values'].iloc[i] / cum_amt_invested.iloc[i])
df_gfm["MOIC"] = MOIC
MOIC_2021 = df_gfm["MOIC"].loc[2023]

del x, pv, idx, amt_invested, cum_amt_invested, MOIC

print(df_gfm[['Net Sales','COGS','FCF','EBIT','Distribution','Write-offs','Profit Share']])

##----------------------------------------------------------------------
##SHOW RESULTS

parameters['npv'] = round(npv, 2)
parameters['irr'] = round(irr*100, 2)
parameters['payback'] = round(discounted_payback_period, 2)
parameters['exit_value'] = round(yearly_data.loc[2021]['Exit Values'], 2)
parameters['moic'] = round(yearly_data.loc[2021]['MOIC'], 2)

# ##----------------------------------------------------------------------
# ## PRINT RESULTS TO WINDOW
#
# open window
window = Tk()
window6 = gui.ShowResults(window, parameters)
window.mainloop()


# ##----------------------------------------------------------------------
# ## WRITE TO DB

conn = output.create_connection('C:\\sqlite\\db\\pythonsqlite.db')

# output.create_table(conn, output.model_results_ddl)
# output.create_table(conn, output.annual_forecast_ddl)

result = pd.DataFrame(columns=['brand_name', 'molecule_name', 'volume_growth_rate', 'npv'])
annual_forecast = pd.DataFrame(columns=['forecast_year', 'number_gx_competitors', 'profit_share', 'net_sales', 'cogs'])

result.append({'brand_name': 'aaa', 'molecule_name': 'xxx', 'volume_growth_rate': ''})
result.append({})

for row in result:
    output.insert_result(conn, row)

for row in annual_forecast:
    output.insert_forecast(conn, row)

conn.close()

# result1 = (101, 'WATER', 'H20', 45.6)
# result2 = (102, 'GLEEVEC', 'IMATINIB', 127.3)
# insert_result(conn, result1)
# insert_result(conn, result2)
#
# annual1 = (101, 1000, 2019, 2, .25, 190000, 45000)
# annual2 = (101, 1000, 2020, 3, .25, 250000, 65000)
# insert_forecast(conn, annual1)
# insert_forecast(conn, annual2)
#
# select_all_results(conn)
# select_all_forecasts(conn)


