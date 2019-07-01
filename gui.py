from tkinter import *
from tkinter import ttk



##----------------------------------------------------------------------
## WINDOW 1: SELECT BRAND NAME


class BrandSelectionWindow:

    w1_parameters = {}

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

        # add Continue button
        self.continue_button = Button(master, text='Continue', command=master.destroy)
        self.continue_button.pack(pady=10)

    # function to collect field entries and store as variables
    def collect_entry_fields(self, event):

        self.w1_parameters['brand_name'] = self.brand_combo.get()
        print(self.w1_parameters['brand_name'])



##----------------------------------------------------------------------
## WINDOW 2: CONFIRM BRAND


class ConfirmBrandWindow:

    def __init__(self, master, parameters):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Review Therapeutic Equivalents')
        self.title.pack(pady=10)

        # create label for brand selection and number of equivalents found
        self.selection_label = Label(master, text='{} therapeutically equivalent NDCs found in IMS for brand {}'
                                .format(parameters['count_eqs'], parameters['brand_name']))
        self.selection_label.pack(pady=10)

        # create labels for molecule and dosage form used

        self.molecules_label = Label(master, text='Molecules searched: {}'.format(parameters['combined_molecules']))
        self.molecules_label.pack(pady=10)

        self.dosage_forms_label = Label(master, text='Dosage forms searched: {}'.format(parameters['dosage_forms']))
        self.dosage_forms_label.pack()


        # add Continue button
        self.continue_button = Button(master, text='Continue', command=master.destroy)
        self.continue_button.pack(pady=10)


##----------------------------------------------------------------------
## WINDOW 3: ENTER MODEL PARAMETERS

class EnterParameters:

    w3_parameters = {}

    def __init__(self, master, parameters):
        self.master = master
        master.title("Generics Forecasting Model")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Enter Model Parameters')
        self.title.pack(pady=10)

        # add entries for variables
        self.growth_rate_label = Label(master, text='Enter expected volume growth rate: ')
        self.growth_rate_label.pack(pady=10)
        self.growth_rate_entry = Entry(master)
        self.growth_rate_entry.pack()

        # add Save and Continue button
        self.continue_button = Button(master, text='Continue', command=self.save_and_continue)
        self.continue_button.pack(pady=10)

    def save_and_continue(self):
        self.w3_parameters['growth_rate'] = self.growth_rate_entry.get()
        self.master.destroy()


##----------------------------------------------------------------------
## WINDOW 4: ENTER API COGS

# TODO change pack to grid for better formatting

class EnterCOGS:
    def __init__(self, master, df_equivalents):

        self.master = master
        master.title("Generics Forecasting Model")

        self.title = Label(master, text='Generics Forecasting Model: Enter API COGS')
        self.title.grid(pady=10)

        self.entries = []  # save entries created in list so that they can be accessed to store values

        # add entry boxes for desired units and API cost per unit
        self.unit_label = Label(master, text='Enter units: ')
        self.unit_label.grid(row=1, column=0)
        self.unit_entry = Entry(master)
        self.unit_entry.grid(row=1, column=1)
        self.entries.append(self.unit_entry)

        self.cost_per_unit_label = Label(master, text='Enter API cost per unit: ')
        self.cost_per_unit_label.grid(row=2, column=0)
        self.cost_per_unit_entry = Entry(master)
        self.cost_per_unit_entry.grid(row=2, column=1)
        self.entries.append(self.cost_per_unit_entry)


        # add entry boxes for API units for each pack type found in therapeutic equivalents
        self.API_costs_label = Label(master, text="Enter number of units for each pack type found: ")
        self.API_costs_label.grid(row=3, columnspan=2, pady=10)

        i = 4  # start placing labels below the already assigned rows

        self.packs = df_equivalents['Pack'].unique()
        for p in self.packs:
            pack_label = Label(master, text=p)
            pack_label.grid(row=i, column=0)
            pack_entry = Entry(master)
            pack_entry.grid(row=i, column=1)
            self.entries.append(pack_entry)
            i += 1

        # add Run Model button
        run_model_button = Button(master, text='Run Model', command=self.save_and_run)
        run_model_button.grid(row=i+1, column=1, pady=10)

    def save_and_run(self):
        j = 0
        for e in self.entries:
            print(e.get())
            j += 1
        self.master.destroy()




##----------------------------------------------------------------------
## WINDOW 5: ENTER FINANCIAL ASSUMPTIONS

