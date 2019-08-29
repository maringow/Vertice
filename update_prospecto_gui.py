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
                                                   filetypes=(("csv files", "*.csv"),
                                                              ("all files", "*.*")))
        tk.Label(master, text='Enter filepath:').pack(pady=10)
        self.filepath_entry = tk.Entry(master, width=75)
        self.filepath_entry.insert(tk.END, self.filename)
        self.filepath_entry.pack()

        tk.Button(master, text='Continue', command=self.save_and_continue).pack(pady=10)

    def save_and_continue(self):
        self.parameters['excel_filepath'] = self.filepath_entry.get()
        self.master.destroy()


class SuccessfulRun:
    """
    GUI that shows that the price update was successful.

    | Successful Model Run |
    |:--------------------:|
    |   update complete    |

    """
    def __init__(self, master, count_df):
        self.master = master
        master.geometry("400x350")
        master.title('Generics Forecasting Model')

        tk.Label(master, text='Successful ProspectoRX Price Update',
                 font='Helvetica 9 bold').pack(pady=10)
        tk.Label(master, text='{} NDC prices updated.'.format(count_df[1]),
                 font='Helvetica 9').pack(pady=10)
        tk.Label(master, text='{} new NDCs added to master file.'.format(count_df[2]-count_df[0]),
                 font='Helvetica 9').pack(pady=10)

        tk.Button(master, text='Okay', command=master.destroy).pack(pady=20)
