#find all IMS records that match the Combined Molecule and Prod Form2
def get_equiv(IMS, parameters):
    return  IMS.loc[(IMS['Combined Molecule'].isin(parameters['combined_molecules'])) & (IMS['Prod Form2'].isin(parameters['dosage_forms']))]

def get_dosage_forms(parameters, IMS):
    try:
        if parameters['search_type'] == 'brand':
            parameters['combined_molecules'] = IMS.loc[IMS['Product Sum'] == parameters['brand_name']][
                'Combined Molecule'].unique()
            parameters['dosage_forms'] = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Prod Form2'].unique()
        elif parameters['search_type'] == 'molecule':
            parameters['combined_molecules'] = [parameters['molecule_name']]
            parameters['dosage_forms'] = IMS.loc[IMS['Combined Molecule'] ==
                                                 parameters['molecule_name']]['Prod Form2'].unique()
            parameters['brand_name'] = 'Not specified'
    except KeyError:
        print('Please select a brand or molecule to run the model.')

    return parameters

#join IMS and prospecto data
def merge_ims_prospecto(df_equivalents, prospectoRx):
    import pandas as pd
    import numpy as np

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

    # fill in blank prices with lowest price of same strength and pack quantity
    df_merged_data['WACPrice'].fillna(min(df_merged_data['WACPrice']))

    # TODO if no price match on NDC is found, use the lowest price for the same strength and package units
    #     if no record with the same strength and package units, use the lowest overall price

    # build hierarchical index on Year and NDC
    year_range = [int(i) for i in np.array(range(2016, 2031))] #TODO - use data from excel to make dataframe?
    NDCs = [int(i) for i in df_equivalents['NDC'].unique()]
    index_arrays = [year_range, NDCs]
    multiIndex = pd.MultiIndex.from_product(index_arrays, names=['year_index', 'ndc_index'])

    # create df with multiindex
    df_detail = pd.DataFrame(index=multiIndex, columns=['NDC', 'Units', 'Price', 'Sales'])
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

    return(df_merged_data, df_detail)