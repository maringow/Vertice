import math
import pandas as pd
import numpy as np


def get_growth_rate(df):
    """
    Calculate the 2 year CAGR if applicable, else 1 year growth rate, otherwise 0.

    Args:
        df: The dataframe with molecule- and year-level data (i.e. df_detail).

    Returns:
        growth_rate: A float, the resulting growth rate.

    """
    units_by_year = df['Units'].sum(level='year_index')
    growth_rate1 = ((units_by_year.loc[2018] / units_by_year.loc[2016]) ** (1 / 2) - 1)
    growth_rate2 = ((units_by_year.loc[2018] / units_by_year.loc[2017]) - 1)
    if abs(growth_rate1) != np.inf:
        growth_rate = growth_rate1
    elif abs(growth_rate2) != np.inf:
        growth_rate = growth_rate2
    else:
        growth_rate = 0

    return growth_rate


def set_vertice_price_discount(df_gfm, parameters, df_analog):
    '''
    Check brand status of model run and set Vertice price as % of BWAC/GWAC accordingly
    :param df_gfm: Dataframe that holds annual financial calculations
    :param parameters: Dictionary that holds model parameters
    :param df_analog: Lookup table of model assumptions based on historical data
    :return: df_gfm, updated with model price assumptions for Vertice
    '''
    if parameters['brand_status'] == 'Brand':
        col_name = [parameters['channel'] + ' Net Price Pct BWAC']
        df_gfm['Vertice Price as % of WAC'] = df_analog.loc[df_gfm['Number of Gx Players'],
                                                            col_name].values
    else:
        df_gfm['Vertice Price as % of WAC'] = (1 - parameters['gtn_%']) * \
                                              (1 - df_gfm['Price Discount of Current Gx Net Price'])

    return df_gfm


def get_future_volume(df_detail, parameters):
    """
    Forecasts sales volumes by year and NDC based on base year volume and predicted growth rate.

    Args:
        df_detail: Molecule- and year-level data
        parameters: Dictionary of variables used in model, including predicted growth rate

    :return:
        df_detail: Updated with annual volume forecasts
    """

    df_detail['Units'] = df_detail['Units'].fillna(0)
    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Units'] = df_detail.loc[i - 1]['Units'] * \
                                    (1 + parameters['volume_growth_rate'])

    return df_detail


def store_api_cost(df_detail, df_merged_data, parameters):
    """
    Calculates API cost per unit and merges into df_detail based on user inputs in the API COGS screen (window6).
    If standard margin % option is used, does nothing.
    :param df_detail: Molecule- and year-level data used to calculate financial forecast
    :param df_merged_data: Merged volume and price data for set of "equivalent" NDCs
    :param parameters: Dictionary of variables used in model
    :return:
        df_merged_data: Updated with API cost
        df_detail: Updated with API cost to feed into COGS
    """
    if parameters['standard_cogs_entry'] != '':
        print("Storing standard API COGS for all NDCs")
        df_merged_data['API_cost'] = pd.to_numeric(parameters['standard_cogs_entry'])
    else:
        print("Storing NDC-specific API COGS based on provided API volumes and unit cost")
        for key, value in parameters['api_units_per_pack'].items():
            df_merged_data['API_units'].loc[df_merged_data['Pack'] == key] = pd.to_numeric(value)
        df_merged_data['API_cost'] = df_merged_data['API_units'] * parameters['api_cost_per_unit']
    df_detail = pd.merge(df_detail.reset_index(), df_merged_data[['NDC', 'API_cost']],
                         on='NDC', how='left').set_index(['year_index', 'ndc_index'])

    return df_merged_data, df_detail


def get_vertice_volume_forecast(df_detail, df_gfm, parameters):
    """
    Calculates Vertice volume forecast based on total forecasted market volume, Vertice launch date,
    predicted Gx penetration, predicted Vertice market share, and probability of success

    Args:
        df_detail: Molecule- and year-level data
        df_gfm: Dataframe of annual variables used in model
        parameters: Dictionary of variables used in model, including predicted growth rate

    :return:
        df_vertice_ndc_volumes: dataframe of forecasted Vertice sales volumes by NDC and year
    """

    vol_adj = []
    for i in range(2016, parameters['last_forecasted_year'] + 1):
        if i < parameters['vertice_launch_year']:
            vol_adj.append(0)
        elif i == parameters['vertice_launch_year']:
            vol_adj.append((13 - parameters['vertice_launch_month']) / 12)
        else:
            vol_adj.append(1)

    df_vertice_ndc_volumes = df_detail['Units']\
        .mul(vol_adj * df_gfm['Gx Penetration'], level=0,
             fill_value=0).mul(df_gfm['Vertice Gx Market Share'], level=0, fill_value=0)
    df_vertice_ndc_volumes = df_vertice_ndc_volumes * parameters['pos']
    df_vertice_ndc_volumes = round(df_vertice_ndc_volumes, 0)

    return df_vertice_ndc_volumes



def get_vertice_ndc_prices(df_detail, df_gfm, parameters):
    """
    Calculates forecasted Vertice prices by year and NDC based on predicted price growth (wac_increase)
    and Vertice price discount to market (Vertice Price as % of WAC)

    Args:
        df_detail: Molecule- and year-level data used to calculate financial forecast.
        df_gfm: Aggregated year-level data used to calculate and store financial forecast.
        parameters: Dictionary of variables used in model, including predicted growth rate

    :return: df_vertice_ndc_prices: Dataframe of forecasted Vertice prices by NDC and year
    """

    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Price'] = df_detail.loc[i - 1]['Price'] * (1 + parameters['wac_increase'])

    df_vertice_ndc_prices = df_detail['Price'].mul(df_gfm['Vertice Price as % of WAC'],
                                                   level=0, fill_value=0)

    return df_vertice_ndc_prices



def calculate_cogs(df_detail, df_gfm, df_vertice_ndc_volumes, parameters):
    """
    Calculates COGS based on user input to COGS window. User has 3 options and the first one that has an input is used
    1. Use a gross margin % across all NDCs
    2. Use a standard API cost across all NDCs (essentially weighted approach)
    3. Use an NDC-specific API cost for each NDC
    :param df_detail: Dataframe that contains year and NDC level data used in model
    :param df_gfm: Dataframe that holds annual financial calculations
    :param df_vertice_ndc_volumes: Dataframe of forecasted Vertice prices by NDC and year
    :param parameters: Dictionary that holds model parameters
    :return:
        df_detail: Updated with fixed COGS factors (excipients, labor, etc.)
        df_gfm: Updated with Standard COGS column
    """
    if parameters['profit_margin_override'] != '':
        print("Calculating COGS using profit margin %")
        df_gfm['Standard COGS'] = -df_gfm['Net Sales'] * \
                                  (1 - pd.to_numeric(parameters['profit_margin_override']))
    else:
        print("Calculating COGS using dollar API cost")
        # calculating std_cost_per_unit in future
        # API_cost is the API cost per NDC from the 2nd or 3rd approach in GUI window
        df_detail['std_cost_per_unit'] = df_detail['API_cost'].add(
            (parameters['cogs']['excipients'] + parameters['cogs']['direct_labor'] +
             parameters['cogs']['variable_overhead'] + parameters['cogs']['fixed_overhead'] +
             parameters['cogs']['depreciation'] + parameters['cogs']['cmo_markup']),
            level=0, fill_value=0)
        for i in range(parameters['present_year'] + 1, parameters['last_forecasted_year'] + 1):
            df_detail.loc[i]['std_cost_per_unit'] = df_detail.loc[i - 1]['std_cost_per_unit'] * \
                                                    (1 + parameters['cogs']['cost_increase'])

        df_gfm['Standard COGS'] = -(df_detail['std_cost_per_unit'] *
                                    df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    return df_detail, df_gfm


def financial_calculations(parameters, df_gfm, df_detail, df_analog):
    """
    Reverse-engineer the Excel-based GFM formulas for annual line items.
    Uses dataframes that have been created by reading in Excel data and the user's GUI inputs.

    Args:
        parameters: Dictionary of variables used in model.
        df_gfm: Aggregated year-level data used to calculate financial forecast.
        df_detail: Molecule- and year-level data used to calculate and store financial forecast.
        df_analog: Market share and net price % of BWAC lookup table.

    Returns:
        df_gfm: Aggregated year-level data.
        df_detail: Molecule- and year-level data.

    """

    # assign Vertice price as % of either BWAC or GWAC
    df_gfm = set_vertice_price_discount(df_gfm, parameters, df_analog)
    # check that Vertice price as % of WAC has been set and is > 0 over the forecast years
    # print(df_gfm['Vertice Price as % of WAC'])
    assert ((df_gfm['Vertice Price as % of WAC']).sum() > 0), "Check Vertice price as % of WAC assumptions"

    # store historical volume and size for reference
    df_gfm['Market Volume'] = df_detail['Units'].groupby(level=[0]).sum() * 1.0
    df_gfm['Market Size'] = df_detail['Sales'].groupby(level=[0]).sum() / 1000000

    # calculate projected market size
    df_detail = get_future_volume(df_detail, parameters)
    print(df_detail.loc[parameters['present_year'] + 1]['Units'])
    print(df_detail.loc[parameters['present_year']]['Units'] * (1 + parameters['volume_growth_rate']))
    # check that volume in year [base year + 1] = base year volume X [1 + growth rate]
    assert (df_detail.loc[parameters['present_year'] + 1]['Units'].equals(
            df_detail.loc[parameters['present_year']]['Units'] * (1 + parameters['volume_growth_rate']))), \
            "Volume growth rate applied incorrectly to df_detail Units"

    # calculate projected Vertice volumes
    df_vertice_ndc_volumes = get_vertice_volume_forecast(df_detail, df_gfm, parameters)

    # project future WAC prices
    df_vertice_ndc_prices = get_vertice_ndc_prices(df_detail, df_gfm, parameters)

    # calculate COGS and add to df_detail and df_gfm
    df_detail, df_gfm = calculate_cogs(df_detail, df_gfm, df_vertice_ndc_volumes, parameters)

    ##############################################################
    # calculate remaining financial line items
    ##############################################################
    df_gfm['Net Sales'] = (df_vertice_ndc_prices *
                           df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000
    df_gfm['Gross Sales'] = df_gfm['Net Sales'] / (1 - parameters['gtn_%'])
    df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
    df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
    df_gfm['Profit Share'] = -(df_gfm['Net Sales'] +
                               df_gfm['Standard COGS'] +
                               df_gfm['Distribution'] +
                               df_gfm['Write-offs']) * df_gfm['Profit Share %']
    df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + \
                     df_gfm['Profit Share'] + df_gfm['Milestone Payments']
    df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
    df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS'] / 360
    df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales'] / 360
    df_gfm['Accounts Payable'] = - parameters['DPO'] * \
                                 (df_gfm['Standard COGS'] + df_gfm['Distribution'] +
                                  df_gfm['Write-offs'] + df_gfm['Profit Share'] +
                                  df_gfm['Milestone Payments'] + df_gfm['SG&A']) / 360
    df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - \
                                df_gfm['Accounts Payable']
    df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - \
                     df_gfm['Tax depreciation']
    df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + \
                                 df_gfm['Write-off of Residual Tax Value'] + \
                                 df_gfm['Other Income, Expenses, Except Items'] + \
                                 df_gfm['Additional Impacts on P&L']
    df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
    df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + \
                                         df_gfm['Other Net Current Assets']
    df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - \
                                             df_gfm['Total Net Current Assets'].shift(1)
    df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
    df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + \
                    df_gfm['Tax depreciation'] + df_gfm['Additional Non-cash Effects'] - \
                    df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + \
                    df_gfm['Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']

    return df_gfm, df_detail


def calculate_irr(df_gfm, parameters):
    """
    Calculate internal rate of return (IRR)
    :param df_gfm: Dataframe containing forecasted annual cash flows
    :param parameters: Dictionary of model variables, including Present Year and Years to Discount
    :return: irr value
    """
    irr = np.irr(df_gfm.FCF.loc[parameters['present_year']:
                                parameters['present_year'] + parameters['years_discounted']])
    if math.isnan(irr):
        irr = 'N/A'
    return irr


def calculate_npv(df_gfm, parameters):
    """
    Calculate net present value (NPV)
    :param df_gfm: Dataframe containing forecasted annual cash flows
    :param parameters: Dictionary of model variables, including Present Year and Years to Discount
    :return:
        npv: net present value
        pv: list of present values by year
    """
    x = 0
    pv = []
    for i in df_gfm.FCF.loc[parameters['present_year']:
                            parameters['present_year'] + parameters['years_discounted']]:
        pv.append(i / (1 + parameters['discount_rate']) ** x)
        x += 1
    npv = sum(pv)
    return npv, pv


def calculate_payback(df_gfm, parameters):
    """
    Calculate payback period by checking what year cumulative cash flows become positive
    :param df_gfm: Dataframe containing forecasted annual cash flows
    :param parameters: Dictionary of model variables, including Present Year and Years to Discount
    :return: payback period
    """
    df_gfm['Cumulative FCF'] = np.cumsum(df_gfm['FCF'].loc[parameters['present_year']:
                                                           parameters['present_year'] +
                                                           parameters['years_discounted'] + 1])
    df_gfm['Cumulative FCF'] = df_gfm['Cumulative FCF'].fillna(0)
    idx = df_gfm[df_gfm['Cumulative FCF'] <= 0].index.max()  # last full year for payback calc
    if idx == parameters['last_forecasted_year']:
        payback_period = '> 10'
    else:
        payback_period = idx - parameters['present_year'] + 1 - \
                         df_gfm['Cumulative FCF'].loc[idx] / df_gfm['FCF'].loc[idx + 1]

    return payback_period


def calculate_moic(df_gfm):
    """
    Calculate annual MOIC by
    :param df_gfm: Dataframe containing forecasted annual cash flows
    :param parameters: Dictionary of model variables, including Present Year and Years to Discount
    :return: df_gfm updated with MOIC column
    """
    amt_invested = df_gfm['Total Capitalized'] + df_gfm['R&D'] + df_gfm['SG&A'] + \
                   df_gfm['Milestone Payments']
    cum_amt_invested = np.cumsum(amt_invested)
    moic = []
    for i in range(len(df_gfm['Exit Values'])):
        if cum_amt_invested.iloc[i] == 0:
            moic.append(0)
        else:
            moic.append(-df_gfm['Exit Values'].iloc[i] / cum_amt_invested.iloc[i])
    df_gfm["MOIC"] = moic
    return df_gfm


def valuation_calculations(parameters, df_gfm):
    """
    Calculate the 5 key valuation numbers: IRR, NPV, payback period, exit value, MOIC. Save results to dictionary
    to be written to SQLite database.

    Args:
        parameters: Dictionary of single-value variables.
        df_gfm: Aggregated year-level data from the financial_calculations function.

    Returns:
        result: Single-value variables to be saved in database.
        df_gfm: Select columns of aggregated year-level data to be saved in database.

    """

    irr = calculate_irr(df_gfm, parameters)
    npv, pv = calculate_npv(df_gfm, parameters)

    # calculate present value of FCFs using discount
    df_gfm['FCF PV'] = 0
    df_gfm['FCF PV'].loc[parameters['present_year']:
                         parameters['present_year'] + parameters['years_discounted']] = pv

    payback_period = calculate_payback(df_gfm, parameters)
    df_gfm['Exit Values'] = df_gfm['EBIT'] * parameters['exit_multiple']
    df_gfm = calculate_moic(df_gfm)

    ##############################################################
    # save results
    ##############################################################
    result = {'brand_name': parameters['brand_name'],
              'combined_molecules': parameters['combined_molecules'],
              'dosage_forms': parameters['dosage_forms'],
              'selected_NDCs': parameters['selected_NDCs'],
              'channel': parameters['channel'],
              'indication': parameters['indication'],
              'presentation': parameters['presentation'],
              'internal_external': parameters['internal_external'],
              'brand_status': parameters['brand_status'],
              'comments': parameters['comments'],
              'vertice_filing_month': parameters['vertice_filing_month'],
              'vertice_filing_year': parameters['vertice_filing_year'],
              'vertice_launch_month': parameters['vertice_launch_month'],
              'vertice_launch_year': parameters['vertice_launch_year'],
              'pos': parameters['pos'],
              'exit_multiple': parameters['exit_multiple'],
              'discount_rate': parameters['discount_rate'],
              'tax_rate': parameters['tax_rate'],
              'base_year_volume': df_gfm['Market Volume'].loc[parameters['present_year'] - 1],
              'base_year_market_size': df_gfm['Market Size'].loc[parameters['present_year'] - 1],
              'volume_growth_rate': parameters['volume_growth_rate'],
              'wac_increase': parameters['wac_increase'],
              'api_cost_per_unit': parameters['api_cost_per_unit'],
              'api_cost_unit': parameters['api_units'],
              'profit_margin_override': parameters['profit_margin_override'],
              'standard_cogs_entry': parameters['standard_cogs_entry'],
              'years_discounted': parameters['years_discounted'],
              'cogs_variation': parameters['cogs_variation'],
              'gx_players_adj': parameters['gx_players_adj'],
              'npv': npv,
              'irr': irr,
              'payback_period': payback_period,
              'run_name': parameters['run_name']}

    return result, df_gfm[
        ['Number of Gx Players', 'Profit Share %', 'Milestone Payments', 'R&D',
         'Vertice Price as % of WAC', 'Net Sales', 'COGS', 'EBIT', 'FCF', 'Exit Values', 'MOIC']]


def get_scenario_volume(df_detail, parameters):
    '''

    :param df_detail:
    :param parameters:
    :return:
    '''
    n_years = parameters['last_forecasted_year'] + 1 - parameters['present_year']
    rate_array = np.ones(n_years) + 1 * parameters['volume_growth_rate']
    cum_years = np.arange(n_years) + 1
    comp_growth = rate_array ** cum_years
    get_volumes = lambda x: np.asarray(x) * np.asarray(comp_growth)
    df = df_detail.loc[parameters['present_year'] - 1]['Units'].apply(get_volumes)
    df = pd.DataFrame(np.concatenate(df.values),
                      index=pd.MultiIndex
                      .from_product([df.index.values,
                                     np.arange(parameters['present_year'],
                                               parameters['last_forecasted_year'] + 1)],
                                    names=['ndc_index', 'year_index']))
    df.columns = ['Units']
    df = df.swaplevel(1, 0).sort_values(by=['year_index'])
    df_detail = pd.merge(df_detail, df, on=['year_index', 'ndc_index'], how='left')
    df = df_detail.Units_x.loc[:parameters['present_year'] - 1]
    df = df.append(df_detail.Units_y.loc[parameters['present_year']:])
    df_detail['Units'] = df.values
    df_detail = df_detail.drop(['Units_x', 'Units_y'], axis=1)

    return df_detail


def get_scenario_vertice_sales(df_detail, df_gfm, df_analog, parameters):
    """
    Calculate projected Vertice sales for a given scenario using scenario assumptions (time of launch,
    Vertice market share) and store in df_gfm
    :param df_detail: Dataframe containing year and NDC-level data used in model calculations
    :param df_gfm: Dataframe that holds annual financial calculations
    :param df_analog: Lookup table that holds model assumptions based on historical data
    :param parameters: Dictionary that holds model parameters
    :return:
        df_vertice_ndc_volumes: Holds projected Vertice sales by NDC
        df_gfm: Updated with projected Vertice net sales column
    """

    # adjust for partial year volumes
    vol_adj = []
    for i in range(2016, parameters['last_forecasted_year'] + 1):
        if i < parameters['vertice_launch_year']:
            vol_adj.append(0)
        elif i == parameters['vertice_launch_year']:
            vol_adj.append((13 - parameters['vertice_launch_month']) / 12)
        else:
            vol_adj.append(1)

    # calculate Vertice price and volume
    df_gfm['Vertice Gx Market Share'] = df_analog.loc[
        df_gfm['Number of Gx Players'], [parameters['channel'] + ' Market Share']].values

    df_vertice_ndc_volumes = df_detail['Units'].mul(vol_adj * df_gfm['Gx Penetration'], level=0,
                                                    fill_value=0).mul(df_gfm['Vertice Gx Market Share'],
                                                                      level=0, fill_value=0)
    df_vertice_ndc_volumes = df_vertice_ndc_volumes * parameters['pos']
    df_vertice_ndc_volumes = round(df_vertice_ndc_volumes, 0)

    df_vertice_ndc_prices = df_detail['Price'].mul(df_gfm['Vertice Price as % of WAC'],
                                                   level=0, fill_value=0)
    df_gfm['Net Sales'] = (df_vertice_ndc_prices *
                           df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    return df_vertice_ndc_volumes, df_gfm


def forloop_financial_calculations(parameters, df_gfm, df_detail, df_analog):
    """
    Altered financial_calculations function that handles the parameter scan and
    removes formulas with results that will not change during parameter scan.
    Additionally, it only returns df_gfm, not df_details.

    Args:
        parameters: Dictionary of single-value variables.
        df_gfm: Aggregated year-level data.
        df_detail: Molecule- and year-level data.
        df_analog: Market share and net price % of BWAC lookup table.

    Returns:
        df_gfm: Aggregated year-level data.

    """

    # assign Vertice price as % of either BWAC or GWAC
    df_gfm = set_vertice_price_discount(df_gfm, parameters, df_analog)
    assert ((df_gfm['Vertice Price as % of WAC']).sum() > 0), "Check Vertice price as % of WAC assumptions"

    # calculate volume of market in future
    df_detail = get_scenario_volume(df_detail, parameters)

    # adjust volumes for launch year and if there is a partial year
    df_vertice_ndc_volumes, df_gfm = get_scenario_vertice_sales(df_detail, df_gfm, df_analog, parameters)

    ##############################################################
    # if stmt for margin approach or API approach
    ##############################################################
    if parameters['profit_margin_override'] != '':
        df_gfm['Standard COGS'] = -df_gfm['Net Sales'] * \
                                  (1 - pd.to_numeric(parameters['profit_margin_override']))
    else:
        df_gfm['Standard COGS'] = -(df_detail['std_cost_per_unit'] *
                                    df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    ##############################################################
    # calculating remaining financial line items
    ##############################################################
    df_gfm['Gross Sales'] = df_gfm['Net Sales'] / (1 - parameters['gtn_%'])
    df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
    df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
    df_gfm['Profit Share'] = -(df_gfm['Net Sales'] + df_gfm['Standard COGS'] +
                               df_gfm['Distribution'] + df_gfm['Write-offs']) * \
                             df_gfm['Profit Share %']
    df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + \
                     df_gfm['Profit Share'] + df_gfm['Milestone Payments']
    df_gfm['COGS'] = df_gfm['COGS'] * (1 + parameters['cogs_variation'])
    df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
    df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS'] / 360
    df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales'] / 360
    df_gfm['Accounts Payable'] = - parameters['DPO'] * \
                                 (df_gfm['Standard COGS'] + df_gfm['Distribution'] +
                                  df_gfm['Write-offs'] + df_gfm['Profit Share'] +
                                  df_gfm['Milestone Payments'] + df_gfm['SG&A']) / 360
    df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - \
                                df_gfm['Accounts Payable']
    df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - \
                     df_gfm['Tax depreciation']
    df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + \
                                 df_gfm['Write-off of Residual Tax Value'] + \
                                 df_gfm['Other Income, Expenses, Except Items'] + \
                                 df_gfm['Additional Impacts on P&L']
    df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
    df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + \
                                         df_gfm['Other Net Current Assets']
    df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - \
                                             df_gfm['Total Net Current Assets'].shift(1)
    df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
    df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + \
                    df_gfm['Tax depreciation'] + df_gfm['Additional Non-cash Effects'] - \
                    df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + \
                    df_gfm['Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']

    return df_gfm
