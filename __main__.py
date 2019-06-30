import operator
import numpy as np
import matplotlib as mpl
import datetime as dt
import pandas as pd
import re
import openpyxl as xl
import tkinter
from tkinter import *
from tkinter import ttk
import gui


##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)

# ingest IMS and price data
IMS = pd.read_csv('sample_8_molecules_w_product.csv')
prospectoRx = pd.read_csv('gleevec_prospectorx.csv')

# get valid brands from IMS file
brands = sorted(IMS['Product Sum'].unique())


##----------------------------------------------------------------------
## OPEN WINDOW1
window = Tk()
window1 = gui.window1(window, brands)
window.mainloop()
print('saved variable: {}'.format(window1.parameters['brand_name']))


##----------------------------------------------------------------------
## FIND THERAPEUTIC EQUIVALENTS

# pull records that are therapeutic equivalents of selected brand name drug
# find Combined Molecule and Prod Form 3 of selected brand name drug; store in lists in case there are multiple
combined_molecules = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Combined Molecule'].unique()
dosage_forms = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Prod Form3'].unique()

# find all IMS records that match the Combined Molecule and Prod Form 3
df_equivalents = IMS.loc[(IMS['Combined Molecule'].isin(combined_molecules)) & (IMS['Prod Form3'].isin(dosage_forms))]
print(df_equivalents)
