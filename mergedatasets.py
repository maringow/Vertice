import math
import pandas as pd
import numpy as np


def get_dosage_forms(IMS, parameters):
    """
    Get the combined molecule name, based on selected molecule or brand.
    Get the list of dosage forms for that combined molecule.
    Return parameter dictionary with dosage form appended.
    """
    try:
        if parameters['search_type'] == 'brand':
            parameters['combined_molecules'] = IMS.loc[IMS['Product Sum'] ==
                                                       parameters['brand_name']]['Combined Molecule'].unique()
            parameters['dosage_forms'] = IMS.loc[IMS['Product Sum'] ==
                                                 parameters['brand_name']]['Vertice Dosage Form'].unique()
            parameters['molecule_name'] = 'Not specified'
        elif parameters['search_type'] == 'molecule':
            parameters['combined_molecules'] = [parameters['molecule_name']]
            parameters['dosage_forms'] = IMS.loc[IMS['Combined Molecule'] ==
                                                 parameters['molecule_name']]['Vertice Dosage Form'].unique()
            parameters['brand_name'] = 'Not specified'
    except KeyError:
        print('Please select a brand or molecule to run the model.')

    return parameters


def get_equiv(IMS, parameters):
    """
    Find all IMS records that match the Combined Molecule and Vertice dosage form.
    """
    return IMS.loc[(IMS['Combined Molecule'].isin(parameters['combined_molecules'])) &
                   (IMS['Vertice Dosage Form'].isin(parameters['dosage_forms']))]


def get_api_cost(df_detail, df_merged_data, parameters):
    """
    Calculates API cost per unit and merges into df_detail based on user inputs in the API COGS screen (window6).
    :param df_detail: Molecule- and year-level data used to calculate and store financial forecast
    :param df_merged_data: Merged volume and price data for set of "equivalent" NDCs
    :param parameters: Dictionary of variables used in model
    :return:
        df_merged_data: Updated with API cost
        df_detail: Updated with API cost to feed into COGS
    """
    if parameters['standard_cogs_entry'] != '':
        df_merged_data['API_cost'] = pd.to_numeric(parameters['standard_cogs_entry'])
    else:
        for key, value in parameters['api_units_per_pack'].items():
            df_merged_data['API_units'].loc[df_merged_data['Pack'] == key] = pd.to_numeric(value)
        df_merged_data['API_cost'] = df_merged_data['API_units'] * parameters['api_cost_per_unit']
    df_detail = pd.merge(df_detail.reset_index(), df_merged_data[['NDC', 'API_cost']],
                         on='NDC', how='left').set_index(['year_index', 'ndc_index'])

    return df_merged_data, df_detail


def merge_ims_prospecto(df_equivalents, prospectoRx):
    """
    Join IMS and prospecto data.
    Creates molecule- and year-level dataframe.

    """
    def strip_non_numeric(df_column):
        df_column = df_column.str.replace('[^0-9]', '')
        df_column = pd.to_numeric(df_column)
        return df_column

    ##############################################################
    # parse NDC columns from IMS and ProspectoRx
    ##############################################################
    df_equivalents['NDC'] = strip_non_numeric(df_equivalents['NDC'].str.split('\s', expand=True)[0])
    df_equivalents['NDC'].fillna(999, inplace=True)  # e.g. if NDC is "NDC NOT AVAILABLE"
    df_equivalents['NDC'] = df_equivalents['NDC'].astype(np.int64)
    prospectoRx['WACPrice'] = round(prospectoRx['Package Size'] * prospectoRx['WAC (Unit)'], 2)
    prospectoRx.rename(index=str, columns={'Drug Identifier': 'NDC'}, inplace=True)
    # prospectoRx['NDC'] = strip_non_numeric(prospectoRx['NDC'])

    ##############################################################
    # join price and therapeutic equivalents on NDC
    ##############################################################
    df_merged_data = df_equivalents.merge(prospectoRx[['NDC', 'WACPrice']], how='left', on='NDC')

    ##############################################################
    # fill blank prices with lowest WAC price
    # try by matching pack first, then strength&quantity, otherwise overall min
    ##############################################################
    for i in df_merged_data.index:
        if math.isnan(df_merged_data['WACPrice'].iloc[i]):
            try:
                df_merged_data['WACPrice'].iloc[i] = min(
                    df_merged_data[df_merged_data['Pack'] ==
                                   df_merged_data['Pack'].iloc[i]]['WACPrice'].dropna())
            except:
                try:
                    # x = df_merged_data[df_merged_data['Strength'] == df_merged_data['Strength'].iloc[i]][['WACPrice', 'Pack Quantity']].dropna()  # find same strengths e.g. 100MG
                    # x["WACPrice_OneUnit_ByStrength"] = x['WACPrice'] / x['Pack Quantity']  # find unit price... price / quantity
                    # df_merged_data['WACPrice'].iloc[i] = min(x["WACPrice_OneUnit_ByStrength"]) * df_merged_data['Pack Quantity'].iloc[i]  # get price.. unit price * units
                    df_merged_data['WACPrice'].iloc[i] = min(df_merged_data
                                                             [(df_merged_data['Strength'] ==
                                                               df_merged_data['Strength'].iloc[i]) &
                                                              (df_merged_data['Pack Quantity'] ==
                                                               df_merged_data['Pack Quantity'].iloc[i])]['WACPrice'].dropna())
                except:
                    try:
                        df_merged_data['WACPrice'].iloc[i] = min(df_merged_data['WACPrice'].dropna())
                    except:
                        df_merged_data['WACPrice'].iloc[i] = 0

    ##############################################################
    # build hierarchical index on Year and NDC
    ##############################################################
    year_range = [int(i) for i in np.array(range(2016, 2035))]
    NDCs = [int(i) for i in df_equivalents['NDC'].unique()]
    index_arrays = [year_range, NDCs]
    multiIndex = pd.MultiIndex.from_product(index_arrays, names=['year_index', 'ndc_index'])

    ##############################################################
    # create df with multiindex
    ##############################################################
    df_detail = pd.DataFrame(index=multiIndex, columns=['NDC', 'Units', 'Price', 'Sales'])
    df_detail['NDC'] = df_detail.index.get_level_values('ndc_index')

    ##############################################################
    # create list of Units columns from IMS data
    ##############################################################
    columns = [[2016, '2016_Units'], [2017, '2017_Units'], [2018, '2018_Units'],
               [2019, '2019_Units'], [2020, '2020_Units'], [2021, '2021_Units'],
               [2022, '2022_Units']]

    ##############################################################
    # map units and price into df_detail
    ##############################################################
    for year in columns:
        if year[1] in df_merged_data.columns:
            df_merged_data_agg = df_merged_data[
                ['NDC', year[1]]]  # using df_merged_data_agg to sum units across duplicate NDCs
            df_merged_data_agg[year[1]] = pd.to_numeric(df_merged_data_agg[year[1]].str.replace(',', ''))
            df_merged_data_agg[year[1]] = df_merged_data_agg.groupby('NDC')[year[1]].transform('sum')
            df_detail['Units'].loc[year[0]][df_merged_data_agg['NDC']] = df_merged_data_agg[year[1]]
            df_detail['Price'].loc[year[0]][df_merged_data['NDC']] = df_merged_data['WACPrice']
        else:
            break
    df_detail['Units'] = df_detail['Units'].fillna(0)
    df_detail['Sales'] = df_detail['Units'] * df_detail['Price']

    return (df_merged_data, df_detail)
