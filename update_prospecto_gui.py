import tkinter as tk
from tkinter import filedialog

class EnterFilepath:
    """
    GUI to get file path to ProspectoRx price change file.
    Finder window automatically pops up to select file (currently cannot reopen it if closed).

    |  Update ProspectoRx Prices |
    |:--------------------------:|
    |     **Enter filepath:**    |
    |          Continue          |

    """
    parameters = {}

    def __init__(self, master):
        self.master = master
        master.title("Update ProspectoRx Prices")
        master.geometry("600x400")

        ##############################################################
        # create window header
        ##############################################################
        tk.Label(master, text='Generics Forecasting Model: Update ProspectoRx Prices',
                 font='Helvetica 9 bold').pack(pady=10)

        ##############################################################
        # add entry for filepath and populate
        ##############################################################
        self.filename = filedialog.askopenfilename(initialdir="C:\\Documents",  # TODO update
                                                   title="Select ProspectoRx price change file",
                                                   filetypes=(("excel files", "*.xlsx"),
                                                              ("all files", "*.*")))
        tk.Label(master, text='Enter filepath:').pack(pady=10)
        self.filepath_entry = tk.Entry(master, width=75)
        self.filepath_entry.insert(tk.END, self.filename)
        self.filepath_entry.pack()

        tk.Button(master, text='Continue', command=self.save_and_continue).pack(pady=10)

    def save_and_continue(self):
        self.parameters['excel_filepath'] = self.filepath_entry.get()
        self.master.destroy()
