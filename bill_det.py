import tkinter as tk
import csv
from tkinter import messagebox
class Bill:
    def __init__(self):
        # Create the main window
        self.window = tk.Tk()
        self.window.title('Bill')
        self.window.geometry('400x400')

        # Create labels and entry fields
        self.customer_name_label = tk.Label(self.window, text="Customer Name:")
        self.customer_name_label.pack()
        self.customer_name_entry = tk.Entry(self.window)
        self.customer_name_entry.pack()

        

        # Create generate bill button
        self.generate_bill_button = tk.Button(self.window, text="Generate Bill", 
                                              command=self.generate_bill)
        self.generate_bill_button.pack()

    def generate_bill(self):
        customer_name = self.customer_name_entry.get()
        self.pend_orders = []
        with open('customer_orders.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['Customer Name'] == customer_name:
                    self.pend_orders.append(row["Order Pickup Date"])
            
        self.clicked = tk.StringVar()
        self.clicked.set( "Choose order date" )
  
    # Create Dropdown menu
        drop = tk.OptionMenu( self.window , self.clicked , *self.pend_orders )
        drop.pack()
  
    # Create button, it will change label text
        self.button = tk.Button(self.window , text = "click Me" , 
                           command = self.label.config( text = self.clicked.get())).pack()
  
    # Create Label
        self.label = tk.Label( self.window , text = " " )
        self.label.pack()

        # Validate inputs
        if customer_name == "":
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        # Retrieve bill details from CSV
        bill_details = []
        with open('customer_orders.csv') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if (row['Customer Name'] == customer_name and self.clicked.get()):
                    bill_details = [row['Bill ID'], row['Customer Name'], 
                                    row['Bill Amount'], self.clicked.get()]
                                    
                    break

            if not bill_details:
                messagebox.showerror("Error", "Bill details not found.")
                return

    # Display the bill
            messagebox.showinfo("Bill Details",f"Bill ID: {bill_details[0]}\n" 
                                         f"Customer Name: {bill_details[1]}\n"
                                         f"Total Amount: {bill_details[2]}\n"
                                         f"Bill Date: {bill_details[3]}")



# Start the main event loop
if __name__ == '__main__':
    app = Bill()
