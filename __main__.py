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
## INGEST DATA (IMS, ProspectoRx)

# ingest IMS and price data
IMS = pd.read_csv('full_extract_6.26.csv')
prospectoRx = pd.read_csv('gleevec_prospectorx.csv')

# get valid brands from IMS file
brands = sorted(IMS.loc[IMS['Brand/Generic'] == 'BRAND']['Product Sum'].unique())

#IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Combined Molecule'].unique()

parameters = {}


##----------------------------------------------------------------------
## OPEN WINDOW1 AND SAVE PARAMETERS
window = Tk()
window1 = gui.BrandSelection(window, brands)
window.mainloop()
print('saved variable: {}'.format(window1.w1_parameters['brand_name']))

parameters.update(window1.w1_parameters)
print(parameters)

##----------------------------------------------------------------------
## FIND THERAPEUTIC EQUIVALENTS

# pull records that are therapeutic equivalents of selected brand name drug
# find Combined Molecule and Prod Form 3 of selected brand name drug; store in lists in case there are multiple
parameters['combined_molecules'] = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Combined Molecule'].unique()
parameters['dosage_forms'] = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Prod Form3'].unique()

# find all IMS records that match the Combined Molecule and Prod Form 3
df_equivalents = IMS.loc[(IMS['Combined Molecule'].isin(parameters['combined_molecules'])) &
                         (IMS['Prod Form3'].isin(parameters['dosage_forms']))]
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
window2 = gui.ConfirmBrand(window, parameters)
window.mainloop()



##----------------------------------------------------------------------
## WINDOW3: OPEN EnterCOGS WINDOW AND SAVE VALUES
window = Tk()
window3 = gui.EnterCOGS(window, df_equivalents)
window.mainloop()

parameters['api_units'] = window3.COGS['units']
parameters['api_cost_per_unit'] = pd.to_numeric(window3.COGS['cost_per_unit'])
df_merged_data['API_units'] = 0

# map COGS into df_merged_data and df_detail
for key, value in window3.COGS['units_per_pack'].items():
    df_merged_data['API_units'].loc[df_merged_data['Pack'] == key] = pd.to_numeric(value)
df_merged_data['API_cost'] = df_merged_data['API_units'] * parameters['api_cost_per_unit']
df_detail = pd.merge(df_detail.reset_index(), df_merged_data[['NDC', 'API_cost']], on='NDC', how='left').set_index(['year_index', 'ndc_index'])
df_detail['COGS'] = df_detail['Units'] * df_detail['API_cost']
df_detail.drop(columns=['API_cost'])
print(df_detail)

##----------------------------------------------------------------------
## WINDOW4: OPEN EnterFilepath WINDOW AND SAVE VALUES
window = Tk()
window4 = gui.EnterFilepath(window, parameters)
window.mainloop()

parameters.update(window4.w3_parameters)

##----------------------------------------------------------------------
## Read Excel file

# read user input Excel file
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
                   'volume_growth_rate':
                    })  # more to be added

print(parameters)