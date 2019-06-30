import __main__
from tkinter import *
from tkinter import ttk

##----------------------------------------------------------------------
## WINDOW 1: SELECT BRAND NAME


class Window1:
    parameters = {}

    def __init__(self, master, brands):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Brand Selection')
        self.title.pack(pady=10)

        # add label and combobox for brand selection
        self.brand_label = Label(master, text='Select a brand name drug: ')
        self.brand_label.pack()
        self.brand_combo = ttk.Combobox(master, values=brands)
        self.brand_combo.pack()
        self.brand_combo.bind("<<ComboboxSelected>>", self.collect_entry_fields)

        # add Finish button
        self.continue_button = Button(master, text='Continue', command=master.quit)
        self.continue_button.pack(pady=10)

    # function to collect field entries and store as variables
    def collect_entry_fields(self, event):

        self.parameters['brand_name'] = self.brand_combo.get()
        print(self.parameters['brand_name'])


##----------------------------------------------------------------------
## WINDOW 2: CONFIRM BRAND


class Window2:

    def __init__(self, master, brands):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # add label

        # add Finish button
        self.continue_button = Button(master, text='Continue', command=master.quit)
        self.continue_button.pack(pady=10)


##----------------------------------------------------------------------
## WINDOW 3: ENTER MODEL PARAMETERS







##----------------------------------------------------------------------
## WINDOW 4: ENTER API COGS








##----------------------------------------------------------------------
## WINDOW 5: ENTER FINANCIAL ASSUMPTIONS

