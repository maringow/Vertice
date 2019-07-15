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
    df_gfm['Market Volume'] = df_detail['Units'].groupby(level=[0]).sum()  # TODO somehow annualize the volumes???
    df_gfm['Market Size'] = df_detail['Sales'].groupby(level=[0]).sum()

    # Calculating volume of market in future
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

    # IRR
    irr = np.irr(df_gfm.FCF.loc[parameters['present_year']:2030])

    # NPV
    x = 0
    pv = []
    for i in df_gfm.FCF.loc[parameters['present_year']:2030]:
        pv.append(i / (1 + parameters['discount_rate']) ** x)
        x += 1
    npv = sum(pv)

    # Discounted Payback Period
    df_gfm['FCF PV'] = 0
    df_gfm['FCF PV'].loc[parameters['present_year']:] = pv
    df_gfm['Cummulative Discounted FCF'] = np.cumsum(df_gfm["FCF PV"].loc[parameters['present_year']:])
    df_gfm['Cummulative Discounted FCF'] = df_gfm['Cummulative Discounted FCF'].fillna(0)
    idx = df_gfm[df_gfm['Cummulative Discounted FCF'] <= 0].index.max()  # last full year for payback calc
    if idx == parameters['last_forecasted_year']:
        discounted_payback_period = np.nan
    else:
        discounted_payback_period = idx - parameters['present_year'] + 1 - df_gfm['Cummulative Discounted FCF'].loc[
            idx] / df_gfm['FCF PV'].loc[idx + 1]

    # Exit values (specificially saves value in 2021)
    df_gfm['Exit Values'] = df_gfm['EBIT'] * parameters['exit_multiple']
    exit_value_2021 = df_gfm['Exit Values'].loc[2023]

    # MOIC in 2021
    amt_invested = df_gfm['Total Capitalized'] + df_gfm['R&D'] + df_gfm['SG&A'] + df_gfm['Milestone Payments']
    cum_amt_invested = np.cumsum(amt_invested)
    MOIC = []
    for i in range(len(df_gfm['Exit Values'])):
        if cum_amt_invested.iloc[i] == 0:
            MOIC.append(0)
        else:
            MOIC.append(-df_gfm['Exit Values'].iloc[i] / cum_amt_invested.iloc[i])
    df_gfm["MOIC"] = MOIC
    MOIC_2021 = df_gfm["MOIC"].loc[2023]

    return (irr,
            npv,
            discounted_payback_period,
            df_gfm['Market Size'].loc[parameters['present_year'] - 1],
            df_gfm['Market Volume'].loc[parameters['present_year'] - 1],
            # yearly data:
            df_gfm[['Exit Values', 'MOIC', 'Net Sales', 'COGS', 'EBIT', 'FCF', 'Profit Share']])

