import pandas as pd
import numpy as np
import re


def get_base_units(df):
    def make_numeric(df):
        df = df.str.replace('[^0-9]', '')
        df = df.fillna(0)
        df = pd.to_numeric(df)
        return df

    # NSP Ext.Units is Pack_Quantity * Units * Pack_Size
    # so dropping them
    # df = df.drop(['2013_NSP Ext. Units', '2014_NSP Ext. Units',
    #               '2015_NSP Ext. Units', '2016_NSP Ext. Units', '2017_NSP Ext. Units',
    #               '2018_NSP Ext. Units', '2019_NSP Ext. Units'], axis=1)
    df['2013_Sales $'] = make_numeric(df['2013_Sales $'])
    df['2014_Sales $'] = make_numeric(df['2014_Sales $'])
    df['2015_Sales $'] = make_numeric(df['2015_Sales $'])
    df['2016_Sales $'] = make_numeric(df['2016_Sales $'])
    df['2017_Sales $'] = make_numeric(df['2017_Sales $'])
    df['2018_Sales $'] = make_numeric(df['2018_Sales $'])
    df['2019_Sales $'] = make_numeric(df['2019_Sales $'])
    df['2013_Units'] = make_numeric(df['2013_Units'])
    df['2014_Units'] = make_numeric(df['2014_Units'])
    df['2015_Units'] = make_numeric(df['2015_Units'])
    df['2016_Units'] = make_numeric(df['2016_Units'])
    df['2017_Units'] = make_numeric(df['2017_Units'])
    df['2018_Units'] = make_numeric(df['2018_Units'])
    df['2019_Units'] = make_numeric(df['2019_Units'])
    # df['2013_NSP Ext. Units'] = make_numeric(df['2013_NSP Ext. Units'])
    # df['2014_NSP Ext. Units'] = make_numeric(df['2014_NSP Ext. Units'])
    # df['2015_NSP Ext. Units'] = make_numeric(df['2015_NSP Ext. Units'])
    # df['2016_NSP Ext. Units'] = make_numeric(df['2016_NSP Ext. Units'])
    # df['2017_NSP Ext. Units'] = make_numeric(df['2017_NSP Ext. Units'])
    # df['2018_NSP Ext. Units'] = make_numeric(df['2018_NSP Ext. Units'])
    # df['2019_NSP Ext. Units'] = make_numeric(df['2019_NSP Ext. Units'])

    # getting most common unit sold, make base unit
    df['unitssum'] = df['2013_Units'] + df['2014_Units'] + df['2015_Units'] + df['2016_Units'] + df['2017_Units'] + df[
        '2018_Units'] + df['2019_Units']
    x = df.groupby(['Combined Molecule', 'Strength'])['2019_Units', 'unitssum'].sum().sort_values(
        ['Combined Molecule', 'unitssum'], ascending=[True, False]).reset_index()
    x = x.groupby('Combined Molecule').nth(1).drop(['2019_Units', 'unitssum'], axis=1)
    df = df.merge(x, on='Combined Molecule', how='left', suffixes=['', 'Base Unit']).drop('unitssum', axis=1)
    df = df.rename(columns={"StrengthBase Unit": "Base Unit1"})
    # if no sales, the most freq in the db is the base unit
    x = df[df['Base Unit1'] != df['Base Unit1']]
    x = x.groupby(['Combined Molecule', 'Strength'])['Strength'].count().reset_index(name='count')
    x = x.sort_values(['Combined Molecule', 'count'], ascending=[True, False])
    x = x.groupby('Combined Molecule').first().drop('count', axis=1)
    df = df.merge(x, on='Combined Molecule', how='left', suffixes=['', 'Base Unit'])
    df = df.rename(columns={"StrengthBase Unit": "Base Unit2"})
    # combining columns
    df['Base Unit'] = (df['Base Unit1'].fillna('') + df['Base Unit2'].fillna(''))
    df = df.drop(['Base Unit1', 'Base Unit2'], axis=1)

    #parsing the number of base units each NDC has
    df['Units'] = np.nan
    for i in range(len(df)):
        # if the base unit is the strength
        if df['Base Unit'][i] == df.Strength[i]:
            df.Units[i] = 1
        # if strength is nan
        elif df.Strength.iloc[i] != df.Strength.iloc[i]:
            df.Units[i] = ''
            # if there are dashes (setting to blank since inconsistent format)
        elif re.sub('[^-]', '', str(df.Strength.iloc[i])).find('-') == 0:
            df.Units[i] = ''
            # if one is a ratio and the other isn't
        elif re.sub('[^/]', '', str(df.Strength.iloc[i])) != re.sub('[^/]', '', str(df['Base Unit'].iloc[i])):
            df.Units[i] = ''
        # for ratios
        elif re.sub('[^/]', '', str(df.Strength.iloc[i])).find('/') == 0:
            try:
                a1, b1 = str(df.Strength.iloc[i]).split('/')
                a2, b2 = str(df['Base Unit'].iloc[i]).split('/')

                a1unit = re.sub('[. 0-9]', '', str(a1))
                b1unit = re.sub('[. 0-9]', '', str(b1))
                a2unit = re.sub('[. 0-9]', '', str(a2))
                b2unit = re.sub('[. 0-9]', '', str(b2))
            except:
                df.Units.iloc[i] = ''
            else:
                if (b1unit == '') | (b2unit == ''):
                    df.Units.iloc[i] = ''
                elif (a1unit == a2unit) & (b1unit == b2unit):
                    a1 = a1.split(a1unit)[0]
                    a2 = a2.split(a2unit)[0]
                    b1 = b1.split(b1unit)[0]
                    b2 = b2.split(b2unit)[0]
                    if b1 == '':
                        b1 = 1
                    if b2 == '':
                        b2 = 1
                    df.Units.iloc[i] = (float(a1) / float(a2) * float(b2) / float(b1))
                else:
                    df.Units.iloc[i] = ''

        # adjust if base unit is the strength unit
        elif re.sub('[. 0-9]', '', str(df.Strength.iloc[i])) == re.sub('[.0-9]', '', str(df['Base Unit'].iloc[i])):
            x = re.sub('[. 0-9]', '', str(df.Strength.iloc[i]))
            a = list(filter(None, str(df.Strength.iloc[i]).split(x)))[0]
            b = list(filter(None, str(df['Base Unit'].iloc[i]).split(x)))[0]
            try:
                df.Units.iloc[i] = (float(a) / float(b))
            except:
                df.Units.iloc[i] = ''

        else:
            df.Units = ''
    for i in range(len(df)):
        try:
            df['Units'].iloc[i] = df['Units'].iloc[i] * df['Pack Quantity'].iloc[i] * df['Pack Size'].iloc[i]
        except:
            df['Units'].iloc[i] = df['Units'].iloc[i]
    return (df)