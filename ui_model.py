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
window = Tk()
window.geometry("600x400")
window.title("Test")

# create window header
title = Label(window, text='Generics Forecasting Model: User Input')
title.pack(pady=10)

##----------------------------------------------------------------------
## INGEST DATA (IMS, ProspectoRx)

# ingest IMS and price data
IMS = pd.read_csv('sample_8_molecules_w_product.csv')
prospectoRx = pd.read_csv('gleevec_prospectorx.csv')


##----------------------------------------------------------------------
## BUILD GUI COMPONENTS AND OPEN DISPLAY

# define function to collect field entries and store as variables
def collect_entry_fields(event):
    global brand
    brand = brand_combo.get()


# get valid brands from IMS file
brands = sorted(IMS['Product Sum'].unique())

# add label and combobox for brand selection
brand_label = Label(window, text='Select a brand name drug: ')
brand_label.pack()
brand_combo = ttk.Combobox(window, values=brands)
brand_combo.pack()
brand_combo.bind("<<ComboboxSelected>>", collect_entry_fields)


# add Finish button
finish_button = Button(window, text='Finish', command=window.quit)
finish_button.pack(pady=10)


# open window
window.mainloop()

print('Brand: {}'.format(brand))




# pull records that are therapeutic equivalents of selected brand name drug
# find Combined Molecule and Prod Form 3 of selected brand name drug; store in lists in case there are multiple
combined_molecules = IMS.loc[IMS['Product Sum'] == brand]['Combined Molecule'].unique()
dosage_forms = IMS.loc[IMS['Product Sum'] == brand]['Prod Form3'].unique()


print(combined_molecules)