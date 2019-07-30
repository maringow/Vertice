from tkinter import *
from tkinter import ttk
import tkinter.tix as tix
from tkinter import filedialog
import pandas as pd
import numpy as np

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
        self.brand_combo = ttk.Combobox(master, values=brands, width=30, height=15)  # 15 rows to display
        self.brand_combo.pack()
        self.brand_combo.bind("<<ComboboxSelected>>", self.get_brand)

        self.or_label = Label(master, text='OR', font='Helvetica 10 bold')
        self.or_label.pack(pady=10)

        # add label and combobox for molecule selection
        self.molecule_label = Label(master, text='Select a molecule: ')
        self.molecule_label.pack()
        self.molecule_combo = ttk.Combobox(master, values=molecules, width=30, height=15)
        self.molecule_combo.pack()
        self.molecule_combo.bind("<<ComboboxSelected>>", self.get_molecule)

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
            v = IntVar()
            box = Checkbutton(self.master, text=self.dosage_forms[d], variable=v)
            box.pack()
            self.var.append(v)

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
## WINDOW: SELECT NDCS V2
class SelectNDCs():

    def __init__(self, master, df_merged_data):

        self.master = master
        master.title("Generics Forecasting Model")
        # master.geometry("600x400")

        self.title = Label(master, text='Generics Forecasting Model: Select NDCs', font='Helvetica 9 bold')
        self.title.grid(row=0, columnspan=2, pady=20, padx=20)

        self.outer_frame = Frame(master)
        self.outer_frame.grid(row=1, column=0, columnspan=2)
        self.outer_frame.rowconfigure(0, weight=1)
        self.outer_frame.columnconfigure(0, weight=1)

        self.canvas = Canvas(self.outer_frame, width=900)
        self.canvas.grid(sticky="nsew", padx=40)

        self.inner_frame = Frame(self.canvas)
        self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        # set up variables to store user selections
        self.ndcs = df_merged_data.sort_values(by=['Manufacturer', 'NDC'])[
            ['NDC', 'Manufacturer', 'Prod Form3', '2018_Units', '2019_Units', 'WACPrice', 'Pack']].reset_index(
            drop=True)
        self.ndcs = self.ndcs.drop_duplicates().reset_index()
        print('df_merged_data', df_merged_data)
        print('self.ndcs', self.ndcs)
        self.selected_ndcs = pd.DataFrame()
        self.var = []

        m = 0

        header = ['NDC', 'Manufacturer', 'Dosage Form', '2018 Volume', '2019 Volume', 'WAC Price ($)', 'Pack']
        for h in header:
            label = Label(self.inner_frame, text=h, font='Helvetica 8 bold')
            label.grid(row=0, column=m, padx=8)
            m += 1

        n = 1

        # ndc checkboxes
        for index, row in self.ndcs.iterrows():
            v = IntVar()
            if row['2019_Units'] != row['2019_Units']:  # if nan
                v.set(0)
            else:
                v.set(1)
            box = Checkbutton(self.inner_frame, text=row['NDC'], variable=v)
            box.grid(row=n, column=0, sticky='w', padx=2)
            self.var.append(v)
            self.manufacturer_label = Label(self.inner_frame, text=row['Manufacturer'])
            self.manufacturer_label.grid(row=n, column=1, sticky='w', padx=8)
            self.form_label = Label(self.inner_frame, text=row['Prod Form3'])
            self.form_label.grid(row=n, column=2, sticky='w', padx=8)
            self.units_2018 = Label(self.inner_frame, text=row['2018_Units'])
            self.units_2018.grid(row=n, column=3, sticky='w', padx=8)
            self.units_2019 = Label(self.inner_frame, text=row['2019_Units'])
            self.units_2019.grid(row=n, column=4, sticky='w', padx=8)
            self.wacprice = Label(self.inner_frame, text=row['WACPrice'])
            self.wacprice.grid(row=n, column=5, sticky='w', padx=8)
            self.addt_spacing = Label(self.inner_frame, text=row['Pack'])
            self.addt_spacing.grid(row=n, column=6, sticky='w', padx=8)
            n += 1

        self.scroll = Scrollbar(self.outer_frame, orient=VERTICAL)
        self.scroll.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.scroll.set)
        self.scroll.grid(row=0, sticky="nse")

        self.inner_frame.bind("<Configure>", self.update_scrollregion)

        self.continue_button = Button(master, text='Continue', command=self.save_and_continue)
        self.continue_button.grid(row=1000, column=1, pady=20, padx=20, sticky='e')

    def save_and_continue(self):
        print(self.var)
        print(self.ndcs['NDC'])
        self.selected_ndcs = [self.ndcs['NDC'][i] for i in range(len(self.ndcs))
                              if self.var[i].get() == 1]
        self.master.destroy()

    def update_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

##----------------------------------------------------------------------
## WINDOW: ENTER EXCEL FILEPATH
class EnterFilepath:
    parameters = {}

    def __init__(self, master):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Set File Path and Run Tag',
                           font='Helvetica 9 bold')
        self.title.pack(pady=10)

        # add entry for filepath and populate
        self.filename = filedialog.askopenfilename(initialdir="C:\\Users\\",  # TODO update this
                                                   title="Select Model Input file",
                                                   filetypes=(("excel files", "*.xlsx"), ("all files", "*.*")))
        self.filepath_label = Label(master, text='Enter filepath for Excel parameters:')
        self.filepath_label.pack(pady=10)
        self.filepath_entry = Entry(master, width=75)
        self.filepath_entry.insert(END, "Model Inputs.xlsx")
        self.filepath_entry.pack()

        # add entry for run name
        self.run_name_label = Label(master, text='Enter a run tag (optional):')
        self.run_name_label.pack(pady=10)
        self.run_name_entry = Entry(master, width=50)
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

        self.title = Label(master, text='Enter Gross Margin', font='Helvetica 9 bold')  # margin before Distribution, Write-offs, Profit Share, and Milestone Payments
        self.title.grid(row=0, columnspan=2, pady=10)

        # if user uses straight gross margin approach, instead of API approach
        self.gross_margin_label = Label(master, text='Gross margin assumption (as decimal): ')
        self.gross_margin_label.grid(row=1, column=0, sticky='e')
        self.gross_margin_entry = Entry(master)
        self.gross_margin_entry.grid(row=1, column=1, sticky='w')

        self.sep1 = ttk.Separator(master, orient="horizontal")
        self.sep1.grid(column=0, row=2, columnspan=2, sticky="ew")
        self.sty = ttk.Style(master)
        self.sty.configure("TSeparator", background="blue")

        self.or_label = Label(master, text='OR', font='Helvetica 9 bold')
        self.or_label.grid(row=2, columnspan=2, pady=10, padx=10)
        self.subtitle = Label(master, text="Enter Standard API Cost", font='Helvetica 9 bold')
        self.subtitle.grid(row=3, columnspan=2, pady=10, padx=10)

        # add entry boxes for desired units and API cost per unit
        self.standard_cogs_label = Label(master, text='Standard API Cost ($): ')
        self.standard_cogs_label.grid(row=4, column=0, sticky='e')
        self.standard_cogs_entry = Entry(master)
        self.standard_cogs_entry.grid(row=4, column=1, sticky='w')

        self.sep2 = ttk.Separator(master, orient="horizontal")
        self.sep2.grid(column=0, row=5, columnspan=2, sticky="ew")

        self.or_label = Label(master, text='OR', font='Helvetica 9 bold')
        self.or_label.grid(row=5, columnspan=2, pady=10, padx=10)
        self.subtitle = Label(master, text='Enter API Cost Per Unit', font='Helvetica 9 bold')
        self.subtitle.grid(row=6, columnspan=2, pady=10, padx=10)

        self.unit_label = Label(master, text='Base unit: ')
        self.unit_label.grid(row=7, column=0, sticky='e')
        self.unit_entry = Entry(master)
        self.unit_entry.grid(row=7, column=1, sticky='w')

        self.cost_per_unit_label = Label(master, text='API cost per unit ($): ')
        self.cost_per_unit_label.grid(row=8, column=0, sticky='e')
        self.cost_per_unit_entry = Entry(master)
        self.cost_per_unit_entry.grid(row=8, column=1, sticky='w')

        # add entry boxes for API units for each pack type found in therapeutic equivalents
        self.API_costs_label = Label(master, text='Enter number of units for each pack type found: ')
        self.API_costs_label.grid(row=9, columnspan=2, pady=10)

        self.entries = []  # save entries created in list so that they can be accessed to store values
        i = 0  # start placing labels below the already assigned rows

        self.outer_frame = Frame(master)
        self.outer_frame.grid(row=10, column=0, columnspan=2)
        self.outer_frame.rowconfigure(0, weight=1)
        self.outer_frame.columnconfigure(0, weight=1)

        self.canvas = Canvas(self.outer_frame, height=100)
        self.canvas.grid(sticky="nsew")

        self.inner_frame = Frame(self.canvas)
        self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        self.packs = df_equivalents['Pack'].unique()
        for p in self.packs:
            pack_label = Label(self.inner_frame, text=p)
            pack_label.grid(row=i, column=1, padx=5, sticky='e')
            pack_entry = Entry(self.inner_frame)
            pack_entry.grid(row=i, column=2, padx=5, sticky='e')
            self.entries.append(pack_entry)
            i += 1

        self.scroll = Scrollbar(self.outer_frame, orient=VERTICAL)
        self.scroll.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.scroll.set)
        self.scroll.grid(row=0, sticky="nse")

        self.inner_frame.bind("<Configure>", self.update_scrollregion)

        run_model_button = Button(master, text='Run Model', command=self.save_and_run)
        run_model_button.grid(row=11, column=1, pady=10)

    def save_and_run(self):
        self.COGS['gm_override'] = self.gross_margin_entry.get()
        self.COGS['standard_cogs_entry'] = self.standard_cogs_entry.get()
        self.COGS['units'] = self.unit_entry.get()
        self.COGS['cost_per_unit'] = self.cost_per_unit_entry.get()
        self.COGS['units_per_pack'] = {}
        j = 0
        for e in self.entries:
            self.COGS['units_per_pack'][self.packs[j]] = e.get()
            j += 1
        self.master.destroy()

    def update_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

##----------------------------------------------------------------------
## WINDOW: PRINT RESULTS
class ShowResults:

    def __init__(self, master, parameters):
        self.master = master
        master.title('Generics Forecasting Model')
        master.geometry("500x300")

        self.title = Label(master, text='Generics Forecasting Model: Results Summary', font='Helvetica 9 bold')
        self.title.pack(pady=10)

        self.unit_label = Label(master, text='NPV: ${} million'.format(parameters['npv']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='IRR: {}%'.format(parameters['irr']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='Payback: {} years'.format(parameters['payback']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='Exit value in 2021: ${} million'.format(parameters['exit_value']))
        self.unit_label.pack()
        self.unit_label = Label(master, text='MOIC in 2021: {}x'.format(parameters['moic']))
        self.unit_label.pack()

        run_model_button = Button(master, text='Run Parameter Scan', command=master.destroy)
        run_model_button.pack(pady=20)

        def stop_model():
            import sys
            sys.exit()

        stop_model_button = Button(master, text='Cancel Parameter Scan', command=stop_model)
        stop_model_button.pack()

##----------------------------------------------------------------------
## WINDOW: PRINT RESULTS
class SuccessfulRun:

    def __init__(self, master):
        self.master = master
        master.title('')
        master.geometry("300x150")

        self.title = Label(master, text='Generics Forecasting Model: Successful Model Run', font='Helvetica 9 bold')
        self.title.pack(pady=10)
        self.title = Label(master, text='Parameter scan complete.', font='Helvetica 9')
        self.title.pack(pady=10)
        self.title = Label(master, text='Results saved to the database.', font='Helvetica 9')
        self.title.pack(pady=10)

        run_model_button = Button(master, text='Finish', command=master.destroy)
        run_model_button.pack(pady=20)

##----------------------------------------------------------------------
## WINDOW: PRINT DETAILED RESULTS
class ShowDetailedResults():

    def __init__(self, master, parameters, df_gfm):
        self.master = master
        master.title('Generics Forecasting Model')
        # master.geometry("600x400")

        Label(master, text='Generics Forecasting Model: Results Summary',
              font='Helvetica 9 bold').grid(row=0, column=0, sticky=N, columnspan=12)
        Label(master, text='Did not opt to do the parameter scan. No results saved to the database.',
              font='Helvetica 9').grid(row=1, column=0, sticky=N, columnspan=12)

        Label(master, text='').grid(row=2, rowspan=2)

        if parameters['search_type'] == 'brand':
            search_type = 'Brand Name'
            drug_id = parameters['brand_name']
        else:
            search_type = 'Molecule'
            drug_id = parameters['molecule_name']

        Label(master, text='{}:  '.format(search_type), font='Helvetica 9 bold').grid(row=4, column=0, sticky=E,columnspan=6)
        Label(master, text='NPV:  ', font='Helvetica 9 bold').grid(row=5, column=0, sticky=E, columnspan=6)
        Label(master, text='IRR:  ', font='Helvetica 9 bold').grid(row=6, column=0, sticky=E, columnspan=6)
        Label(master, text='Payback:  ', font='Helvetica 9 bold').grid(row=7, column=0, sticky=E, columnspan=6)
        Label(master, text='Exit value in 2021:  ', font='Helvetica 9 bold').grid(row=8, column=0, sticky=E,columnspan=6)
        Label(master, text='MOIC in 2021:  ', font='Helvetica 9 bold').grid(row=9, column=0, sticky=E, columnspan=6)

        Label(master, text='{}'.format(drug_id)).grid(row=4, column=6, sticky=W, columnspan=6)
        Label(master, text='${} million'.format(parameters['npv'])).grid(row=5, column=6, sticky=W, columnspan=6)
        Label(master, text='{}%'.format(parameters['irr'])).grid(row=6, column=6, sticky=W, columnspan=6)
        Label(master, text='{} years'.format(parameters['payback'])).grid(row=7, column=6, sticky=W, columnspan=6)
        Label(master, text='${} million'.format(parameters['exit_value'])).grid(row=8, column=6, sticky=W, columnspan=6)
        Label(master, text='{}x'.format(parameters['moic'])).grid(row=9, column=6, sticky=W, columnspan=6)

        Label(master, text='').grid(row=10, columnspan=12)

        Label(master, text="($m)", font='Helvetica 9').grid(row=11, column=0)
        Label(master, text="Net Sales", font='Helvetica 9 bold').grid(row=12, column=0)
        Label(master, text="COGS", font='Helvetica 9 bold').grid(row=13, column=0)
        Label(master, text="EBIT", font='Helvetica 9 bold').grid(row=14, column=0)
        Label(master, text="FCF", font='Helvetica 9 bold').grid(row=15, column=0)

        c = 1
        for i in range(parameters['present_year'], parameters['present_year'] + 11):
            Label(master, text=i, font='Helvetica 9 bold').grid(row=11, column=c)
            c = c + 1

        df = round(df_gfm[['Net Sales', 'COGS', 'EBIT', 'FCF']].loc[parameters['present_year']:].transpose(), 2)

        r = 12
        for x in ['Net Sales', 'COGS', 'EBIT', 'FCF']:
            c = 1
            for y in range(parameters['present_year'], parameters['present_year'] + 11):
                Label(master, text=df[y].loc[x], font='Helvetica 9').grid(row=r, column=c)
                c = c + 1
            r = r + 1

        Label(master, text='').grid(row=16, rowspan=2)
        Button(master, text='Finish', command=master.destroy).grid(row=16, columnspan=12, pady=10)