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
import sqlite3
from sqlite3 import Error
import gui
import fincalcs
import readinputs
import mergedatasets
import output
import time
from sklearn.model_selection import ParameterGrid
import sys
# import warnings
# warnings.filterwarnings('ignore')


##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)

# ingest IMS and price data
IMS = pd.read_csv('full_extract_6.26.csv')
prospectoRx = pd.read_csv('prospecto_all_one_year_20190708.csv')

# get valid brands from IMS file
# TODO remove NaNs from these lists
brands = sorted(IMS.loc[IMS['Brand/Generic'] == 'BRAND']['Product Sum'].unique())  #TODO what about BRANDED GENERIC?
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

parameters = mergedatasets.get_dosage_forms(parameters, IMS)
# print(parameters['dosage_forms'])


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
# df_equivalents =
parameters['count_eqs'] = len(df_equivalents)

df_merged_data, df_detail = mergedatasets.merge_ims_prospecto(df_equivalents, prospectoRx)
#df_detail = pd.merge(df_detail.reset_index(), df_merged_data[['NDC']], on='NDC', how='left').set_index(['year_index', 'ndc_index'])

# turn arrays into strings now that we are done using them (SQLite does not support arrays)
parameters['combined_molecules'] = '; '.join(parameters['combined_molecules'])
parameters['dosage_forms'] = '; '.join(parameters['dosage_forms'])

##----------------------------------------------------------------------
## WINDOW2: OPEN ConfirmBrand WINDOW AND SAVE

# set parameters to display in confirmation window
parameters['count_competitors'] = len(df_equivalents.loc[pd.isnull(df_equivalents['2018_Units']) == False]
                                      ['Manufacturer'].unique())  #TODO - years - will need to update when we have new annual data
parameters['historical_growth_rate'] = fincalcs.get_growth_rate(df_detail)

# open window
window = Tk()
window3 = gui.ConfirmBrand(window, parameters, df_detail)
window.mainloop()


##----------------------------------------------------------------------
## WINDOW2: OPEN SelectNDCs WINDOW AND SAVE

# open window
window=Tk()
window8 = gui.SelectNDCs(window, df_merged_data)
window.mainloop()

parameters['selected_NDCs'] = window8.selected_ndcs
print('Before drop: {}'.format(df_equivalents['NDC']))
df_detail = df_detail[df_detail['NDC'].isin(parameters['selected_NDCs'])]
df_merged_data = df_merged_data[df_merged_data['NDC'].isin(parameters['selected_NDCs'])]
df_equivalents = df_equivalents[df_equivalents['NDC'].isin(parameters['selected_NDCs'])]
print('After drop: {}'.format(df_equivalents['NDC']))
parameters['selected_NDCs'] = str(parameters['selected_NDCs'])  #.replace(['[', ']'], '')

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

parameters['profit_margin_override'] = window4.COGS['gm_override']
parameters['api_units'] = window4.COGS['units']
parameters['api_cost_per_unit'] = pd.to_numeric(window4.COGS['cost_per_unit'])
parameters['standard_cogs_entry'] = window4.COGS['standard_cogs_entry']
df_merged_data['API_units'] = 0

# map COGS into df_merged_data and df_detail
if parameters['standard_cogs_entry'] != '':
    df_merged_data['API_cost'] = pd.to_numeric(parameters['standard_cogs_entry'])
else:
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
parameters['years_discounted'] = 10
parameters['launch_delay'] = 0
parameters['cogs_variation'] = 0
parameters['gx_players_adj'] = 0

df_gfm, df_detail = fincalcs.financial_calculations(parameters, df_gfm, df_detail, df_analog)

results, annual_forecast = fincalcs.valuation_calculations(parameters, df_gfm)

print('DEBUG', annual_forecast)

print(annual_forecast[['Net Sales','COGS','EBIT','FCF']])

##----------------------------------------------------------------------
##SHOW RESULTS

parameters['npv'] = round(results['npv'], 2)
parameters['irr'] = round(results['irr']*100, 1)
parameters['payback'] = round(results['discounted_payback_period'], 2)
parameters['exit_value'] = round(annual_forecast.loc[2021]['Exit Values'], 2)
parameters['moic'] = round(annual_forecast.loc[2021]['MOIC'], 1)

##----------------------------------------------------------------------
## PRINT RESULTS TO WINDOW

#If user does not opt to do parameter scan and save output:
parameters['scan_and_save'] = 'No'
if parameters['scan_and_save'] == 'No':
    window = Tk()
    window7 = gui.ShowDetailedResults(window, parameters, df_gfm)
    window.mainloop()
    sys.exit()

# open window
window = Tk()
window6 = gui.ShowResults(window, parameters)
window.mainloop()

### BEGIN LOOP --------------------------------------------------
# PRODUCE ADJUSTED SCENARIO PARAMETERS (AFTER RUNNING BASE CASE)

#add scenario number
scenario_id = 0
results['scenario_id'] = scenario_id
annual_forecast['scenario_id'] = scenario_id

#creating the df that will be inserted to the SQL db
# df_result = pd.DataFrame.from_dict(data=results, orient='index')
# df_result = df_result.transpose()
# df_annual_forecast = pd.DataFrame()
# print('results: {}'.format(results))
# df_annual_forecast = df_annual_forecast.append(annual_forecast)
#
# t0 = time.time()
# # Parameters to scan
# years_to_discount = [5,10]
# probability_of_success = [.75,1]
# launch_delay_years = [0,1]
# overall_cogs_increase = [-.3,0,.3]
# volume_growth = [parameters['historical_growth_rate']-.05,parameters['historical_growth_rate'],parameters['historical_growth_rate']+.05]
# gx_players_adj = [-2, -1, 0, 1, 2]
# base_gx_players = df_gfm['Number of Gx Players']
#
# for i in years_to_discount:
#     for j in probability_of_success:
#         for k in launch_delay_years:
#             for l in overall_cogs_increase:
#                 for m in volume_growth:
#                     for n in gx_players_adj:
#                        # global scenario_id, df_results, df_annual_forecast, parameters, df_gfm, df_detail, df_analog
#                         scenario_id = scenario_id + 1
#
#                         parameters['years_discounted'] = i
#                         parameters['pos'] = j
#                         parameters['launch_delay'] = k
#                         parameters['cogs_variation'] = l
#                         parameters['volume_growth_rate'] = m
#                         parameters['gx_players_adj'] = n
#
#                         df_gfm['Number of Gx Players'] = base_gx_players + n
#                         fincalcstart = time.time()
#                         x, y = fincalcs.forloop_financial_calculations(parameters, df_gfm, df_detail, df_analog)
#                         valcalcstart = time.time()
#                         v, w = fincalcs.valuation_calculations(parameters, x)
#                         calcend = time.time()
#                         # add scenario number to these results
#                         v['scenario_id'] = scenario_id
#                         w['scenario_id'] = scenario_id
#
#                         # adding results to df that will go to SQL
#                         df_result = df_result.append(pd.Series(v, index=df_result.columns), ignore_index=True)
#
#                         df_annual_forecast = df_annual_forecast.append(w)
#
#                         print(scenario_id)
#                         print('Time taken to run financial_calculations: {} seconds'.format(round(valcalcstart-fincalcstart,4)))
#                         print('Time taken to run valuation_calculations: {} seconds'.format(round(calcend-valcalcstart,4)))
# t1 = time.time()
# total = t1-t0
# print('Time taken to run parameter scan: {} seconds'.format(round(total,1)))

#                         print(scenario_id)
#                         print('Time taken to run financial_calculations: {} seconds'.format(round(valcalcstart-fincalcstart,4)))
#                         print('Time taken to run valuation_calculations: {} seconds'.format(round(calcend-valcalcstart,4)))
# t1 = time.time()
# total = t1-t0
# print(total)
# print(np.std(timefincalc), np.mean(timefincalc))
# print(np.std(timevalcalc), np.mean(timevalcalc))

df_result = pd.DataFrame.from_dict(data=results, orient='index')
df_result = df_result.transpose()
df_annual_forecast = pd.DataFrame()
print('results: {}'.format(results))
df_annual_forecast = df_annual_forecast.append(annual_forecast)
#

t0 = time.time()

base_gx_players = df_gfm['Number of Gx Players']
base_launch_year = parameters['vertice_launch_year']

param_grid = {'years_to_discount': [5,10],
              'probability_of_success': [.75,1],
              'launch_delay_years': [0,1],
              'overall_cogs_increase': [-.3,0,.3],
              'volume_growth': [parameters['volume_growth_rate']-.05,parameters['volume_growth_rate'],parameters['volume_growth_rate']+.05],
              'gx_players_adj': [-2,-1,0,1,2]}

param_mat = pd.DataFrame(ParameterGrid(param_grid))

def parameterscan(years_to_discount, probability_of_success, launch_delay_years, overall_cogs_increase, volume_growth, gx_players_adj, parameters, df_gfm, df_detail, df_analog):
    parameters['years_discounted'] = years_to_discount
    parameters['pos'] = probability_of_success
    parameters['vertice_launch_year'] = base_launch_year + launch_delay_years
    parameters['cogs_variation'] = overall_cogs_increase
    parameters['volume_growth_rate'] = volume_growth
    parameters['gx_players_adj'] = gx_players_adj
    df_gfm['Number of Gx Players'] = base_gx_players + gx_players_adj
    x, y = fincalcs.forloop_financial_calculations(parameters, df_gfm, df_detail, df_analog)
    return fincalcs.valuation_calculations(parameters, x)

x = param_mat.apply(lambda row: parameterscan(row['years_to_discount'], row['probability_of_success'],
                                                 row['launch_delay_years'], row['overall_cogs_increase'],
                                                 row['volume_growth'], row['gx_players_adj'],
                                                 parameters, df_gfm, df_detail, df_analog), axis=1, result_type='expand')
for i in x[0]:
    df_result = df_result.append(pd.DataFrame.from_dict(data=i, orient='index').transpose())
s = df_result['scenario_id']
df_result['is_base_case'] = np.where(s==0, 'Y', 'N')

df_result.scenario_id = np.arange(0, len(df_result.scenario_id))
for i in x[1]:
    scenario_id = scenario_id + 1
    i['scenario_id']=scenario_id
    df_annual_forecast = df_annual_forecast.append(i)


# t1 = time.time()
# total = t1-t0
# print('Time taken to run parameter scan: {} seconds'.format(round(total,1)))

### FORMATTING THE RESULTS TO PUT INTO DB ----------------------------

# assign run_ids starting at 0 once loop is over
run_id = 0
df_result['run_id'] = run_id
df_annual_forecast['run_id'] = run_id

df_annual_forecast.columns = ['Number of Gx Players', 'Profit Share', 'Milestone Payments', 'R&D', 'Vertice Price as % of WAC',
                             'Net Sales', 'COGS', 'EBIT', 'FCF', 'Exit Values', 'MOIC', 'scenario_id', 'run_id']

# creating a forecast year column
df_annual_forecast['forecast_year'] = df_annual_forecast.index.values

# ordering the columns
df_result = df_result[['scenario_id', 'run_id', 'run_name', 'brand_name', 'combined_molecules', 'dosage_forms',
                       'selected_NDCs', 'channel', 'indication', 'presentation', 'internal_external', 'brand_status','comments',
                       'vertice_filing_month', 'vertice_filing_year','vertice_launch_month', 'vertice_launch_year',
                       'pos', 'exit_multiple', 'discount_rate', 'tax_rate', 'base_year_volume','base_year_market_size',
                       'volume_growth_rate', 'wac_increase', 'api_cost_per_unit', 'api_cost_unit', 'profit_margin_override',
                       'standard_cogs_entry', 'years_discounted', 'cogs_variation', 'gx_players_adj', 'npv', 'irr',
                       'discounted_payback_period', 'is_base_case']]
df_annual_forecast = df_annual_forecast[['scenario_id', 'run_id', 'forecast_year', 'Number of Gx Players', 'Profit Share',
                                         'Milestone Payments','R&D','Vertice Price as % of WAC', 'Net Sales','COGS',
                                         'EBIT','FCF', 'Exit Values', 'MOIC']]


# OPEN CONNECTION TO DB
conn = output.create_connection('C:\\sqlite\\db\\pythonsqlite.db')
print('connection created')

# create tables - only needed on first run
output.create_table(conn, output.model_results_ddl)
output.create_table(conn, output.annual_forecast_ddl)

# output.add_column(conn, 'model_results', 'is_base_case', 'text')

# get max values for run_id and scenario_id
try:
    scenario_id, run_id = output.select_max_ids(conn)[0]
    print('run_id {}'.format(run_id))
    run_id = int(run_id or 0) + 1
    scenario_id = int(scenario_id or 0) + 1
except Error as e:
    print('Exception occurred when reading max IDs')
    print('Error message: {}'.format(e))
    run_id = 1
    scenario_id = 1

#adding the max run_id and scenario_id to the 0-base numbers
df_result['run_id'] = df_result['run_id'] + run_id
df_annual_forecast['run_id'] = df_annual_forecast['run_id'] + run_id
df_result['scenario_id'] = df_result['scenario_id'] + scenario_id
df_annual_forecast['scenario_id'] = df_annual_forecast['scenario_id'] + scenario_id

# insert data
for index, row in df_result.iterrows():
    # print(row)
    output.insert_result(conn, row)

for index, row in df_annual_forecast.iterrows():
    # print(row)
    output.insert_forecast(conn, row)
# print('rows written')

conn.commit()

#output.select_all_forecasts(conn)
#output.select_all_results(conn)

conn.close()
