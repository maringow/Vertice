import tkinter as tk
from tkinter import filedialog
import pandas as pd


class AutocompleteCombobox(tk.ttk.Combobox):
    """
    Modifying Tkinter Combobox to have ability to autocomplete. Used to select Brand or Molecule.
    Idea from: [stackoverflow link](https://stackoverflow.com/questions/12298159/tkinter-how-to-create-a-combo-box-with-autocompletion)

    """
    def set_completion_list(self, completion_list):
        """Use our completion list as our drop down selection menu, arrows move through menu."""
        self._completion_list = completion_list
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._completion_list  # Setup our popup menu

    def autocomplete(self):
        """
        Autocomplete the Combobox.

        """
        self.position = len(self.get())
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):  # match case insensitively
                _hits.append(element)
        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = self._hit_index % len(self._hits)
        # now finally perform the auto completion
        if self._hits:
            self.delete(0, tk.END)
            self.insert(0, self._hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        """
        Event handler for the keyrelease event on this widget.
        e.g. pressing an arrow or deleting text.

        """
        if event.keysym == "BackSpace":
            self.delete(self.index(tk.INSERT), tk.END)
            self.position = self.index(tk.END)
        if event.keysym == "Left":
            if self.position < self.index(tk.END):  # delete the selection
                self.delete(self.position, tk.END)
            else:
                self.position = self.position - 1  # delete one character
                self.delete(self.position, tk.END)
        if event.keysym == "Right":
            self.position = self.index(tk.END)  # go to end (no selection)
        if len(event.keysym) == 1:
            self.autocomplete()


class BrandSelection:
    """
    GUI to select product based on brand name or molecule name.

    |    Brand Selection   |
    |:--------------------:|
    |   **Select brand:**  |
    |         -----        |
    |       Continue       |
    |          OR          |
    | **Select molecule:** |
    |         -----        |
    |       Continue       |

    """
    w1_parameters = {}

    def __init__(self, master, brands, molecules):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("400x350")

        ##############################################################
        # create window header
        ##############################################################
        tk.Label(master, text='Generics Forecasting Model: Brand Selection',
                 font='Helvetica 9 bold').pack(pady=10)

        ##############################################################
        # add label and combobox for brand selection
        ##############################################################
        tk.Label(master, text='Select a brand name drug: ').pack()
        self.brand_combo = AutocompleteCombobox(master)  # using combobox with autocomplete ability
        self.brand_combo.set_completion_list(brands)
        self.brand_combo.configure(width=30, height=15)  # show 15 rows
        self.brand_combo.pack()

        tk.Button(master, text='Continue with Brand', command=self.get_brand).pack(pady=10)

        tk.Label(master, text='OR', font='Helvetica 9 bold').pack(pady=20)

        ##############################################################
        # add label and combobox for molecule selection
        ##############################################################
        tk.Label(master, text='Select a molecule: ').pack()
        self.molecule_combo = AutocompleteCombobox(master)  # combobox with autocomplete ability
        self.molecule_combo.set_completion_list(molecules)
        self.molecule_combo.configure(width=30, height=15)
        self.molecule_combo.pack()

        tk.Button(master, text='Continue with Molecule', command=self.get_molecule).pack(pady=10)

    def get_brand(self):
        self.w1_parameters['search_type'] = 'brand'
        self.w1_parameters['brand_name'] = self.brand_combo.get()
        print(self.w1_parameters['brand_name'])
        self.master.destroy()

    def get_molecule(self):
        self.w1_parameters['search_type'] = 'molecule'
        self.w1_parameters['molecule_name'] = self.molecule_combo.get()
        print(self.w1_parameters['molecule_name'])
        self.master.destroy()


class DosageForms:
    """
    GUI to select dosage forms based on selected product.
    Only appears if there is more than one dosage form.

    |  Select Dosage Forms |
    |:--------------------:|
    |       ❑ form 1       |
    |       ❑ form n       |
    |       Continue       |

    """
    def __init__(self, master, dosage_forms):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("400x350")

        ##############################################################
        # create window header
        ##############################################################
        tk.Label(master, text='Generics Forecasting Model: Select Dosage Forms',
                 font='Helvetica 9 bold').pack(pady=10)

        self.dosage_forms = dosage_forms
        self.selected_dosage_forms = []
        self.var = []

        ##############################################################
        # add dosage form checkboxes
        ##############################################################
        for d in range(len(self.dosage_forms)):
            v = tk.IntVar()
            box = tk.Checkbutton(self.master, text=self.dosage_forms[d], variable=v)
            box.pack()
            self.var.append(v)

        tk.Button(master, text='Continue', command=self.save_and_continue).pack(pady=10)

    ##############################################################
    # for each checked box, save the dosage form into selected_dosage_forms
    ##############################################################
    def save_and_continue(self):
        self.selected_dosage_forms = [self.dosage_forms[i] for i in range(len(self.dosage_forms))
                                      if self.var[i].get() == 1]
        self.master.destroy()


class ConfirmBrand:
    """
    GUI that shows summary information of selected product.

    | Review Therapeutic EquivalentS |
    |:------------------------------:|
    |   n equivalents found for xyz  |
    |                                |
    |     Molecules searched: xyz    |
    | Dosage forms searched: form 1  |
    |            Continue            |

    """
    def __init__(self, master, parameters, df_detail):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        ##############################################################
        # create window header
        ##############################################################
        tk.Label(master, text='Generics Forecasting Model: Review Therapeutic Equivalents',
                 font='Helvetica 9 bold').pack(pady=10)

        ##############################################################
        # create label for brand selection and number of equivalents found
        ##############################################################
        if parameters['search_type'] == 'brand':
            tk.Label(master, text='{} therapeutically equivalent NDCs found in IMS for brand {}'
                     .format(parameters['count_eqs'], parameters['brand_name'])).pack(pady=20)
        elif parameters['search_type'] == 'molecule':
            tk.Label(master, text='{} therapeutically equivalent NDCs found in IMS for molecule {}'
                     .format(parameters['count_eqs'], parameters['molecule_name'])).pack(pady=20)

        ##############################################################
        # create labels for molecule and dosage form used
        ##############################################################
        self.combined_molecules = parameters['combined_molecules']
        tk.Label(master, text='Molecules searched: {}'.format(self.combined_molecules)).pack()

        self.dosage_forms = parameters['dosage_forms']
        tk.Label(master, text='Dosage forms searched: {}'.format(self.dosage_forms)).pack()

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

        tk.Button(master, text='Continue', command=master.destroy).pack(pady=10)


class SelectNDCs:
    """
    GUI that allows selection of NDCs to include in model.
    Shows information for each NDC in a table format to assist selection.

    | NDC | Manuf | Form | 2018 Volume | 2019 Volume | Price |   Pack   |
    |-----|-------|------|-------------|-------------|-------|----------|
    | ❑ x | x    | x    | x           | x           | x     | x        |
    | ❑ x | x    | x    | x           | x           | x     | x        |
    | ❑ x | x    | x    | x           | x           | x     | x        |
    | ❑ x | x    | x    | x           | x           | x     | x        |
    | ❑ x | x    | x    | x           | x           | x     | x        |
    |     |      |      |             |             |       | Continue |

    """
    def __init__(self, master, df_merged_data):

        self.master = master
        master.title("Generics Forecasting Model")
        # master.resizable(width=False, height=False)  # disable ability to resize window

        tk.Label(master, text='Generics Forecasting Model: Select NDCs',
                 font='Helvetica 9 bold').grid(row=0, columnspan=4, pady=20, padx=20)

        ##############################################################
        # set up to enable the scrollbar
        ##############################################################
        self.outer_frame = tk.Frame(master)
        self.outer_frame.grid(row=1, column=0, columnspan=4)
        self.outer_frame.rowconfigure(0, weight=1)
        self.outer_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.outer_frame, width=900)
        self.canvas.grid(sticky="nsew", padx=40)

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        ##############################################################
        # set up variables to store user selections
        ##############################################################
        self.ndcs = df_merged_data.sort_values(by=['Manufacturer', 'NDC'])[
            ['NDC', 'Manufacturer', 'Vertice Dosage Form', '2018_Units', '2019_Units', 'WACPrice', 'Pack']]\
            .reset_index(drop=True)
        self.ndcs = self.ndcs.drop_duplicates().reset_index()
        self.selected_ndcs = pd.DataFrame()
        self.var = []

        ##############################################################
        # set up columns to show
        ##############################################################
        m = 0
        header = ['NDC', 'Manufacturer', 'Dosage Form', '2018 Volume', '2019 Volume',
                  'WAC Price ($)', 'Pack']
        for h in header:
            tk.Label(self.inner_frame, text=h,
                     font='Helvetica 8 bold').grid(row=0, column=m, padx=8)
            m += 1

        ##############################################################
        # ndc checkboxes
        ##############################################################
        n = 1
        for index, row in self.ndcs.iterrows():
            v = tk.IntVar()
            if row['2019_Units'] != row['2019_Units']:  # if nan
                v.set(0)
            else:
                v.set(1)
            box = tk.Checkbutton(self.inner_frame, text=row['NDC'], variable=v, command= self.callback)
            box.grid(row=n, column=0, sticky='w', padx=2)
            self.var.append(v)
            tk.Label(self.inner_frame, text=row['Manufacturer'])\
                .grid(row=n, column=1, sticky='w', padx=8)
            tk.Label(self.inner_frame, text=row['Vertice Dosage Form'])\
                .grid(row=n, column=2, sticky='w', padx=8)
            tk.Label(self.inner_frame, text=row['2018_Units'])\
                .grid(row=n, column=3, sticky='w', padx=8)
            tk.Label(self.inner_frame, text=row['2019_Units'])\
                .grid(row=n, column=4, sticky='w', padx=8)
            tk.Label(self.inner_frame, text=row['WACPrice'])\
                .grid(row=n, column=5, sticky='w', padx=8)
            tk.Label(self.inner_frame, text=row['Pack'])\
                .grid(row=n, column=6, sticky='w', padx=8)
            n += 1

        ##############################################################
        # scrollbar
        ##############################################################
        self.scroll = tk.Scrollbar(self.outer_frame, orient='vertical')
        self.scroll.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.scroll.set)
        self.scroll.grid(row=0, sticky="nse")
        self.inner_frame.bind("<Configure>", self.update_scrollregion)  # update height of scrollbar

        ##############################################################
        # adjusting spacing when window expands
        ##############################################################
        for i in [0,1000,1001]:
            master.grid_rowconfigure(i, weight=1)
        master.grid_columnconfigure(0, weight=2)
        for i in range(1,5):
            master.grid_columnconfigure(i, weight=1)

        ##############################################################
        # count of ndcs selected at bottom
        ##############################################################
        self.count_of_ndcs = tk.StringVar()
        x = str(sum([1 for i in range(len(self.ndcs)) if self.var[i].get() == 1])) + ' Selected'
        self.count_of_ndcs.set(x)
        tk.Label(master, textvariable=self.count_of_ndcs,
                 font='Helvetica 9 bold').grid(row=1000, column=0, sticky='ew')

        tk.Button(master, text='Select all', command=self.select_all).grid(row=1000, column=1)
        tk.Button(master, text='Unselect all', command=self.unselect_all).grid(row=1000, column=2)

        tk.Button(master, text='Continue', command=self.save_and_continue)\
            .grid(row=1000, column=3, pady=20, padx=20)

    def callback(self):
        '''Update count of NDCs selected when box is checked/unchecked.'''
        x = sum([1 for i in range(len(self.ndcs)) if self.var[i].get() == 1])
        self.count_of_ndcs.set(str(x) + ' Selected')

    def save_and_continue(self):
        self.selected_ndcs = [self.ndcs['NDC'][i] for i in range(len(self.ndcs))
                              if self.var[i].get() == 1]
        self.master.destroy()

    def update_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def select_all(self):
        '''Select all boxes and update count of NDCs selected.'''
        for i in self.var:
            i.set(1)
        x = sum([1 for i in range(len(self.ndcs)) if self.var[i].get() == 1])
        self.count_of_ndcs.set(str(x) + ' Selected')

    def unselect_all(self):
        '''Unselect all boxes and update count of NDCs selected to 0.'''
        for i in self.var:
            i.set(0)
        x = sum([1 for i in range(len(self.ndcs)) if self.var[i].get() == 1])
        self.count_of_ndcs.set(str(x) + ' Selected')


class EnterFilepath:
    """
    GUI to get file path to Model Input Excel file.
    Finder window automatically pops up to select file (currently cannot reopen it if closed).
    Ability to add a run name.

    |    File Path and Run Tag   |
    |:--------------------------:|
    |     **Enter filepath:**    |
    |            -----           |
    |             OR             |
    |     **Enter run tag:**     |
    |            -----           |
    |          Continue          |

    """
    parameters = {}

    def __init__(self, master):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        ##############################################################
        # create window header
        ##############################################################
        tk.Label(master, text='Generics Forecasting Model: Set File Path and Run Tag',
                 font='Helvetica 9 bold').pack(pady=10)

        ##############################################################
        # add entry for filepath and populate
        ##############################################################
        self.filename = filedialog.askopenfilename(initialdir="C:\\Documents",  # TODO update
                                                   title="Select Model Input file",
                                                   filetypes=(("excel files", "*.xlsx"),
                                                              ("all files", "*.*")))
        tk.Label(master, text='Enter filepath for Excel parameters:').pack(pady=10)
        self.filepath_entry = tk.Entry(master, width=75)
        self.filepath_entry.insert(tk.END, self.filename)
        self.filepath_entry.pack()

        ##############################################################
        # add entry for run name
        ##############################################################
        tk.Label(master, text='Enter a run tag (optional):').pack(pady=10)
        self.run_name_entry = tk.Entry(master, width=50)
        self.run_name_entry.pack()
        master.after(10, self.run_name_entry.focus_force())

        tk.Button(master, text='Continue', command=self.save_and_continue).pack(pady=10)

    def save_and_continue(self):
        self.parameters['excel_filepath'] = self.filepath_entry.get()
        self.parameters['run_name'] = self.run_name_entry.get()

        self.master.destroy()


class EnterCOGS:
    """
    GUI to enter drug costs with three options.
    1. Margin
    2. Standard cost applied to each NDC
    3. Cost per each NDC

    |      Enter Gross Margin     |           |
    |:---------------------------:|:---------:|
    |                     margin: |    000    |
    |          --- OR --          |           |
    | **Enter Standard API Cost** |           |
    |          standard api cost: |    000    |
    |          --- OR ---         |           |
    | **Enter API Cost Per Unit** |           |
    |                  Base unit: |     MG    |
    |          api cost per unit: |    000    |
    |    Enter number of units:   |           |
    |                      pack 1 |    000    |
    |                      pack 2 |    000    |
    |                      pack n |    000    |
    |                             | Run Model |

    """
    COGS = {}

    def __init__(self, master, df_equivalents):
        self.master = master
        master.title('Generics Forecasting Model')
        master.resizable(width=False, height=False)  # disable ability to resize window

        tk.Label(master, text='Enter Gross Margin',
                 font='Helvetica 9 bold').grid(row=0, columnspan=2, pady=10)

        ##############################################################
        # if user uses straight gross margin approach
        ##############################################################
        tk.Label(master,
                 text='Gross margin assumption (as decimal): ').grid(row=1, column=0, sticky='e')
        self.gross_margin_entry = tk.Entry(master)
        self.gross_margin_entry.grid(row=1, column=1, sticky='w')

        ##############################################################
        # if user uses standard API approach
        ##############################################################
        self.sep1 = tk.ttk.Separator(master, orient="horizontal")
        self.sep1.grid(column=0, row=2, columnspan=2, sticky="ew")
        self.sty = tk.ttk.Style(master)
        self.sty.configure("TSeparator", background="blue")

        tk.Label(master, text='OR', font='Helvetica 9 bold')\
            .grid(row=2, columnspan=2, pady=10, padx=10)
        tk.Label(master, text="Enter Standard API Cost", font='Helvetica 9 bold')\
            .grid(row=3, columnspan=2, pady=10, padx=10)

        tk.Label(master, text='Standard API Cost ($): ').grid(row=4, column=0, sticky='e')
        self.standard_cogs_entry = tk.Entry(master)
        self.standard_cogs_entry.grid(row=4, column=1, sticky='w')

        ##############################################################
        # if user uses API cost per unit approach
        ##############################################################
        self.sep2 = tk.ttk.Separator(master, orient="horizontal")
        self.sep2.grid(column=0, row=5, columnspan=2, sticky="ew")

        tk.Label(master, text='OR', font='Helvetica 9 bold')\
            .grid(row=5, columnspan=2, pady=10, padx=10)
        tk.Label(master, text='Enter API Cost Per Unit', font='Helvetica 9 bold')\
            .grid(row=6, columnspan=2, pady=10, padx=10)

        tk.Label(master, text='Base unit: ').grid(row=7, column=0, sticky='e')
        self.unit_entry = tk.Entry(master)
        self.unit_entry.insert(tk.END, df_equivalents['Base Unit'].iloc[0])
        self.unit_entry.grid(row=7, column=1, sticky='w')

        tk.Label(master, text='API cost per unit ($): ').grid(row=8, column=0, sticky='e')
        self.cost_per_unit_entry = tk.Entry(master)
        self.cost_per_unit_entry.grid(row=8, column=1, sticky='w')

        ##############################################################
        # add entry boxes for API units for each pack type found in therapeutic equivalents
        ##############################################################
        tk.Label(master, text='Enter number of units for each pack type found: \n'
                              'Double check auto-populated numbers.')\
            .grid(row=9, rowspan=2, columnspan=2, pady=10)

        self.entries = []  # save entries created in list
        i = 0  # start placing labels below the already assigned rows

        ##############################################################
        # setup for scroll bar
        ##############################################################
        self.outer_frame = tk.Frame(master)
        self.outer_frame.grid(row=11, column=0, columnspan=2)
        self.outer_frame.rowconfigure(0, weight=1)
        self.outer_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.outer_frame, height=100)
        self.canvas.grid(sticky="nsew")

        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window(0, 0, window=self.inner_frame, anchor='nw')

        ##############################################################
        # fill scroll bar area with pack and number of units in each pack
        ##############################################################
        self.packs = df_equivalents[['Pack', 'Units']].drop_duplicates()['Pack'].values
        self.units = df_equivalents[['Pack', 'Units']].drop_duplicates()['Units'].values
        for p in range(len(df_equivalents[['Pack', 'Units']].drop_duplicates())):
            tk.Label(self.inner_frame, text=self.packs[p]).grid(row=i, column=1, padx=5, sticky='e')
            pack_entry = tk.Entry(self.inner_frame)
            pack_entry.insert(tk.END, self.units[p])
            pack_entry.grid(row=i, column=2, padx=5)
            self.entries.append(pack_entry)
            i += 1

        ##############################################################
        # scrollbar
        ##############################################################
        self.scroll = tk.Scrollbar(self.outer_frame, orient='vertical')
        self.scroll.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.scroll.set)
        self.scroll.grid(row=0, sticky="nse")

        self.inner_frame.bind("<Configure>", self.update_scrollregion)  # update height of scrollbar

        run_model_button = tk.Button(master, text='Run Model', command=self.save_and_run)
        run_model_button.grid(row=12, column=1, pady=10)

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


# class ShowResults:
#     """
#     GUI that shows results and allows user to kick off parameter scan or cancel it.
#
#     |     Results Summary    |
#     |:----------------------:|
#     |     **NPV**: 0.00m     |
#     |      **IRR**: 0.0%     |
#     | **Payback**: 0.0 years |
#     |  **Exit value**: 0.00m |
#     |     **MOIC**: 0.0x     |
#     |        Run Scan        |
#     |       Cancel Scan      |
#
#     """
#     def __init__(self, master, parameters):
#         self.master = master
#         master.title('Generics Forecasting Model')
#         master.geometry("500x300")
#
#         self.title = Label(master, text='Generics Forecasting Model: Results Summary',
#                            font='Helvetica 9 bold')
#         self.title.pack(pady=10)
#
#         ##############################################################
#         # printing the 5 calculated valuation metrics
#         ##############################################################
#         self.unit_label = Label(master, text='NPV: ${} million'.format(parameters['npv']))
#         self.unit_label.pack()
#         self.unit_label = Label(master, text='IRR: {}%'.format(parameters['irr']))
#         self.unit_label.pack()
#         self.unit_label = Label(master, text='Payback: {} years'.format(parameters['payback']))
#         self.unit_label.pack()
#         self.unit_label = Label(master, text='Exit value in 2021: ${} million'
#                                 .format(parameters['exit_value']))
#         self.unit_label.pack()
#         self.unit_label = Label(master, text='MOIC in 2021: {}x'.format(parameters['moic']))
#         self.unit_label.pack()
#
#         run_model_button = Button(master, text='Run Parameter Scan', command=master.destroy)
#         run_model_button.pack(pady=20)
#
#         def stop_model():
#             import sys
#             sys.exit()
#
#         stop_model_button = Button(master, text='Cancel Parameter Scan', command=stop_model)
#         stop_model_button.pack()


class ShowDetailedResults():
    """
    GUI that shows detailed results when user choose not to run parameter in Excel file.

    |               |          |          |     Results Summary    |          |          |          |
    |---------------|----------|----------|:----------------------:|----------|----------|----------|
    |               |          |          |     **NPV**: 0.00m     |          |          |          |
    |               |          |          |      **IRR**: 0.0%     |          |          |          |
    |               |          |          | **Payback**: 0.0 years |          |          |          |
    |               |          |          |  **Exit value**: 0.00m |          |          |          |
    |               |          |          |     **MOIC**: 0.0x     |          |          |          |
    |               |          |          |                        |          |          |          |
    |               | **2019** | **2020** |           ...          | **2028** | **2029** | **2030** |
    | **Net Sales** |     0    |     0    |           ...          |     0    |     0    |     0    |
    | **COGS**      |     0    |     0    |           ...          |     0    |     0    |     0    |
    | **EBIT**      |     0    |     0    |           ...          |     0    |     0    |     0    |
    | **FCF**       |     0    |     0    |           ...          |     0    |     0    |     0    |
    |               |          |          |         Finish         |          |          |          |

    """
    def __init__(self, master, parameters, df_gfm):
        self.master = master
        master.title('Generics Forecasting Model')

        tk.Label(master, text='Generics Forecasting Model: Results Summary',
                 font='Helvetica 9 bold').grid(row=0, column=0, sticky='n', columnspan=12)
        tk.Label(master,
                 text='Chose whether to run the parameter scan and save results to the database.',
                 font='Helvetica 9').grid(row=1, column=0, sticky='n', columnspan=12)

        tk.Label(master, text='').grid(row=2, rowspan=2)

        ##############################################################
        # select what brand/molecule the user picked in the first screen
        ##############################################################
        if parameters['search_type'] == 'brand':
            search_type = 'Brand Name'
            drug_id = parameters['brand_name']
        else:
            search_type = 'Molecule'
            drug_id = parameters['molecule_name']

        ##############################################################
        # printing the 5 calculated valuation metrics
        ##############################################################
        tk.Label(master, text='{}:  '.format(search_type),
                 font='Helvetica 9 bold').grid(row=4, column=0, sticky='e', columnspan=6)
        tk.Label(master, text='NPV:  ',
                 font='Helvetica 9 bold').grid(row=5, column=0, sticky='e', columnspan=6)
        tk.Label(master, text='IRR:  ',
                 font='Helvetica 9 bold').grid(row=6, column=0, sticky='e', columnspan=6)
        tk.Label(master, text='Payback:  ',
                 font='Helvetica 9 bold').grid(row=7, column=0, sticky='e', columnspan=6)
        tk.Label(master, text='Exit value in 2021:  ',
                 font='Helvetica 9 bold').grid(row=8, column=0, sticky='e', columnspan=6)
        tk.Label(master, text='MOIC in 2021:  ',
                 font='Helvetica 9 bold').grid(row=9, column=0, sticky='e', columnspan=6)

        tk.Label(master, text='{}'.format(drug_id))\
            .grid(row=4, column=6, sticky='w', columnspan=6)
        tk.Label(master, text='${} million'.format(parameters['npv']))\
            .grid(row=5, column=6, sticky='w', columnspan=6)
        tk.Label(master, text='{}%'.format(parameters['irr']))\
            .grid(row=6, column=6, sticky='w', columnspan=6)
        tk.Label(master, text='{} years'.format(parameters['payback']))\
            .grid(row=7, column=6, sticky='w', columnspan=6)
        tk.Label(master, text='${} million'.format(parameters['exit_value']))\
            .grid(row=8, column=6, sticky='w', columnspan=6)
        tk.Label(master, text='{}x'.format(parameters['moic']))\
            .grid(row=9, column=6, sticky='w', columnspan=6)

        tk.Label(master, text='').grid(row=10, columnspan=12)

        ##############################################################
        # set up annual financial results table
        ##############################################################
        tk.Label(master, text="($m)", font='Helvetica 9').grid(row=11, column=0)
        tk.Label(master, text="Net Sales", font='Helvetica 9 bold').grid(row=12, column=0)
        tk.Label(master, text="COGS", font='Helvetica 9 bold').grid(row=13, column=0)
        tk.Label(master, text="EBIT", font='Helvetica 9 bold').grid(row=14, column=0)
        tk.Label(master, text="FCF", font='Helvetica 9 bold').grid(row=15, column=0)

        ##############################################################
        # years as headers
        ##############################################################
        c = 1
        for i in range(parameters['present_year'], parameters['present_year'] + 11):
            tk.Label(master, text=i, font='Helvetica 9 bold').grid(row=11, column=c)
            c = c + 1

        ##############################################################
        # adding the results to the results table
        ##############################################################
        df = round(df_gfm[['Net Sales', 'COGS', 'EBIT',
                           'FCF']].loc[parameters['present_year']:].transpose(), 2)

        r = 12
        for x in ['Net Sales', 'COGS', 'EBIT', 'FCF']:
            c = 1
            for y in range(parameters['present_year'], parameters['present_year'] + 11):
                tk.Label(master, text=df[y].loc[x], font='Helvetica 9').grid(row=r, column=c)
                c = c + 1
            r = r + 1

        ##############################################################
        # adjusting spacing when window expands
        ##############################################################
        for i in [0,10,18]:
            master.grid_rowconfigure(i, weight=1)
        for i in range(1,12):
            master.grid_columnconfigure(i, weight=1)

        run_model_button = tk.Button(master, text='Run Parameter Scan', command=master.destroy)
        run_model_button.grid(row=16, columnspan=12, pady=10)

        def stop_model():
            import sys
            sys.exit()

        stop_model_button = tk.Button(master, text='Cancel Parameter Scan', command=stop_model)
        stop_model_button.grid(row=17, columnspan=12, pady=10)


class SuccessfulRun:
    """
    GUI that shows that the parameter scan and writing of results to the database was successful.

    | Successful Model Run |
    |:--------------------:|
    |    scan complete     |
    |    results saved     |

    """
    def __init__(self, master):
        self.master = master
        master.title('')
        master.geometry("300x150")

        tk.Label(master, text='Generics Forecasting Model: Successful Model Run',
                 font='Helvetica 9 bold').pack(pady=10)
        tk.Label(master, text='Parameter scan complete.', font='Helvetica 9').pack(pady=10)
        tk.Label(master, text='Results saved to the database.', font='Helvetica 9').pack(pady=10)

        tk.Button(master, text='Finish', command=master.destroy).pack(pady=20)
