import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .processor_tools import ExcelManager, CreditCardProcessor
from .main_tools import get_resource_path
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

CARD_ORDERED_MAP_PATH = get_resource_path("data/card_order_map.json")


class CreditCardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Statement Analyser")
        self.root.geometry("600x400")

        self.processor = None
        self.selected_pdf = None

        self._create_widgets()

    def _create_widgets(self):
        # PDF selection
        tk.Label(self.root, text="Select PDF file:").pack(pady=5)
        self.pdf_entry = tk.Entry(self.root, width=60)  # Fixed variable name
        self.pdf_entry.pack()
        tk.Button(self.root, text="Browse PDF", command=self.select_pdf).pack()

        # Bank selection
        tk.Label(self.root, text="Select Bank:").pack(pady=5)
        self.bank_var = tk.StringVar()
        self.bank_dropdown = ttk.Combobox(self.root, textvariable=self.bank_var)
        self.bank_dropdown['values'] = list(CreditCardProcessor.BANK_CLASSES.keys())
        self.bank_dropdown.pack()
        self.bank_dropdown.bind("<<ComboboxSelected>>", self.update_password_field)

        # Password entry
        tk.Label(self.root, text="PDF Password:").pack(pady=5)
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        # Excel file path
        tk.Label(self.root, text="Excel File:").pack(pady=5)
        self.excel_entry = tk.Entry(self.root, width=60)
        self.excel_entry.pack()
        tk.Button(self.root, text="Browse Excel", command=self.select_excel).pack()

        # Record number
        tk.Label(self.root, text="Record Number:").pack(pady=5)
        self.record_entry = tk.Entry(self.root)
        self.record_entry.pack()

        # Parse button
        tk.Button(self.root, text="Parse and Update Excel", command=self.run_parser).pack(pady=10)

        # Status label
        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.pack(pady=5)

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, path)

    def select_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if path:
            self.excel_entry.delete(0, tk.END)
            self.excel_entry.insert(0, path)

    def show_processing_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Processing")
        tk.Label(popup, text="Parsing in progress... Please wait.").pack(padx=20, pady=20)
        popup.grab_set()
        self.root.update()
        return popup

    def run_parser(self):
        selected_pdf = self.pdf_entry.get()
        bank = self.bank_var.get()
        excel_path = self.excel_entry.get()
        record_number = self.record_entry.get()
        password = self.password_entry.get()

        if not (selected_pdf and bank and excel_path and record_number):
            messagebox.showerror("Missing Info", "Please fill in all fields.")
            return

        try:
            record_number = int(record_number)
        except ValueError:
            messagebox.showerror("Invalid Number", "Record number must be an integer.")
            return

        self.processor = CreditCardProcessor(bank, ExcelManager(CARD_ORDERED_MAP_PATH))

        popup = self.show_processing_popup()
        try:
            results = self.processor.parse_statement(selected_pdf, password)
            self.processor.write_to_excel(results, excel_path, record_number)
            popup.destroy()
            self.status_label.config(text="Parsing and Excel update complete.", fg="green")
            messagebox.showinfo("Success", "Parsing and Excel update complete.")
        except Exception as e:
            popup.destroy()
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            messagebox.showerror("Error", str(e))

    def update_password_field(self, event=None):
        # Always allow the user to input the password manually
        self.password_entry.config(state="normal")
        self.password_entry.delete(0, tk.END)


def main():
    root = tk.Tk()
    app = CreditCardGUI(root)
    root.mainloop()