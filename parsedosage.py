import re
import pandas as pd
import numpy as np


def get_base_units(df):
    """
    Parse IMS data to get base units and quantity of base units for each NDC.
    Parsed data is used to calculate API costs per NDC, which auto-populates in the gui entry boxes.
    Base Unit is based on most units sold of the NDCs selected in GUI windows.

    Example:
    **Before**
    | Pack Size | Pack Quantity | Strength |        Pack          |
    |:---------:|:-------------:|:--------:|:--------------------:|
    | 1         | 1             |100MG/ML  | SYR 100MG/ML 1.0ML   |
    | 1         | 90            | 8MG      | CAP 8MG 90           |
    | 4         | 25            | 0.4MG    | TAB SL .4MG 25X4     |
    | 1         | 4000          | 100%     | LIQ BULK 100% 4000ML |
    | 1         | 100           | 15MG     | TAB 15MG 15          |

    **After**
    | Pack Size | Pack Quantity | Strength |        Pack          | Base Unit | Units |
    |:---------:|:-------------:|:--------:|:--------------------:|:---------:|:-----:|
    | 1         | 1             |100MG/ML  | SYR 100MG/ML 1.0ML   | 40MG/.4ML | 1     |
    | 1         | 90            | 8MG      | CAP 8MG 90           | 1MG       | 720   |
    | 4         | 25            | 0.4MG    | TAB SL .4MG 25X4     | 0.4MG     | 100   |
    | 1         | 4000          | 100%     | LIQ BULK 100% 4000ML | 100%      | 4000  |
    | 1         | 100           | 15MG     | TAB 15MG 15          | 5MG       | 300   |

    """
    ##############################################################
    # reformating numerical data to be numerical (yearly units used to find most common Base Unit)
    ##############################################################
    def make_numeric(df):
        df = df.str.replace('[^0-9]', '')
        df = df.fillna(0)
        df = pd.to_numeric(df)
        return df

    df['2017_Units'] = make_numeric(df['2017_Units'])
    df['2018_Units'] = make_numeric(df['2018_Units'])
    df['2019_Units'] = make_numeric(df['2019_Units'])

    ##############################################################
    # getting the Base Unit
    ##############################################################
    # getting most common unit sold, make Base Unit
    df['unitssum'] = df['2017_Units'] + df['2018_Units'] + df['2019_Units']
    x = df.groupby(['Combined Molecule', 'Strength'])['2019_Units', 'unitssum']\
        .sum().sort_values(['Combined Molecule', 'unitssum'], ascending=[True, False]).reset_index()
    x = x.groupby('Combined Molecule').first().drop(['2019_Units', 'unitssum'], axis=1)
    df = df.merge(x, on='Combined Molecule', how='left',
                  suffixes=['', 'Base Unit']).drop('unitssum', axis=1)
    df = df.rename(columns={"StrengthBase Unit": "Base Unit"})
    df['Base Unit'] = df['Base Unit'].fillna('')

    ##############################################################
    # parsing the number of Base Units in the Strength string
    ##############################################################
    df['Units'] = np.nan
    for i in range(len(df)):
        # if the base Unit is the Strength
        if df['Base Unit'][i] == df.Strength[i]:
            df.Units[i] = 1
        # if Strength is nan
        elif df.Strength.iloc[i] != df.Strength.iloc[i]:
            df.Units[i] = ''
            # if there are dashes (setting to blank since inconsistent format)
        elif re.sub('[^-]', '', str(df.Strength.iloc[i])).find('-') == 0:
            df.Units[i] = ''
            # if only Strength or Base Unit is a ratio and the other isn't
        elif re.sub('[^/]', '', str(df.Strength.iloc[i])) != \
                re.sub('[^/]', '', str(df['Base Unit'].iloc[i])):
            df.Units[i] = ''
        # if both ratios (when both Strength and Base Unit are ratios e.g. 10MG/20ML)
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
        # if both Strength are Base Unit single units e.g. 10MG or 5ML
        elif re.sub('[. 0-9]', '', str(df.Strength.iloc[i])) == \
                re.sub('[.0-9]', '', str(df['Base Unit'].iloc[i])):
            x = re.sub('[. 0-9]', '', str(df.Strength.iloc[i]))
            a = list(filter(None, str(df.Strength.iloc[i]).split(x)))[0]
            b = list(filter(None, str(df['Base Unit'].iloc[i]).split(x)))[0]
            try:
                df.Units.iloc[i] = (float(a) / float(b))
            except:
                df.Units.iloc[i] = ''
        # if not parsed, it goes blank
        else:
            df.Units.iloc[i] = ''

    ##############################################################
    # multiplying parsed # if possible to get total Base Units
    ##############################################################
    for i in range(len(df)):
        try:
            df['Units'].iloc[i] = df['Units'].iloc[i] *\
                                  df['Pack Quantity'].iloc[i] * \
                                  df['Pack Size'].iloc[i]
        except:
            df['Units'].iloc[i] = df['Units'].iloc[i]

    return df
