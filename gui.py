from tkinter import *
from tkinter import ttk
import tkinter.tix as tix

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
        self.title = Label(master, text='Generics Forecasting Model: Select Dosage Forms', font='Helvetica 9 bold')
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

# TODO make a function for label creation & packing

class ConfirmBrand:

    def __init__(self, master, parameters, df_detail):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Review Therapeutic Equivalents',
                           font='Helvetica 9 bold')
        self.title.pack(pady=10)

        # create label for brand selection and number of equivalents found
        if parameters['search_type'] == 'brand':
            self.selection_label = Label(master, text='{} therapeutically equivalent NDCs found in IMS for brand {}'
                                    .format(parameters['count_eqs'], parameters['brand_name']))
            self.selection_label.pack(pady=20)
        elif parameters['search_type'] == 'molecule':
            self.selection_label = Label(master, text='{} therapeutically equivalent NDCs found in IMS for molecule {}'
                                    .format(parameters['count_eqs'], parameters['molecule_name']))
            self.selection_label.pack(pady=20)

        # create labels for molecule and dosage form used
        self.combined_molecules = parameters['combined_molecules']
        self.molecules_label = Label(master, text='Molecules searched: {}'.format(self.combined_molecules))
        self.molecules_label.pack()

        self.dosage_forms = parameters['dosage_forms']
        self.dosage_forms_label = Label(master, text='Dosage forms searched: {}'.format(self.dosage_forms))
        self.dosage_forms_label.pack()

        # create label for number of competitors found
        # self.competitors_label = Label(master, text='Number of active competitors found (sales in 2018): {}'.
        #                                format(parameters['count_competitors']))
        # self.competitors_label.pack()

        # create label for 2-year growth rate
        # self.growth_label = Label(master, text='Two-year market volume growth rate (CAGR) for molecule: {}'
        #                           .format(round(parameters['historical_growth_rate'],2)))
        # self.growth_label.pack()

        # print df_merged_data
        # self.volumes_label = Label(master, text='2016 volume: {:,}; 2017 volume: {:,}; 2018 volume: {:,}; 2019 volume: {:,}'.format(
        #                         int(df_detail['Units'].sum(level='year_index').loc[2016]),
        #                         int(df_detail['Units'].sum(level='year_index').loc[2017]),
        #                         int(df_detail['Units'].sum(level='year_index').loc[2018]),
        #                         int(df_detail['Units'].sum(level='year_index').loc[2019])))
        # self.volumes_label.pack()

        # add Continue button
        self.continue_button = Button(master, text='Continue', command=master.destroy)
        self.continue_button.pack(pady=10)


##----------------------------------------------------------------------
## WINDOW: SELECT NDCS

class SelectNDCs():

    def __init__(self, master, df_merged_data, df_detail):

        self.master = master
        master.title("Generics Forecasting Model")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Select NDCs', font='Helvetica 9 bold')
        self.title.grid(row=0, columnspan=2, pady=20, padx=20)

        # create canvas and scrollbar
        self.canvas = Canvas(master, borderwidth=2, scrollregion=(0,0,500,500))
        self.canvas.grid(row=1, columnspan=2)
        self.scrollbar = Scrollbar(master, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, rowspan=100, column=3)
        #self.scrollbar.pack(side='right')


        # create frame to lay out objects within the canvas
        self.frame = Frame(self.canvas, borderwidth=2)
        self.frame.grid(row=0, columnspan=2)

        # set up variables to store user selections
        self.ndcs = df_merged_data.sort_values(by=['Manufacturer', 'NDC'])['NDC']
        print(self.ndcs)
        self.selected_ndcs = []
        self.var = []

        m = 0
        header = ['NDC', 'Manufacturer', 'Dosage Form']
        for h in header:
            label = Label(self.frame,text=h, font='Helvetica 8 bold')
            label.grid(row=0, column=m, padx=4)
            m+=1

        n = 1

        # add ndc checkboxes
        for index, row in df_merged_data.sort_values(by=['Manufacturer', 'NDC']).iterrows():
            v=IntVar()
            v.set(1)
            box = Checkbutton(self.frame, text=row['NDC'], variable=v)
            box.grid(row=n, column=0, sticky='w', padx=2)
            self.var.append(v)
            self.manufacturer_label = Label(self.frame, text=row['Manufacturer'])
            self.manufacturer_label.grid(row=n, column=1, sticky='w', padx=2)
            self.form_label = Label(self.frame, text=row['Prod Form3'])
            self.form_label.grid(row=n, column=2, sticky='w', padx=2)
            n+=1

        self.canvas.create_window((0,0), anchor='nw', window=self.frame, tags='self.frame')
        self.frame.bind('<Configure>', self.onFrameConfigure)

        # add Continue button
        self.continue_button = Button(master, text='Continue', command=self.save_and_continue)
        self.continue_button.grid(row=1000, column=1, pady=20, padx=20, sticky='e')

    def onFrameConfigure(self, event):
        '''Reset scroll region to encompass inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def save_and_continue(self):
        print(self.ndcs)
        self.selected_ndcs = [self.ndcs[i] for i in range(len(self.ndcs))
                                      if self.var[i].get() == 1]
        self.master.destroy()

##----------------------------------------------------------------------
## WINDOW: ENTER EXCEL FILEPATH

class EnterFilepath:

    parameters = {}

    def __init__(self, master):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Set Filepath and Run Tag', font='Helvetica 9 bold')
        self.title.pack(pady=10)

        # add entry for filepath and populate
        self.filepath_label = Label(master, text='Enter filepath for Excel parameters:')
        self.filepath_label.pack(pady=10)
        self.filepath_entry = Entry(master)
        self.filepath_entry.insert(END, 'Model Inputs Demo.xlsx')
        self.filepath_entry.pack()

        # add entry for run name
        self.run_name_label = Label(master, text='Enter a run tag (optional):')
        self.run_name_label.pack(pady=10)
        self.run_name_entry = Entry(master)
        self.run_name_entry.pack()

        # add Save and Continue button
        self.continue_button = Button(master, text='Continue', command=self.save_and_continue)
        self.continue_button.pack(pady=10)

    def save_and_continue(self):
        self.parameters['excel_filepath'] = self.filepath_entry.get()
        self.parameters['run_name'] = self.run_name_entry.get()

        self.master.destroy()


##----------------------------------------------------------------------
## WINDOW: ENTER API COGS

class EnterCOGS:

    COGS = {}

    def __init__(self, master, df_equivalents):

        self.master = master
        master.title('Generics Forecasting Model')

        self.title = Label(master, text='Enter Standard Margin', font='Helvetica 9 bold')
        self.title.grid(row=0, columnspan=2, pady=10)

        #if user uses straight gross margin approach, instead of API approach
        self.gross_margin = Label(master, text='Enter gross margin assumption (as decimal):')
        self.gross_margin.grid(row=1, column=0, padx=10)
        self.gross_margin = Entry(master)
        self.gross_margin.grid(row=1, column=1, padx=10)

        self.sep1 = ttk.Separator(master, orient="horizontal")
        self.sep1.grid(column=0, row=2, columnspan=2, sticky="ew")
        self.sty = ttk.Style(master)
        self.sty.configure("TSeparator", background="blue")

        self.or_label = Label(master, text='OR', font='Helvetica 9 bold')
        self.or_label.grid(row=2, columnspan=2, pady=10, padx=10)
        self.subtitle = Label(master, text="Enter Standard COGS", font='Helvetica 9 bold') # TODO make sure this is COGS, not API COGS
        self.subtitle.grid(row=3, columnspan=2, pady=10, padx=10)

        # add entry boxes for desired units and API cost per unit
        self.standard_cogs_label = Label(master, text='Standard COGS ($): ')
        self.standard_cogs_label.grid(row=4, column=0, padx=10)
        self.standard_cogs_entry = Entry(master)
        self.standard_cogs_entry.grid(row=4, column=1, padx=10)

        self.sep2 = ttk.Separator(master, orient="horizontal")
        self.sep2.grid(column=0, row=5, columnspan=2, sticky="ew")
        # self.sty = ttk.Style(master)
        # self.sty.configure("TSeparator", background="red")

        self.or_label = Label(master, text='OR', font='Helvetica 9 bold')
        self.or_label.grid(row=5, columnspan=2, pady=20, padx=10)
        self.subtitle = Label(master, text='Enter API Cost Per Unit', font='Helvetica 9 bold')
        self.subtitle.grid(row=6, columnspan=2, pady=10, padx=10)

        self.unit_label = Label(master, text='Base unit: ')
        self.unit_label.grid(row=7, column=0)
        self.unit_entry = Entry(master)
        self.unit_entry.grid(row=7, column=1)

        self.cost_per_unit_label = Label(master, text='API cost per unit ($): ')
        self.cost_per_unit_label.grid(row=8, column=0)
        self.cost_per_unit_entry = Entry(master)
        self.cost_per_unit_entry.grid(row=8, column=1)

        # add entry boxes for API units for each pack type found in therapeutic equivalents
        self.API_costs_label = Label(master, text='Enter number of units for each pack type found: ')
        self.API_costs_label.grid(row=9, columnspan=2, pady=20)

        self.entries = []  # save entries created in list so that they can be accessed to store values
        i = 0  # start placing labels below the already assigned rows

        # add frame to allow scrolling
        #self.canvas = Canvas()
        # self.canvas.grid()
        self.frame = Frame(master)
        self.frame.grid(row=10, columnspan=2)

        # add scrollbar
        #self.scroll = Scrollbar(master, orient='vertical')
        #self.scroll.grid(column=3, sticky='ns')

        self.packs = df_equivalents['Pack'].unique()
        for p in self.packs:
            pack_label = Label(self.frame, text=p)
            pack_label.grid(row=i, column=0, padx=10)
            pack_entry = Entry(self.frame)
            pack_entry.grid(row=i, column=1, padx=10)
            self.entries.append(pack_entry)
            i += 1

        # add Run Model button
        run_model_button = Button(master, text='Run Model', command=self.save_and_run)
        run_model_button.grid(row=11, column=1, pady=10)

    def save_and_run(self):
        self.COGS['gm_override'] = self.gross_margin.get()
        self.COGS['standard_cogs_entry'] = self.standard_cogs_entry.get()
        self.COGS['units'] = self.unit_entry.get()
        self.COGS['cost_per_unit'] = self.cost_per_unit_entry.get()
        self.COGS['units_per_pack'] = {}
        j = 0
        for e in self.entries:
            self.COGS['units_per_pack'][self.packs[j]] = e.get()
            j += 1
        self.master.destroy()



##----------------------------------------------------------------------
## WINDOW: PRINT RESULTS

class ShowResults:

    def __init__(self, master, parameters):

        self.master = master
        master.title('Generics Forecasting Model')
        master.geometry("600x400")

        self.title = Label(master, text='Generics Forecasting Model: Results Summary', font='Helvetica 9 bold')
        self.title.pack(pady=10)

        # add labels for financial results
        self.unit_label = Label(master, text='NPV: ${} million'.format(parameters['npv']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='IRR: {}%'.format(parameters['irr']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='Payback: {} years'.format(parameters['payback']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='Exit value: ${} million'.format(parameters['exit_value']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='MOIC: {}x'.format(parameters['moic']))
        self.unit_label.pack()

        # add Finish button
        run_model_button = Button(master, text='Finish', command=master.destroy)
        run_model_button.pack(pady=20)