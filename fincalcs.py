import pandas as pd
import numpy as np
import time

#Function to get 2yr volume CAGR #TODO - years - will need to update when we have new annual data
def get_growth_rate(df):
    import numpy as np
    units_by_year = df['Units'].sum(level='year_index')
    growth_rate1 = ((units_by_year.loc[2018] / units_by_year.loc[2016]) ** (1/2) - 1)
    growth_rate2 = ((units_by_year.loc[2018] / units_by_year.loc[2017]) - 1)
    if abs(growth_rate1) != np.inf:
        growth_rate = growth_rate1
    elif abs(growth_rate2) != np.inf:
        growth_rate = growth_rate2
    else:
        growth_rate= 0
    return growth_rate


#Function to do financial calculations, these are all dependent on previous data
def financial_calculations(parameters, df_gfm, df_detail, df_analog):

    # Assign Vertice price as % of either BWAC or GWAC
    if parameters['brand_status'] == 'Brand':
        col_name = [parameters['channel'] + ' Net Price Pct BWAC']
        df_gfm['Vertice Price as % of WAC'] = df_analog.loc[df_gfm['Number of Gx Players'], col_name].values
    else:
        df_gfm['Vertice Price as % of WAC'] = (1 - parameters['gtn_%']) * (
                    1 - df_gfm['Price Discount of Current Gx Net Price'])

    # Keep market unit sales for reference
    df_gfm['Market Volume'] = df_detail['Units'].groupby(level=[0]).sum()  # TODO annualize the volumes???
    df_gfm['Market Size'] = df_detail['Sales'].groupby(level=[0]).sum()

    # Calculating volume of market in future
    df_detail['Units'] = df_detail['Units'].fillna(0)
    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Units'] = df_detail.loc[i - 1]['Units'] * (1 + parameters['volume_growth_rate'])

    # Adjust volumes for launch year and if there is a partial year
    vol_adj = []
    for i in range(2016, parameters['last_forecasted_year'] + 1):
        if i < parameters['vertice_launch_year']:
            vol_adj.append(0)
        elif i == parameters['vertice_launch_year']:
            vol_adj.append((13 - parameters['vertice_launch_month']) / 12)
        else:
            vol_adj.append(1)

    df_vertice_ndc_volumes = df_detail['Units'].mul(vol_adj * df_gfm['Gx Penetration'], level=0, fill_value=0).mul(
        df_gfm['Vertice Gx Market Share'], level=0, fill_value=0)
    df_vertice_ndc_volumes = df_vertice_ndc_volumes * parameters['pos']

    # Calculating price (WAC) in future
    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Price'] = df_detail.loc[i - 1]['Price'] * (1 + parameters['wac_increase'])

    df_vertice_ndc_prices = df_detail['Price'].mul(df_gfm['Vertice Price as % of WAC'], level=0, fill_value=0)
    df_gfm['Net Sales'] = (df_vertice_ndc_prices * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    df_gfm['Gross Sales'] = df_gfm['Net Sales'] / (1 - parameters['gtn_%'])
    df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
    df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']

    #if stmt for margin approach or API approach
    if parameters['profit_margin_override'] != '':
        df_gfm['Standard COGS'] = -df_gfm['Net Sales'] * (1 - pd.to_numeric(parameters['profit_margin_override']))
    else:
        # Calculating std_cost_per_unit in future
        df_detail['std_cost_per_unit'] = df_detail['API_cost'].add((parameters['cogs']['excipients'] +
                                                                    parameters['cogs']['direct_labor'] +
                                                                    parameters['cogs']['variable_overhead'] +
                                                                    parameters['cogs']['fixed_overhead'] +
                                                                    parameters['cogs']['depreciation'] +
                                                                    parameters['cogs']['cmo_markup']), level=0, fill_value=0)
        for i in range(parameters['present_year'] + 1, parameters['last_forecasted_year'] + 1):
            df_detail.loc[i]['std_cost_per_unit'] = df_detail.loc[i - 1]['std_cost_per_unit'] * (1 + parameters['cogs']['cost_increase'])

        df_gfm['Standard COGS'] = -(df_detail['std_cost_per_unit'] * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    df_gfm['Profit Share'] = -(df_gfm['Net Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm['Profit Share %']
    df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
    df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
    df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS'] / 360
    df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales'] / 360
    df_gfm['Accounts Payable'] = - parameters['DPO'] * (
                df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] +
                df_gfm['Milestone Payments'] + df_gfm['SG&A']) / 360
    df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - df_gfm['Accounts Payable']
    df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - df_gfm['Tax depreciation']  # essentially "adjusted EBIT" as it doesn't include other impacts, proceeds from disposals, write-offs of residual tax value, etc
    df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + df_gfm[
        'Write-off of Residual Tax Value'] + df_gfm['Other Income, Expenses, Except Items'] + df_gfm[
                                     'Additional Impacts on P&L']
    df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
    df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + df_gfm['Other Net Current Assets']  # put in as positive numbers, different than excel
    df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - df_gfm['Total Net Current Assets'].shift(1)
    df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
    df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + df_gfm['Tax depreciation'] + df_gfm[
        'Additional Non-cash Effects'] - df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + df_gfm[
                        'Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']

    return(df_gfm, df_detail)


def valuation_calculations(parameters, df_gfm):

    # IRR
    irr = np.irr(df_gfm.FCF.loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted']])

    # NPV
    x = 0
    pv = []
    for i in df_gfm.FCF.loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted']]:
        pv.append(i / (1 + parameters['discount_rate']) ** x)
        x += 1
    npv = sum(pv)

    # Discounted Payback Period
    df_gfm['FCF PV'] = 0
    df_gfm['FCF PV'].loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted']] = pv
    df_gfm['Cumulative Discounted FCF'] = np.cumsum(df_gfm["FCF PV"].loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted']+1])
    df_gfm['Cumulative Discounted FCF'] = df_gfm['Cumulative Discounted FCF'].fillna(0)
    idx = df_gfm[df_gfm['Cumulative Discounted FCF'] <= 0].index.max()  # last full year for payback calc
    if idx == parameters['last_forecasted_year']:
        discounted_payback_period = np.nan
    else:
        discounted_payback_period = idx - parameters['present_year'] + 1 - df_gfm['Cumulative Discounted FCF'].loc[
            idx] / df_gfm['FCF PV'].loc[idx + 1]

    # Exit values
    df_gfm['Exit Values'] = df_gfm['EBIT'] * parameters['exit_multiple']

    # MOIC
    amt_invested = df_gfm['Total Capitalized'] + df_gfm['R&D'] + df_gfm['SG&A'] + df_gfm['Milestone Payments']
    cum_amt_invested = np.cumsum(amt_invested)
    MOIC = []
    for i in range(len(df_gfm['Exit Values'])):
        if cum_amt_invested.iloc[i] == 0:
            MOIC.append(0)
        else:
            MOIC.append(-df_gfm['Exit Values'].iloc[i] / cum_amt_invested.iloc[i])
    df_gfm["MOIC"] = MOIC

    # save results
    result = {'brand_name': parameters['brand_name'],
              'combined_molecules': parameters['combined_molecules'],
              'dosage_forms': parameters['dosage_forms'],
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
              'discounted_payback_period': discounted_payback_period,
              'run_name': parameters['run_name']}

    return result, df_gfm[['Number of Gx Players', 'Profit Share %', 'Milestone Payments', 'R&D',
                           'Vertice Price as % of WAC','Net Sales', 'COGS', 'EBIT',
                            'FCF', 'Exit Values', 'MOIC']] #yearly data


def forloop_financial_calculations(parameters, df_gfm, df_detail, df_analog):
    time_A = time.time()
    # Assign Vertice price as % of either BWAC or GWAC
    if parameters['brand_status'] == 'Brand':
        col_name = [parameters['channel'] + ' Net Price Pct BWAC']
        df_gfm['Vertice Price as % of WAC'] = df_analog.loc[df_gfm['Number of Gx Players'], col_name].values
    else:
        df_gfm['Vertice Price as % of WAC'] = (1 - parameters['gtn_%']) * (1 - df_gfm['Price Discount of Current Gx Net Price'])
    time_B = time.time()
    # Calculating volume of market in future
    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Units'] = df_detail.loc[i - 1]['Units'] * (1 + parameters['volume_growth_rate'])
    #TODO times it by an array and see if this is faster
    #look into np.mul function so not a for loop?
    # rate_array = np.ones(parameters['present_year'], parameters['last_forecasted_year'] + 1)

    # rate_array = np.ones(10) + 1 * parameters['volume_growth_rate']
    # cum_years = np.arange(10) + 1
    # comp_growth = rate_array ** cum_years




    time_C = time.time()

    # Adjust volumes for launch year and if there is a partial year
    parameters['vertice_launch_year'] = parameters['launch_delay'] + parameters['vertice_launch_year']
    vol_adj = []
    for i in range(2016, parameters['last_forecasted_year'] + 1):
        if i < parameters['vertice_launch_year']:
            vol_adj.append(0)
        elif i == parameters['vertice_launch_year']:
            vol_adj.append((13 - parameters['vertice_launch_month']) / 12)
        else:
            vol_adj.append(1)
    time_D = time.time()
    # Assign Vertice GX Market Share based on analog
    df_gfm['Vertice Gx Market Share'] = df_analog.loc[df_gfm['Number of Gx Players'],[parameters['channel'] + ' Market Share']].values
    time_E = time.time()
    df_vertice_ndc_volumes = df_detail['Units'].mul(vol_adj * df_gfm['Gx Penetration'], level=0, fill_value=0).mul(
    df_gfm['Vertice Gx Market Share'], level=0, fill_value=0)
    df_vertice_ndc_volumes = df_vertice_ndc_volumes * parameters['pos']

    df_vertice_ndc_prices = df_detail['Price'].mul(df_gfm['Vertice Price as % of WAC'], level=0, fill_value=0)
    df_gfm['Net Sales'] = (df_vertice_ndc_prices * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    # Financial statement calculations
    df_gfm['Gross Sales'] = df_gfm['Net Sales'] / (1 - parameters['gtn_%'])
    df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
    df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
    df_gfm['Profit Share'] = -(df_gfm['Net Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm['Profit Share %']
    df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
    df_gfm['COGS'] = df_gfm['COGS'] * (1 + parameters['cogs_variation'])
    df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
    df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS'] / 360
    df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales'] / 360
    df_gfm['Accounts Payable'] = - parameters['DPO'] * (
                df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] +
                df_gfm['Milestone Payments'] + df_gfm['SG&A']) / 360
    df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - df_gfm['Accounts Payable']
    df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - df_gfm['Tax depreciation']
    df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + df_gfm[
        'Write-off of Residual Tax Value'] + df_gfm['Other Income, Expenses, Except Items'] + df_gfm[
                                     'Additional Impacts on P&L']
    df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
    df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + df_gfm['Other Net Current Assets']
    df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - df_gfm['Total Net Current Assets'].shift(1)
    df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
    df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + df_gfm['Tax depreciation'] + df_gfm[
        'Additional Non-cash Effects'] - df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + df_gfm[
                        'Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']
    time_E = time.time()
    print(time_B-time_A,time_C-time_B, time_D-time_C,time_E-time_D)
    return(df_gfm, df_detail) #TODO don't return every column? If it saves time?