#Function to get 2yr volume CAGR
def get_growth_rate(df):
    units_by_year = df['Units'].sum(level='year_index')
    growth_rate = round(((units_by_year.loc[2018] / units_by_year.loc[2016]) ** (1/2) - 1), 2)
    return growth_rate


#Function to do financial calculations, these are all dependent on previous data
def financial_calculations(parameters, df_gfm, df_detail, df_analog):
    import pandas as pd
    import numpy as np

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
    parameters['vertice_launch_month'] = parameters['launch_delay'] + parameters['vertice_launch_month']
    if parameters['vertice_launch_month'] > 12:
        parameters['vertice_launch_month'] = parameters['vertice_launch_month'] - 12
        parameters['vertice_launch_year'] = parameters['vertice_launch_year'] + 1
    vol_adj = []
    for i in range(2016, parameters['last_forecasted_year'] + 1):
        if i < parameters['vertice_launch_year']:
            vol_adj.append(0)
        elif i == parameters['vertice_launch_year']:
            vol_adj.append((13 - parameters['vertice_launch_month']) / 12)
        else:
            vol_adj.append(1)

    df_vertice_ndc_volumes_100 = df_detail['Units'].mul(vol_adj * df_gfm['Gx Penetration'], level=0, fill_value=0).mul(
        df_gfm['Vertice Gx Market Share'], level=0, fill_value=0)
    df_vertice_ndc_volumes = df_vertice_ndc_volumes_100 * parameters['pos']

    # Calculating price (WAC) in future
    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Price'] = df_detail.loc[i - 1]['Price'] * (1 + parameters['wac_increase'])

    df_vertice_ndc_prices = df_detail['Price'].mul(df_gfm['Vertice Price as % of WAC'], level=0, fill_value=0)
    df_gfm['Net Sales'] = (df_vertice_ndc_prices * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    # Calculating API_cost in future
    for i in range(parameters['present_year'] + 1, parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['API_cost'] = df_detail.loc[i - 1]['API_cost'] * (1 + parameters['cogs']['cost_increase'])

    df_gfm['Standard COGS'] = -(df_detail['API_cost'] * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000
    df_gfm['Other Unit COGS'] = -((parameters['cogs']['excipients'] + parameters['cogs']['direct_labor'] +
                                   parameters['cogs']['variable_overhead'] + parameters['cogs']['fixed_overhead'] +
                                   parameters['cogs']['depreciation'] + parameters['cogs'][
                                       'cmo_markup']) * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    # Financial statement calculations
    df_gfm['Gross Sales'] = df_gfm['Net Sales'] / (1 - parameters['gtn_%'])
    df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
    df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
    df_gfm['Profit Share'] = -(
                df_gfm['Net Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm[
                                 'Profit Share %']
    df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Other Unit COGS'] + df_gfm['Distribution'] + df_gfm[
        'Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
    df_gfm['COGS'] = df_gfm['COGS'] * (1 + parameters['cogs_variation'])
    df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
    df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS'] / 360
    df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales'] / 360
    df_gfm['Accounts Payable'] = - parameters['DPO'] * (
                df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] +
                df_gfm['Milestone Payments'] + df_gfm['SG&A']) / 360
    df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - df_gfm['Accounts Payable']
    df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - df_gfm[
        'Tax depreciation']  # essentially "adjusted EBIT" as it doesn't include other impacts, proceeds from disposals, write-offs of residual tax value, etc
    df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + df_gfm[
        'Write-off of Residual Tax Value'] + df_gfm['Other Income, Expenses, Except Items'] + df_gfm[
                                     'Additional Impacts on P&L']
    df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
    df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + df_gfm[
        'Other Net Current Assets']  # put in as positive numbers, different than excel
    df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - df_gfm[
        'Total Net Current Assets'].shift(1)
    df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
    df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + df_gfm['Tax depreciation'] + df_gfm[
        'Additional Non-cash Effects'] - df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + df_gfm[
                        'Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']

    return(df_gfm, df_detail, df_vertice_ndc_volumes_100)


def valuation_calculations(parameters, df_gfm):
    import pandas as pd
    import numpy as np

    # IRR
    irr = np.irr(df_gfm.FCF.loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted'] + 1])

    # NPV
    x = 0
    pv = []
    for i in df_gfm.FCF.loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted'] + 1]:
        pv.append(i / (1 + parameters['discount_rate']) ** x)
        x += 1
    npv = sum(pv)

    # Discounted Payback Period
    df_gfm['FCF PV'] = 0
    df_gfm['FCF PV'].loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted'] + 1] = pv
    df_gfm['Cumulative Discounted FCF'] = np.cumsum(df_gfm["FCF PV"].loc[parameters['present_year']:parameters['present_year'] + parameters['years_discounted'] + 1])
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
    result = {'brand_name': parameters['brand_name'],
              'combined_molecules': parameters['combined_molecules'],
              'channel': parameters['channel'],
              'indication': parameters['indication'],
              'presentation': parameters['presentation'],
              'comments': parameters['comments'],
              'vertice_filing_month': parameters['vertice_filing_month'],
              'vertice_filing_year': parameters['vertice_filing_year'],
              'vertice_launch_month': parameters['vertice_launch_month'],
              'vertice_launch_year': parameters['vertice_launch_year'],
              'pos': parameters['pos'],
              'base_year_volume': df_gfm['Market Volume'].loc[parameters['present_year'] - 1],
              'base_year_market_size': df_gfm['Market Size'].loc[parameters['present_year'] - 1],
              'volume_growth_rate': parameters['volume_growth_rate'],
              'wac_increase': parameters['wac_increase'],
              'api_cost_per_unit': parameters['api_cost_per_unit'],
              'years_discounted': parameters['years_discounted'],
              'cogs_variation': parameters['cogs_variation'],
              'gx_players_adj': parameters['gx_players_adj'],
              'npv': npv,
              'irr': irr,
              'discounted_payback_period': discounted_payback_period}

    print('loop: printing combined molecules: {}'.format(result['combined_molecules']))

    # return ([parameters['brand_name'],
    #          parameters['combined_molecules'],
    #          parameters['channel'],
    #          parameters['indication'],
    #          parameters['presentation'],
    #          parameters['comments'],
    #          parameters['vertice_filing_month'],
    #          parameters['vertice_filing_year'],
    #          parameters['vertice_launch_month'],
    #          parameters['vertice_launch_year'],
    #          parameters['pos'],
    #          df_gfm['Market Volume'].loc[parameters['present_year'] - 1],
    #          df_gfm['Market Size'].loc[parameters['present_year'] - 1],
    #          parameters['volume_growth_rate'],
    #          parameters['wac_increase'],
    #          parameters['api_cost_per_unit'],
    #          parameters['years_discounted'],
    #          parameters['cogs_variation'],
    #          parameters['gx_players_adj'],
    #          npv,
    #          irr,
    #          discounted_payback_period],
    return result, df_gfm[['Number of Gx Players', 'Profit Share', 'Milestone Payments', 'R&D', 'Net Sales', 'COGS', 'EBIT',
                    'FCF', 'Exit Values', 'MOIC']] #yearly data
#Financial calculations affected only by the parameter scan
def forloop_financial_calculations(parameters, df_gfm, df_detail, df_analog, df_vertice_ndc_volumes):
    import pandas as pd
    import numpy as np

    # Assign Vertice price as % of either BWAC or GWAC
    if parameters['brand_status'] == 'Brand':
        col_name = [parameters['channel'] + ' Net Price Pct BWAC']
        df_gfm['Vertice Price as % of WAC'] = df_analog.loc[df_gfm['Number of Gx Players'], col_name].values
    else:
        df_gfm['Vertice Price as % of WAC'] = (1 - parameters['gtn_%']) * (
                    1 - df_gfm['Price Discount of Current Gx Net Price'])

    # Calculating volume of market in future
    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Units'] = df_detail.loc[i - 1]['Units'] * (1 + parameters['volume_growth_rate'])

    # Adjust volumes for launch year and if there is a partial year
    parameters['vertice_launch_month'] = parameters['launch_delay'] + parameters['vertice_launch_month']
    if parameters['vertice_launch_month'] > 12:
        parameters['vertice_launch_month'] = parameters['vertice_launch_month'] - 12
        parameters['vertice_launch_year'] = parameters['vertice_launch_year'] + 1
    vol_adj = []
    for i in range(2016, parameters['last_forecasted_year'] + 1):
        if i < parameters['vertice_launch_year']:
            vol_adj.append(0)
        elif i == parameters['vertice_launch_year']:
            vol_adj.append((13 - parameters['vertice_launch_month']) / 12)
        else:
            vol_adj.append(1)

    df_vertice_ndc_volumes = df_vertice_ndc_volumes * parameters['pos']

    # Calculating price (WAC) in future
    for i in range(parameters['present_year'], parameters['last_forecasted_year'] + 1):
        df_detail.loc[i]['Price'] = df_detail.loc[i - 1]['Price'] * (1 + parameters['wac_increase'])

    df_vertice_ndc_prices = df_detail['Price'].mul(df_gfm['Vertice Price as % of WAC'], level=0, fill_value=0)
    df_gfm['Net Sales'] = (df_vertice_ndc_prices * df_vertice_ndc_volumes).groupby(level=[0]).sum() / 1000000

    # Financial statement calculations
    df_gfm['Gross Sales'] = df_gfm['Net Sales'] / (1 - parameters['gtn_%'])
    df_gfm['Distribution'] = -df_gfm['Gross Sales'] * parameters['cogs']['distribution']
    df_gfm['Write-offs'] = -df_gfm['Gross Sales'] * parameters['cogs']['writeoffs']
    df_gfm['Profit Share'] = -(
                df_gfm['Net Sales'] + df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs']) * df_gfm[
                                 'Profit Share %']
    df_gfm['COGS'] = df_gfm['Standard COGS'] + df_gfm['Other Unit COGS'] + df_gfm['Distribution'] + df_gfm[
        'Write-offs'] + df_gfm['Profit Share'] + df_gfm['Milestone Payments']
    df_gfm['COGS'] = df_gfm['COGS'] * (1 + parameters['cogs_variation'])
    df_gfm['Gross Profit'] = df_gfm['Net Sales'] + df_gfm['COGS']
    df_gfm['Inventory'] = - parameters['DIO'] * df_gfm['Standard COGS'] / 360
    df_gfm['Accounts Receivable'] = parameters['DSO'] * df_gfm['Net Sales'] / 360
    df_gfm['Accounts Payable'] = - parameters['DPO'] * (
                df_gfm['Standard COGS'] + df_gfm['Distribution'] + df_gfm['Write-offs'] + df_gfm['Profit Share'] +
                df_gfm['Milestone Payments'] + df_gfm['SG&A']) / 360
    df_gfm['Working Capital'] = df_gfm['Inventory'] + df_gfm['Accounts Receivable'] - df_gfm['Accounts Payable']
    df_gfm['EBIT'] = df_gfm['Gross Profit'] + df_gfm['SG&A'] + df_gfm['R&D'] - df_gfm[
        'Tax depreciation']
    df_gfm['Operating Income'] = df_gfm['EBIT'] + df_gfm['Net proceeds from Disposals'] + df_gfm[
        'Write-off of Residual Tax Value'] + df_gfm['Other Income, Expenses, Except Items'] + df_gfm[
                                     'Additional Impacts on P&L']
    df_gfm['Profit Tax'] = -df_gfm['Operating Income'] * parameters['tax_rate']
    df_gfm['Total Net Current Assets'] = df_gfm['Working Capital'] + df_gfm[
        'Other Net Current Assets']
    df_gfm['Change in Net Current Assets'] = df_gfm['Total Net Current Assets'] - df_gfm[
        'Total Net Current Assets'].shift(1)
    df_gfm['Change in Net Current Assets'] = df_gfm['Change in Net Current Assets'].fillna(0)
    df_gfm['FCF'] = df_gfm['Operating Income'] + df_gfm['Profit Tax'] + df_gfm['Tax depreciation'] + df_gfm[
        'Additional Non-cash Effects'] - df_gfm['Change in Net Current Assets'] + df_gfm['Capital Avoidance'] + df_gfm[
                        'Total Capitalized'] - df_gfm['Write-off of Residual Tax Value']

    return(df_gfm, df_detail)