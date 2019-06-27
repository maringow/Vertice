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

# get valid brands from IMS file
brands = sorted(IMS['Product Sum'].unique())

# create label and combobox for brand selection
brand_label = Label(window, text='Select a brand name drug: ')
brand_label.pack()
brand_combo = ttk.Combobox(window, values=brands)
brand_combo.pack()
brand = brand_combo.get()
print(brand)

# open window
window.mainloop()


