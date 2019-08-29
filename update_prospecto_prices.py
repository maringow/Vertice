import pandas as pd
import tkinter as tk


window = tk.Tk()
window1 = update_prospecto_gui.EnterFilepath(window)
window.mainloop()

print(window1.parameters['excel_filepath'])

#
# # read in master file
# prospectoRx = pd.read_excel('WAC_082719.xlsx')
# if 'PriceUpdateDate' not in prospectoRx.columns:  # add this column only if it doesn't exist
#     prospectoRx['PriceUpdateDate'] = np.repeat('From 2019-08-28 data pull', len(prospectoRx))
#
# # read in new pricing data
# newdata = pd.read_csv('week_pull_20190829.csv')
#
# def strip_non_numeric(df_column):
#     df_column = df_column.str.replace('[^0-9]', '')
#     df_column = pd.to_numeric(df_column)
#     return df_column
# newdata['PackageIdentifier'] = strip_non_numeric(newdata['PackageIdentifier'])
#
# for i in newdata.PackageIdentifier:
#     if sum(prospectoRx.NDC == i) == 0:  # if the NDC is not in the db, we add the NDC to the master file
#         x = pd.DataFrame(newdata[newdata.PackageIdentifier == i])
#         if x.TypeName.values == 'NDC':
#             x.TypeName = 'NDC11'
#         x = pd.DataFrame([x.PackageIdentifier.values[0], x.TypeName.values[0], x.SpecificDrugProductID.values[0],
#                           x.BrandGenericStatus.values[0],  x.CompanyName.str.replace(',', '').values[0], '', '', '',
#                           x.PackageSize.values[0], x.WACUnitPrice.values[0],  x.WACPrice.values[0],
#                           x.WACBeginDate.values[0]]).transpose()
#         x.columns = prospectoRx.columns
#         prospectoRx = prospectoRx.append(x).reset_index(drop=True)
#     else:  # updates the price in the master file
#         x = pd.DataFrame(newdata[newdata.PackageIdentifier == i])
#         rownum = prospectoRx[prospectoRx.NDC == i].index.values
#         prospectoRx.WACPrice.loc[rownum] = x.WACPrice.values
#         prospectoRx.PriceUpdateDate.loc[rownum] = x.WACBeginDate.values
#
# # save the updated master file, replacing the previous master file
# prospectoRx.to_excel('WAC_082719.xlsx')
