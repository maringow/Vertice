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

def strip_non_numeric(df_column):
    df_column = df_column.str.replace('[^0-9]', '')
    df_column = pd.to_numeric(df_column)
    return df_column

# parse NDC columns from IMS and ProspectoRx
df_equivalents['NDC'] = strip_non_numeric(df_equivalents['NDC'].str.split('\s', expand=True)[0])
df_equivalents['NDC'].fillna(999, inplace=True)  ## if NDC is "NDC NOT AVAILABLE" or other invalid value, fill with 999
prospectoRx.rename(index=str, columns={'PackageIdentifier': 'NDC'}, inplace=True)
prospectoRx['NDC'] = strip_non_numeric(prospectoRx['NDC'])

# join price and therapeutic equivalents on NDC
df_merged_data = df_equivalents.merge(prospectoRx[['NDC', 'WACPrice']], how='left', on='NDC')
print(df_merged_data)

# fill in blank prices with lowest price of same strength and pack quantity
df_merged_data['WACPrice'].fillna(min(df_merged_data['WACPrice']))

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

# TODO try to use strip_non_numeric function here to consolidate
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

# TODO maybe add volume and price numbers to this - could help user forecast growth and confirm code is working
# TODO make count_competitors work past 2019

def get_growth_rate(df):
    units_by_year = df['Units'].sum(level='year_index')
    growth_rate = round(((units_by_year.loc[2018] / units_by_year.loc[2016]) ** (1/2) - 1), 2)
    return growth_rate


# set parameters to display in confirmation window
parameters['count_competitors'] = len(df_equivalents.loc[pd.isnull(df_equivalents['2018_Units']) == False]
                                      ['Manufacturer'].unique())
parameters['historical_growth_rate'] = get_growth_rate(df_detail)
print(parameters['historical_growth_rate'])

# open window
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
window5 = gui.EnterFilepath(window)
window.mainloop()

parameters.update(window5.parameters)

##----------------------------------------------------------------------
## READ EXCEL

# Read user input Excel file
# TODO parse filename - correct backslashes and add .xlsx if not already there

wb = xl.load_workbook(filename=parameters['excel_filepath'], read_only=True, data_only=True) #data_only so it doesn't return us the formulas
sheet = wb['Input']

# Assign single-value variables from Excel cells into parameters dictionary
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
                   #'chargebacks': sheet['B24'].value,
                   #'other_gtn': sheet['B25'].value,
                   'gtn_%': sheet['B26'].value,
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
                            'writeoffs': sheet['B39'].value},
                   'present_year': sheet['B55'].value,
                   'last_forecasted_year': sheet['M55'].value
                    })

# Set up df_gfm data frame
df_gfm = pd.DataFrame()
df_gfm['Year'] = list(range(2015, parameters['last_forecasted_year']+1, 1))
df_gfm = df_gfm.set_index('Year')

# Add excel yearly data
def pull_yearly_data(row_number): #row you want data from
    x = [0] * (parameters['present_year'] - 2015) #zeros for years not in 'model input' excel sheet
    for i in range(2, 14):
        x.append(sheet.cell(row = row_number, column = i).value)
    return(x)

df_gfm['Gx Penetration'] = pull_yearly_data(56)
df_gfm['Number of Gx Players'] = pull_yearly_data(57)
df_gfm['Vertice Gx Market Share'] = pull_yearly_data(58)
df_gfm['Price Discount of Current Gx Net Price'] = pull_yearly_data(59)
df_gfm['Profit Share %'] = pull_yearly_data(60)
df_gfm['Milestone Payments'] =  pull_yearly_data(61)
df_gfm['SG&A'] = pull_yearly_data(62)
# df_gfm['R&D Project Expense'] = pull_yearly_data(63)
# df_gfm['Incremental R&D Headcount Expense'] = pull_yearly_data(64)
# df_gfm['R&D infrastructure cost'] =  pull_yearly_data(65)
df_gfm['R&D'] =  pull_yearly_data(66)
# df_gfm['Capitalized Items - Item 1'] = pull_yearly_data(71)
# df_gfm['Capitalized Items - Item 2'] = pull_yearly_data(72)
# df_gfm['Capitalized Items - Item 3'] = pull_yearly_data(73)
# df_gfm['Capitalized Items - Item 4'] = pull_yearly_data(74)
df_gfm['Total Capitalized'] = pull_yearly_data(75)
df_gfm['Tax depreciation'] = pull_yearly_data(76)
df_gfm['Additional Impacts on P&L'] = pull_yearly_data(84)
df_gfm['Net proceeds from Disposals'] = pull_yearly_data(85)
df_gfm['Write-off of Residual Tax Value'] = pull_yearly_data(86)
df_gfm['Other Income, Expenses, Except Items'] = pull_yearly_data(87)
df_gfm['Additional Non-cash Effects'] =  pull_yearly_data(88)
df_gfm['Other Net Current Assets'] = pull_yearly_data(89)
df_gfm['Capital Avoidance'] = pull_yearly_data(90)
df_gfm = df_gfm.fillna(0) #if there is no data entered in the excel file, it gives NaNs, this converts them to 0s

# Adding analog data
sheet = wb['Analog']
def pull_analog_data(row_number): #row you want data from
    x =[]
    for i in range(2, 12):
        x.append(sheet.cell(row = row_number, column = i).value)
    return(x)

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
if parameters['brand_status'] == 'Branded':
    col_name = [parameters['channel'] + ' Net Price Pct BWAC']
    df_gfm['Vertice Price as % of WAC'] = df_analog.loc[df_gfm['Number of Gx Players'], col_name].values
else:
    df_gfm['Vertice Price as % of WAC'] = (1 - parameters['gtn_%']) * (1 - df_gfm['Price Discount of Current Gx Net Price'])

# Dummy data for below financial calcs
# TODO link df_detail information into these columns once calculated
df_gfm['Net Sales'] =  np.arange(3,6.2,.2)
df_gfm['Standard COGS'] =  -np.arange(.2,1.8,.1)

# Financial statement calculations
df_gfm['Gross Sales'] =  df_gfm['Net Sales'] / (1-parameters['gtn_%'])
df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
df_gfm['Profit Share'] = -(df_gfm['Net Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm['Profit Share %']
df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
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

##----------------------------------------------------------------------
## PERFORM FINANCIAL CALCULATIONS

# IRR
irr = np.irr(df_gfm.FCF.loc[parameters['present_year']:])

# NPV
x = 0
pv = []
for i in df_gfm.FCF.loc[parameters['present_year']:]:
    pv.append(i/(1+parameters['discount_rate'])**x)
    x += 1
npv = sum(pv)

# Discounted Payback Period
df_gfm['FCF PV'] = 0
df_gfm['FCF PV'].loc[parameters['present_year']:] = pv
df_gfm['Cumulative Discounted FCF'] = np.cumsum(df_gfm["FCF PV"].loc[parameters['present_year']:])
df_gfm['Cumulative Discounted FCF'] = df_gfm['Cumulative Discounted FCF'].fillna(0)
idx = df_gfm[df_gfm['Cumulative Discounted FCF'] <= 0].index.max() #last full year for payback calc
discounted_payback_period = idx - parameters['present_year'] + 1- df_gfm['Cumulative Discounted FCF'].loc[idx]/df_gfm['FCF PV'].loc[idx+1]
V_weird_discount_payback_period_calc = idx - parameters['present_year'] + 3.5 - (df_gfm['Cumulative Discounted FCF'].loc[idx+1] / (df_gfm['Cumulative Discounted FCF'].loc[idx+1] - df_gfm['Cumulative Discounted FCF'].loc[idx]))

# Exit values (specifically saves value in 2021)
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


#not actual output, just to compare results with excel model
print("NPV:        ", round(npv,4))
print("IRR:        ", round(irr,4))
print("Payback:    ", round(discounted_payback_period,4))
print("V's Payback ", round(V_weird_discount_payback_period_calc,4))
print("Exit Value: ", round(exit_value_2021,4))
print("MOIC:       ", round(MOIC_2021,4))


# import sqlite3
# from sqlite3 import Error
#
#
# def create_connection(db_file):
#     # create a database connection to a SQLite database
#     try:
#         conn = sqlite3.connect(db_file)
#         return conn
#     except Error as e:
#         print(e)
#
#     return None
#
#
# def create_table(conn, create_table_sql):
#     try:
#         c = conn.cursor()
#         c.execute(create_table_sql)
#     except Error as e:
#         print(e)
#
#
# def insert_result(conn, results):
#     sql = """INSERT INTO model_results(run_id, brand_name, molecule, NPV)
#             VALUES(?,?,?,?)"""
#     cur = conn.cursor()
#     cur.execute(sql, results)
#     return cur.lastrowid
#
#
# def select_all_results(conn):
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM model_results")
#     rows = cur.fetchall()
#
#     for row in rows:
#         print(row)
#
#
# conn = create_connection('C:\\sqlite\\db\\pythonsqlite.db')
#
# create_table_model_results = """CREATE TABLE IF NOT EXISTS model_results (
#                         id integer PRIMARY KEY,
#                         run_id integer NOT NULL,
#                         brand_name text,
#                         molecule text NOT NULL,
#                         NPV real
#                         ); """
# #create_table(conn, create_table_model_results)
#
# result1 = (101, 'WATER', 'H20', 45.6)
# result2 = (102, 'GLEEVEC', 'IMATINIB', 127.3)
# insert_result(conn, result1)
#
# insert_result(conn, result2)
#
# select_all_results(conn)
#
# conn.close()

