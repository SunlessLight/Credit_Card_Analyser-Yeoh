import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .processor_tools import ExcelManager, CreditCardProcessor
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class CreditCardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Statement Analyser")
        self.root.geometry("650x500")

        self.processor = None
        self.excel_manager = None

        self._create_widgets()

    def _create_widgets(self):
        # Bank selection
        tk.Label(self.root, text="Select Bank:").pack(pady=5)
        self.bank_var = tk.StringVar()
        self.bank_dropdown = ttk.Combobox(self.root, textvariable=self.bank_var, state="readonly")
        self.bank_dropdown['values'] = list(CreditCardProcessor.BANK_CLASSES.keys())
        self.bank_dropdown.pack()

        # PDF selection
        tk.Label(self.root, text="Select PDF file:").pack(pady=5)
        self.pdf_entry = tk.Entry(self.root, width=60)
        self.pdf_entry.pack()
        tk.Button(self.root, text="Browse PDF", command=self.select_pdf).pack()

        # Parse button
        tk.Button(self.root, text="Parse Statement", command=self.parse_statement).pack(pady=10)

        # Show result area
        self.result_text = tk.Text(self.root, height=8, width=75, state="disabled")
        self.result_text.pack(pady=5)

        # Excel file selection
        tk.Label(self.root, text="Excel File:").pack(pady=5)
        self.excel_entry = tk.Entry(self.root, width=60)
        self.excel_entry.pack()
        tk.Button(self.root, text="Browse Excel", command=self.select_excel).pack()

        # Record number
        tk.Label(self.root, text="Record Number:").pack(pady=5)
        self.record_entry = tk.Entry(self.root)
        self.record_entry.pack()

        # New or update Excel
        self.excel_mode = tk.StringVar(value="c")
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        tk.Radiobutton(frame, text="Create New Excel", variable=self.excel_mode, value="c").pack(side=tk.LEFT)
        tk.Radiobutton(frame, text="Update Existing Excel", variable=self.excel_mode, value="u").pack(side=tk.LEFT)

        # New bank option (only for update)
        self.new_bank_var = tk.StringVar(value="n")
        self.new_bank_frame = tk.Frame(self.root)
        tk.Label(self.new_bank_frame, text="Is this a new bank?").pack(side=tk.LEFT)
        tk.Radiobutton(self.new_bank_frame, text="Yes", variable=self.new_bank_var, value="y").pack(side=tk.LEFT)
        tk.Radiobutton(self.new_bank_frame, text="No", variable=self.new_bank_var, value="n").pack(side=tk.LEFT)
        self.new_bank_frame.pack(pady=5)
        self.new_bank_frame.pack_forget()  # Hide initially

        # Button to run Excel operation
        tk.Button(self.root, text="Run Excel Operation", command=self.run_excel_operation).pack(pady=10)

        # Status label
        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.pack(pady=5)

        # Bindings
        self.excel_mode.trace_add("write", self.toggle_new_bank_option)

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, path)

    def select_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls")])
        if path:
            self.excel_entry.delete(0, tk.END)
            self.excel_entry.insert(0, path)

    def toggle_new_bank_option(self, *args):
        if self.excel_mode.get() == "u":
            self.new_bank_frame.pack(pady=5)
        else:
            self.new_bank_frame.pack_forget()

    def parse_statement(self):
        bank = self.bank_var.get()
        pdf_path = self.pdf_entry.get()
        if not bank or not pdf_path:
            messagebox.showerror("Missing Info", "Please select a bank and PDF file.")
            return
        try:
            self.processor = CreditCardProcessor(bank)
            logger.info(f"Processor initialised for bank: {bank}")
            # Show result in text area
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Parsing {pdf_path} for {bank}...\n")
            result, dates = self.processor.parse_statement(pdf_path)
            self.result_text.insert(tk.END, f"Results: {result}\nDates: {dates}\n")
            self.result_text.config(state="disabled")
            self.status_label.config(text="Statement parsed successfully.", fg="green")
            # Prepare ExcelManager for next step
            self.excel_manager = ExcelManager(self.processor.bank_name, dates, result)
        except Exception as e:
            logger.error(f"Error parsing statement: {e}")
            self.status_label.config(text=f"Error: {e}", fg="red")
            messagebox.showerror("Error", str(e))

    def run_excel_operation(self):
        if not self.excel_manager:
            messagebox.showerror("Error", "Please parse a statement first.")
            return
        excel_path = self.excel_entry.get()
        record_no = self.record_entry.get()
        if self.excel_mode.get() == "u" and not excel_path:
            messagebox.showerror("Missing Info", "Please select an Excel file to update.")
            return
        try:
            record_no = int(record_no)
            if record_no < 1:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid Input", "Record number must be an integer >= 1.")
            return

        try:
            if self.excel_mode.get() == "c":
                self.excel_manager.create_excel_file()
                self.status_label.config(text="Excel file created.", fg="green")
                messagebox.showinfo("Success", "Excel file created successfully.")
            elif self.excel_mode.get() == "u":
                if self.new_bank_var.get() == "y":
                    self.excel_manager.insert_new_bank(excel_path)
                    self.status_label.config(text="New bank inserted.", fg="green")
                    messagebox.showinfo("Success", "New bank inserted successfully.")
                else:
                    self.excel_manager.update_excel(excel_path)
                    self.status_label.config(text="Excel file updated.", fg="green")
                    messagebox.showinfo("Success", "Excel file updated successfully.")
        except Exception as e:
            logger.error(f"Excel operation failed: {e}")
            self.status_label.config(text=f"Error: {e}", fg="red")
            messagebox.showerror("Error", str(e))

def main():
    root = tk.Tk()
    app = CreditCardGUI(root)
    root.mainloop()