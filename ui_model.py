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

##----------------------------------------------------------------------
## DEFINE GUI WINDOW

# create, size, and title window
window1 = Tk()
window1.geometry("600x400")
window1.title("Test")

# create window header
title = Label(window1, text='Generics Forecasting Model: Brand Selection')
title.pack(pady=10)

##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)

# ingest IMS and price data
IMS = pd.read_csv('sample_8_molecules_w_product.csv')
prospectoRx = pd.read_csv('gleevec_prospectorx.csv')


##----------------------------------------------------------------------
## BUILD GUI COMPONENTS AND OPEN DISPLAY

parameters = {'brand_name': ''}

# define function to collect field entries and store as variables
def collect_entry_fields(event):
    parameters['brand_name'] = brand_combo.get()


# get valid brands from IMS file
brands = sorted(IMS['Product Sum'].unique())

# add label and combobox for brand selection
brand_label = Label(window1, text='Select a brand name drug: ')
brand_label.pack()
brand_combo = ttk.Combobox(window1, values=brands)
brand_combo.pack()
brand_combo.bind("<<ComboboxSelected>>", collect_entry_fields)



# add Finish button
continue_button = Button(window1, text='Continue', command=window1.quit)
continue_button.pack(pady=10)


# open window
window1.mainloop()

print('Brand: {}'.format(parameters['brand_name']))



# pull records that are therapeutic equivalents of selected brand name drug
# find Combined Molecule and Prod Form 3 of selected brand name drug; store in lists in case there are multiple
combined_molecules = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Combined Molecule'].unique()
dosage_forms = IMS.loc[IMS['Product Sum'] == parameters['brand_name']]['Prod Form3'].unique()

# find all IMS records that match the Combined Molecule and Prod Form 3
df_equivalents = IMS.loc[(IMS['Combined Molecule'].isin(combined_molecules)) & (IMS['Prod Form3'].isin(dosage_forms))]
print(df_equivalents)



# create second window
window2 = Tk()
window2.geometry("600x400")
window2.title("Test")

# create window header
title = Label(window2, text='Generics Forecasting Model: User Input')
title.pack(pady=10)


# create label for brand selection and number of equivalents found
selection_label = Label(window2, text='{} therapeutic equivalents found for {}'
                        .format(len(df_equivalents), parameters['brand_name']))
selection_label.pack(pady=10)


# add entry boxes for desired units and API cost per unit
unit_label = Label(window2, text='Enter units: ')
unit_label.pack(pady=10)
unit_entry = Entry(window2)
unit_entry.pack()

cost_per_unit_label = Label(window2, text='Enter API cost per unit: ')
cost_per_unit_label.pack(pady=10)
cost_per_unit_entry = Entry(window2)
cost_per_unit_entry.pack()


# add entry boxes for API units for each pack type found in therapeutic equivalents
packs = df_equivalents['Pack'].unique()
print(packs
      )
# for p in packs:
#     NDC_label = Label(window2, text=p)
#     NDC_label.pack(pady=10)


# add Finish button
run_model_button = Button(window2, text='Run Model', command=window2.quit)
run_model_button.pack(pady=10)


# open window
window2.mainloop()