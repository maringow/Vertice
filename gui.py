import __main__
from tkinter import *
from tkinter import ttk

##----------------------------------------------------------------------
## WINDOW 1: SELECT BRAND NAME


class BrandSelectionWindow:
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


class ConfirmBrandWindow:

    def __init__(self, master, brand_name, combined_molecules, dosage_forms, count_TEs):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Review Therapeutic Equivalents')
        self.title.pack(pady=10)

        # create label for brand selection and number of equivalents found
        self.selection_label = Label(master, text='{} therapeutically equivalent NDCs found in IMS for brand {}'
                                .format(count_TEs, brand_name))
        self.selection_label.pack(pady=10)

        # create labels for molecule and dosage form used

        self.molecules_label = Label(master, text='Molecules searched: {}'.format(combined_molecules))
        self.molecules_label.pack(pady=10)

        self.dosage_forms_label = Label(master, text='Dosage forms searched: {}'.format(dosage_forms))
        self.dosage_forms_label.pack()


        # add Finish button
        self.continue_button = Button(master, text='Continue', command=master.quit)
        self.continue_button.pack(pady=10)


##----------------------------------------------------------------------
## WINDOW 3: ENTER MODEL PARAMETERS







##----------------------------------------------------------------------
## WINDOW 4: ENTER API COGS








##----------------------------------------------------------------------
## WINDOW 5: ENTER FINANCIAL ASSUMPTIONS

