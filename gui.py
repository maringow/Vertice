from tkinter import *
from tkinter import ttk


##----------------------------------------------------------------------
## WINDOW: SELECT BRAND NAME

class BrandSelection:

    w1_parameters = {}

    def __init__(self, master, brands, molecules):

        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Brand Selection', font='Helvetica 9 bold')
        self.title.pack(pady=10)

        # add label and combobox for brand selection
        self.brand_label = Label(master, text='Select a brand name drug: ')
        self.brand_label.pack()
        self.brand_combo = ttk.Combobox(master, values=brands)
        self.brand_combo.pack()
        self.brand_combo.bind("<<ComboboxSelected>>", self.get_brand)

        self.or_label = Label(master, text='OR', font='Helvetica 10 bold')
        self.or_label.pack(pady=10)

        # add label and combobox for molecule selection
        self.molecule_label = Label(master, text='Select a molecule: ')
        self.molecule_label.pack()
        self.molecule_combo = ttk.Combobox(master, values=molecules)
        self.molecule_combo.pack()
        self.molecule_combo.bind("<<ComboboxSelected>>", self.get_molecule)

        # add Continue button
        self.continue_button = Button(master, text='Continue', command=master.destroy)
        self.continue_button.pack(pady=10)

    def get_brand(self, event):

        self.w1_parameters['search_type'] = 'brand'
        self.w1_parameters['brand_name'] = self.brand_combo.get()
        print(self.w1_parameters['brand_name'])

    def get_molecule(self, event):

        self.w1_parameters['search_type'] = 'molecule'
        self.w1_parameters['molecule_name'] = self.molecule_combo.get()
        print(self.w1_parameters['molecule_name'])


##----------------------------------------------------------------------
## WINDOW: SELECT DOSAGE FORMS


class DosageForms:

    def __init__(self, master, dosage_forms):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Select Dosage Forms')
        self.title.pack(pady=10)

        self.dosage_forms = dosage_forms
        self.selected_dosage_forms = []
        self.var = []

        # add dosage form checkboxes
        for d in range(len(self.dosage_forms)):
            v=IntVar()
            box = Checkbutton(self.master, text=self.dosage_forms[d], variable=v)
            box.pack()
            self.var.append(v)

        # add Continue button
        self.continue_button = Button(master, text='Continue', command=self.save_and_continue)
        self.continue_button.pack(pady=10)

    def save_and_continue(self):
        # for each checked box, save the dosage form into selected_dosage_forms
        self.selected_dosage_forms = [self.dosage_forms[i] for i in range(len(self.dosage_forms))
                                      if self.var[i].get() == 1]
        self.master.destroy()

##----------------------------------------------------------------------
## WINDOW: CONFIRM BRAND


class ConfirmBrand:

    def __init__(self, master, parameters):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Review Therapeutic Equivalents')
        self.title.pack(pady=10)


        # create label for brand selection and number of equivalents found
        if parameters['search_type'] == 'brand':
            self.selection_label = Label(master, text='{} therapeutically equivalent NDCs found in IMS for brand {}'
                                    .format(parameters['count_eqs'], parameters['brand_name']))
            self.selection_label.pack(pady=10)
        elif parameters['search_type'] == 'molecule':
            self.selection_label = Label(master, text='{} therapeutically equivalent NDCs found in IMS for molecule {}'
                                    .format(parameters['count_eqs'], parameters['molecule_name']))
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
## WINDOW: ENTER EXCEL FILEPATH

class EnterFilepath:

    parameters = {}

    def __init__(self, master):
        self.master = master
        master.title("Generics Forecasting Model")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Set Excel Filepath')
        self.title.pack(pady=10)

        # add entries for variables
        self.filepath_label = Label(master, text='Enter filepath for Excel parameters: ')
        self.filepath_label.pack(pady=10)
        self.filepath_entry = Entry(master)
        self.filepath_entry.pack()

        # add Save and Continue button
        self.continue_button = Button(master, text='Run Model', command=self.save_and_continue)
        self.continue_button.pack(pady=10)

    def save_and_continue(self):
        self.parameters['excel_filepath'] = self.filepath_entry.get()
        self.master.destroy()


##----------------------------------------------------------------------
## WINDOW: ENTER API COGS

class EnterCOGS:

    COGS = {}

    def __init__(self, master, df_equivalents):

        self.master = master
        master.title('Generics Forecasting Model')

        self.title = Label(master, text='Generics Forecasting Model: Enter API COGS')
        self.title.grid(pady=10)

        # add entry boxes for desired units and API cost per unit
        self.unit_label = Label(master, text='Enter base unit: ')
        self.unit_label.grid(row=1, column=0)
        self.unit_entry = Entry(master)
        self.unit_entry.grid(row=1, column=1)

        self.cost_per_unit_label = Label(master, text='Enter API cost per unit ($): ')
        self.cost_per_unit_label.grid(row=2, column=0)
        self.cost_per_unit_entry = Entry(master)
        self.cost_per_unit_entry.grid(row=2, column=1)

        # add entry boxes for API units for each pack type found in therapeutic equivalents
        self.API_costs_label = Label(master, text='Enter number of units for each pack type found: ')
        self.API_costs_label.grid(row=3, columnspan=2, pady=10)

        self.entries = []  # save entries created in list so that they can be accessed to store values
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
        run_model_button = Button(master, text='Continue', command=self.save_and_run)
        run_model_button.grid(row=i+1, column=1, pady=10)

    def save_and_run(self):
        self.COGS['units'] = self.unit_entry.get()
        self.COGS['cost_per_unit'] = self.cost_per_unit_entry.get()
        self.COGS['units_per_pack'] = {}
        j = 0
        for e in self.entries:
            self.COGS['units_per_pack'][self.packs[j]] = e.get()
            j += 1
        self.master.destroy()