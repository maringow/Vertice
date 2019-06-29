from tkinter import *

##----------------------------------------------------------------------
## WINDOW 1: SELECT BRAND NAME


class window1:
    brand = ''

    def __init__(self, master):
        self.master = master
        master.title("Generics Forecasting Model")
        master.geometry("600x400")

        # create window header
        self.title = Label(master, text='Generics Forecasting Model: Brand Selection')
        self.title.pack(pady=10)

        self.v = StringVar()
        self.entry = Entry(master, textvariable=self.v)
        self.entry.pack()



        self.greet_button = Button(master, text="Greet", command=self.greet)
        self.greet_button.pack()

        self.close_button = Button(master, text="Close", command=master.quit)
        self.close_button.pack()

    def greet(self):
        print("Greetings!")
        self.s=self.entry.get()
        print(self.s)

    def cycle_label_text(self, event):
        self.label_index += 1

