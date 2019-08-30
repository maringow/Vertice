import warnings
import tkinter as tk
from datetime import datetime, date
import pandas as pd
import numpy as np
# importing internal modules
import update_prospecto_gui
# turn off warnings for SettingWithCopy and Future
pd.set_option('mode.chained_assignment', None)
warnings.filterwarnings("ignore", category=FutureWarning)

##############################################################
# finding the most recent price change date in the master file
##############################################################
prospectoRx = pd.read_excel('WAC_082719.xlsx')  # TODO have new name for this, Master Pricing File?
try:
    dates_of_changes = prospectoRx[prospectoRx.PriceUpdateDate != 'From 2019-08-27 data pull'].PriceUpdateDate
    dates_of_changes = dates_of_changes.unique()
    x = []
    for i in dates_of_changes:
        x.append(datetime.strptime(i, '%Y-%m-%d')) # TODO make sure it pulls in the most recent date, NEEDS TO BE FIX PLZ
    x = max(x)
except:
    x = date(2019, 8, 27)

##############################################################
# gui window to show last price change date
##############################################################
window = tk.Tk()
window0 = update_prospecto_gui.InfoWindow(window, x)
window.mainloop()


##############################################################
# gui window to select file with price changes
##############################################################
window = tk.Tk()
window1 = update_prospecto_gui.EnterFilepath(window)
window.mainloop()

##############################################################
# read in master file of prices
##############################################################
# prospectoRx.rename(index=str, columns={'Drug Identifier': 'NDC'}, inplace=True)
if 'PriceUpdateDate' not in prospectoRx.columns:  # add these columns only if they doesn't exist
    prospectoRx['WACPrice'] = round(prospectoRx['Package Size'] * prospectoRx['WAC (Unit)'], 2)
    prospectoRx['PriceUpdateDate'] = np.repeat('From 2019-08-27 data pull', len(prospectoRx))
count_df = [len(prospectoRx)]

##############################################################
# read in new pricing data
##############################################################
def strip_non_numeric(df_column):
    df_column = df_column.str.replace('[^0-9]', '')
    df_column = pd.to_numeric(df_column)
    return df_column
newdata = pd.read_csv(window1.parameters['excel_filepath'])
newdata['PackageIdentifier'] = strip_non_numeric(newdata['PackageIdentifier'])
count_df = [count_df[0], len(newdata)]

##############################################################
# if the NDC is not in the db, we make a new row to add the NDC to the master file
# otherwise, we update the price in the master file
##############################################################
for i in newdata.PackageIdentifier:
    if sum(prospectoRx.NDC == i) == 0:
        x = pd.DataFrame(newdata[newdata.PackageIdentifier == i])
        if x.TypeName.values == 'NDC':
            x.TypeName = 'NDC11'
        x = pd.DataFrame([x.PackageIdentifier.values[0], x.TypeName.values[0],
                          x.SpecificDrugProductID.values[0], x.BrandGenericStatus.values[0],
                          x.CompanyName.str.replace(',', '').values[0], '', '', '',
                          x.PackageSize.values[0], x.WACUnitPrice.values[0],  x.WACPrice.values[0],
                          x.WACBeginDate.values[0]]).transpose()
        x.columns = prospectoRx.columns
        prospectoRx = prospectoRx.append(x).reset_index(drop=True)
    else:
        x = pd.DataFrame(newdata[newdata.PackageIdentifier == i])
        rownum = prospectoRx[prospectoRx.NDC == i].index.values
        prospectoRx.WACPrice.loc[rownum] = x.WACPrice.values
        prospectoRx.PriceUpdateDate.loc[rownum] = x.WACBeginDate.values

count_df = [count_df[0], count_df[1], len(prospectoRx)]
##############################################################
# save the updated master file, replacing the previous master file
##############################################################
prospectoRx.to_excel('WAC_082719.xlsx', index=False)  # TODO have better name for this

##############################################################
# gui window to show changes are successful
##############################################################
window = tk.Tk()
window2 = update_prospecto_gui.SuccessfulRun(window, count_df)
window.mainloop()
