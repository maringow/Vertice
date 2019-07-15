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
import fincalcs
import readinputs
import mergedatasets
# import warnings
# warnings.filterwarnings('ignore')


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

print(parameters['volume_growth_rate'])
print(df_detail['Units'])


#Financial Calcs
df_gfm, df_detail = fincalcs.financial_calculations(parameters, df_gfm, df_detail, df_analog)

irr, npv, discounted_payback_period, mkt_size, mkt_vol, yearly_data = fincalcs.valuation_calculations(parameters, df_gfm)

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

output.create_table(conn, output.model_results_ddl)
output.create_table(conn, output.annual_forecast_ddl)

result = pd.DataFrame(columns=['brand_name', 'molecule_name', 'volume_growth_rate', 'npv'])
annual_forecast = pd.DataFrame(columns=['forecast_year', 'number_gx_competitors', 'profit_share', 'net_sales', 'cogs'])

result.append({'brand_name': 'aaa', 'molecule': 'xxx', 'volume_growth_rate': .05, 'npv': 5.26})
result.append({'brand_name': 'bbb', 'molecule': 'yyy', 'volume_growth_rate': -.03, 'npv': -1.2})

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


