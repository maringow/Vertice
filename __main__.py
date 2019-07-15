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
import fincalcs
import readinputs


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
year_range = [int(i) for i in np.array(range(2016, 2031))]
#TODO - use data from excel to make dataframe?
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
df_detail['COGS'] = df_detail['Units'] * df_detail['API_cost']
#df_detail.drop(columns=['API_cost'])
print(df_detail)

##----------------------------------------------------------------------
## READ EXCEL

# Read user input Excel file
parameters, df_gfm, df_analog = readinputs.read_model_inputs(parameters)

#Financial Calcs (fincalcs.py)
irr, npv, discounted_payback_period, mkt_size, mkt_vol, yearly_data = fincalcs.financial_calculations(parameters, df_gfm, df_detail, df_analog)

##----------------------------------------------------------------------
##SHOW RESULTS

parameters['npv'] = round(npv, 2)
parameters['irr'] = round(irr*100, 2)
parameters['payback'] = round(discounted_payback_period, 2)
parameters['exit_value'] = round(yearly_data.loc[2021]['Exit Values'], 2)
parameters['moic'] = round(yearly_data.loc[2021]['MOIC'], 2)

# ##----------------------------------------------------------------------
# ## WRITE TO DB
#
# open window
window = Tk()
window6 = gui.ShowResults(window, parameters)
window.mainloop()


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

