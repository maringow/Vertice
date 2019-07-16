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
parameters['years_discounted'] = 10
parameters['launch_delay'] = 0
parameters['cogs_variation'] = 0

df_gfm, df_detail = fincalcs.financial_calculations(parameters, df_gfm, df_detail, df_analog)

results, annual_forecast = fincalcs.valuation_calculations(parameters, df_gfm)

##----------------------------------------------------------------------
##SHOW RESULTS

parameters['npv'] = round(results[13], 2)
parameters['irr'] = round(results[14]*100, 2)
parameters['payback'] = round(results[15], 2)
parameters['exit_value'] = round(annual_forecast.loc[2021]['Exit Values'], 2)
parameters['moic'] = round(annual_forecast.loc[2021]['MOIC'], 2)

##----------------------------------------------------------------------
## PRINT RESULTS TO WINDOW
#
# open window
window = Tk()
window6 = gui.ShowResults(window, parameters)
window.mainloop()

### BEGIN LOOP --------------------------------------------------
# PRODUCE ADJUSTED SCENARIO PARAMETERS (AFTER RUNNING BASE CASE)

#creating the df that will be inserted to the SQL db
scenario_id = 0
df_result = pd.DataFrame()
df_annual_forecast = pd.DataFrame(columns = ['scenario_id','Number of Gx Players', 'Profit Share', 'Milestone Payments',
                                             'R&D', 'Net Sales', 'COGS', 'EBIT', 'FCF', 'Exit Values', 'MOIC'])

#add scenario number
results.append(scenario_id)
annual_forecast['scenario_id'] = scenario_id

#adding the results to df that will go to SQL
df_result = df_result.append([results])
df_annual_forecast = df_annual_forecast.append(annual_forecast)

# a few parameters to scan through, smaller range to save time
years_to_discount = [10]
probability_of_success = [.5,1]
launch_delay_months = [0,12]
overall_cogs_increase = [-.1,.1]
wac_price_increase = [0]
volume_growth = [0,.05]

number_of_gx_players = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                        [2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3]]

for i in years_to_discount:
    for j in probability_of_success:
        for k in launch_delay_months:
            for l in overall_cogs_increase:
                for m in wac_price_increase:
                    for n in volume_growth:
                        for o in number_of_gx_players:
                           # global scenario_id, df_results, df_annual_forecast, parameters, df_gfm, df_detail, df_analog
                            scenario_id = scenario_id + 1

                            parameters['years_discounted'] = i
                            parameters['pos'] = j
                            parameters['launch_delay'] = k
                            parameters['cogs_variation'] = l
                            parameters['wac_increase'] = m
                            parameters['volume_growth_rate'] = n
                            df_gfm['Number of Gx Players'] = o

                            x, y = fincalcs.financial_calculations(parameters, df_gfm, df_detail, df_analog)

                            v, w = fincalcs.valuation_calculations(parameters, x)

                            # add scenario number to these results
                            v.append(scenario_id)
                            w['scenario_id'] = scenario_id

                            # adding results to df that will go to SQL
                            df_result = df_result.append([v])
                            df_annual_forecast = df_annual_forecast.append(w)

                            print(scenario_id)

#making scenario_id be the first column
df_result = df_result[[19,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18]]


# RUN FINANCIAL FUNCTION AND GET BACK 1-ROW "RESULT" and 10-ROW "ANNUAL_FORECAST"
# ADD SCENARIO_ID TO BOTH
# APPEND TO OUTSIDE DFS DF_RESULT AND DF_ANNUAL FORECAST

# add scenario_id and append the result row here
# result['scenario_id'] = scenario_id
# df_result = df_result.append({'scenario_id': 123, 'brand_name': 'abc', 'molecule': 'xyz', 'channel': 'Retail',
#                               'indication': 'sdfsdfa', 'presentation': 'bbb', 'comments': 'ewhgoia ewiveowia ceowav',
#                               'vertice_filing_month': 4, 'vertice_filing_year': 2020,
#                               'vertice_launch_month': 8, 'vertice_launch_year': 2020, 'pos': .8,
#                               'base_year_volume': 324342, 'base_year_sales': 34837347, 'volume_growth_rate': .04,
#                               'wac_price_growth_rate': .02, 'per_unit_cogs': 8.10, 'npv': 5.26, 'irr': 120,
#                               'payback': 1.2}, ignore_index=True)

# add append the annual forecast row here
# annual_forecast['scenario_id'] = scenario_id
# df_annual_forecast = df_annual_forecast.append({'scenario_id': 101, 'forecast_year': 2019, 'number_gx_competitors': 2,
#                            'profit_share': .25, 'milestone_payments': 500, 'research_development_cost': 300,
#                            'net_sales': 12, 'cogs': 5, 'ebit': 7, 'fcf': 7, 'exit_value': -35, 'moic': -10},
#                           ignore_index=True)

### END OF LOOP-------------------------------------------------------
# FORMATTING THE RESULTS TO PUT INTO DB
# assign run_ids starting at 0 once loop is over
run_id = 0
df_result['run_id'] = run_id
df_annual_forecast['run_id'] = run_id
#adding column names to df
df_result.columns = ['scenario_id', 'run_id', 'brand_name', 'molecule', 'channel', 'indication', 'presentation',
                    'comments', 'vertice_filing_month', 'vertice_filing_year','vertice_launch_month',
                    'vertice_launch_year', 'pos', 'base_year_volume','base_year_sales', 'volume_growth_rate',
                    'wac_price_growth_rate', 'per_unit_cogs','npv', 'irr', 'payback']
#creating a forecast year column
df_annual_forecast['forecast_year'] = df_annual_forecast.index.values
#ordering the columns
df_annual_forecast = df_annual_forecast[['scenario_id', 'run_id', 'forecast_year', 'Number of Gx Players', 'Profit Share',
                                         'Milestone Payments','R&D','Net Sales','COGS','EBIT','FCF', 'Exit Values', 'MOIC']]


# OPEN CONNECTION TO DB
conn = output.create_connection('C:\\sqlite\\db\\pythonsqlite.db')

#create tables - only needed on first run
output.create_table(conn, output.model_results_ddl)
output.create_table(conn, output.annual_forecast_ddl)

# get max values for run_id and scenario_id
try:
    scenario_id, run_id = output.select_max_ids(conn)[0]
    print('run_id {}'.format(run_id))
    run_id += 1
    scenario_id += 1
    print('run id: {}'.format(run_id))
except:
    print('Exception occurred when reading max IDs')
    run_id = 1
    scenario_id = 1

#adding the max run_id and scenario_id to the 0-base numbers
df_result['run_id'] = df_result['run_id'] + run_id
df_annual_forecast['run_id'] = df_annual_forecast['run_id'] + run_id
df_result['scenario_id'] = df_result['scenario_id'] + scenario_id
df_annual_forecast['scenario_id'] = df_annual_forecast['scenario_id'] + scenario_id

# insert data
for index, row in df_result.iterrows():
    print(row)
    output.insert_result(conn, row)

for index, row in df_annual_forecast.iterrows():
    print(row)
    output.insert_forecast(conn, row)

output.select_all_forecasts(conn)
output.select_all_results(conn)

conn.close()
