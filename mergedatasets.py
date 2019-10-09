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


def strip_non_numeric(df_column):
    df_column = df_column.str.replace('[^0-9]', '')
    df_column = pd.to_numeric(df_column)

    return df_column


def fill_missing_prices(df_merged_data):
    """
    For NDCs where no price is found in the ProspectoRx data, attempts to intelligently fill prices by looking
    for the lowest price among NDCs with the same pack size. If none are found, takes lowest WAC price overall.
    :param df_merged_data: Dataframe containing IMS and ProspectoRx data for all NDCs identified as equivalents
    to the brand/molecule selected by user
    :return: df_merged_data updated with prices
    """
    for i in df_merged_data.index:
        if math.isnan(df_merged_data['WACPrice'].iloc[i]):
            try:
                df_merged_data['WACPrice'].iloc[i] = min(
                    df_merged_data[df_merged_data['Pack'] ==
                                   df_merged_data['Pack'].iloc[i]]['WACPrice'].dropna())
            except:
                try:
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

    return df_merged_data


def populate_df_detail(df_equivalents, df_merged_data):
    """
    Builds dataframe of years and NDCs (df_detail) and populates with data from df_merged_data
    :param df_equivalents: Dataframe of IMS data for identified "equivalent" NDCs
    :param df_merged_data: Dataframe of IMS and ProspectoRx data for equivalent NDCs
    :return: df_detail, dataframe containing year and NDC-level data used in financial calculations
    """
    # build hierarchical index on Year and NDC
    year_range = [int(i) for i in np.array(range(2016, 2035))]
    NDCs = [int(i) for i in df_equivalents['NDC'].unique()]
    index_arrays = [year_range, NDCs]
    multiIndex = pd.MultiIndex.from_product(index_arrays, names=['year_index', 'ndc_index'])

    # create df_detail with multiindex
    df_detail = pd.DataFrame(index=multiIndex, columns=['NDC', 'Units', 'Price', 'Sales'])
    df_detail['NDC'] = df_detail.index.get_level_values('ndc_index')

    # create list of Units columns from IMS data
    columns = [[2016, '2016_Units'], [2017, '2017_Units'], [2018, '2018_Units'],
               [2019, '2019_Units'], [2020, '2020_Units'], [2021, '2021_Units'],
               [2022, '2022_Units']]

    # map units and price into df_detail
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

    return df_detail


def merge_ims_prospecto(df_equivalents, prospectoRx):
    """
    Starting with IMS data in df_equivalents, looks up prices from ProspectoRx and stores in df_merged_data and
    df_detail. If no price is found, function attempts to find the lowest price for the same pack size, otherwise
    takes lowest price on the market overall.
    :param df_equivalents: IMS data for NDCs that have been identified as equivalents to the selected brand or molecule
    :param prospectoRx: Raw price data by NDC
    :return:
        df_merged_data: Dataframe containing both price and volume data for all identified equivalent NDCs
        df_detail: Dataframe indexed on year and NDC, used to hold numbers feeding financial model
    """

    # parse NDC columns from IMS and ProspectoRx
    df_equivalents['NDC'] = strip_non_numeric(df_equivalents['NDC'].str.split('\s', expand=True)[0])
    df_equivalents['NDC'].fillna(999, inplace=True)  # e.g. if NDC is "NDC NOT AVAILABLE"
    df_equivalents['NDC'] = df_equivalents['NDC'].astype(np.int64)
    prospectoRx['WACPrice'] = round(prospectoRx['Package Size'] * prospectoRx['WAC (Unit)'], 2)
    prospectoRx.rename(index=str, columns={'Drug Identifier': 'NDC'}, inplace=True)

    # join price and therapeutic equivalents on NDC
    df_merged_data = df_equivalents.merge(prospectoRx[['NDC', 'WACPrice']], how='left', on='NDC')

    # fill blank prices with lowest WAC price
    # try by matching pack first, then strength&quantity, otherwise overall min
    df_merged_data = fill_missing_prices(df_merged_data)
    print(df_merged_data)

    # build df_detail and map data in
    df_detail = populate_df_detail(df_equivalents, df_merged_data)

    return df_merged_data, df_detail
