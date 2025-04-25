import tkinter as tk
import sys
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from credit_card_parser.processor_tools import ExcelManager, CreditCardProcessor
from credit_card_parser.banks import get_password_from_bank
from credit_card_parser.main_tools import select_pdf_file, parser_show_result

if getattr(sys, 'frozen', False):
    # If running as bundled exe
    base_path = Path(sys._MEIPASS)
else:
    # If running from source
    base_path = Path(__file__).parent

CARD_ORDERED_MAP_PATH = base_path / "card_order_map.json"


class CreditCardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Credit Card Parser")
        self.root.geometry("600x400")

        self.processor = None
        self.selected_pdf = None

        self._create_widgets()

    def _create_widgets(self):
        # Folder selection
        tk.Label(self.root, text="PDF Folder:").pack(pady=5)
        self.folder_entry = tk.Entry(self.root, width=60)
        self.folder_entry.pack()
        tk.Button(self.root, text="Browse Folder", command=self.select_folder).pack()

        # Bank selection
        tk.Label(self.root, text="Select Bank:").pack(pady=5)
        self.bank_var = tk.StringVar()
        self.bank_dropdown = ttk.Combobox(self.root, textvariable=self.bank_var)
        self.bank_dropdown['values'] = list(CreditCardProcessor.BANK_CLASSES.keys())
        self.bank_dropdown.pack()
        self.bank_dropdown.bind("<<ComboboxSelected>>", self.update_password_field)


        # PDF file selection
        tk.Label(self.root, text="Select PDF File:").pack(pady=5)
        self.pdf_dropdown = ttk.Combobox(self.root)
        self.pdf_dropdown.pack()

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

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

            folder_path = Path(folder)
            pdf_files = list(folder_path.glob("*.pdf"))

            if not pdf_files:
                messagebox.showinfo("No PDFs Found", "No PDF files found in the selected folder.")
            else:
                pdf_names = [pdf.name for pdf in pdf_files]
                self.pdf_dropdown['values'] = pdf_names
                self.pdf_dropdown.set(pdf_names[0])  # auto-select first PDF


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
        folder = self.folder_entry.get()
        selected_pdf_name = self.pdf_dropdown.get()
        bank = self.bank_var.get()
        excel_path = self.excel_entry.get()
        record_number = self.record_entry.get()
        password = self.password_entry.get()

        if not (folder and selected_pdf_name and bank and excel_path and record_number):
            messagebox.showerror("Missing Info", "Please fill in all fields.")
            return

        try:
            record_number = int(record_number)
        except ValueError:
            messagebox.showerror("Invalid Number", "Record number must be an integer.")
            return

        self.processor = CreditCardProcessor(bank, ExcelManager(CARD_ORDERED_MAP_PATH))
        pdf_path = str(Path(folder) / selected_pdf_name)
        
        popup = self.show_processing_popup()
        try:
            results = self.processor.parse_statement(pdf_path, password)
            self.processor.write_to_excel(results, excel_path, record_number)
            popup.destroy()
            self.status_label.config(text="Parsing and Excel update complete.", fg="green")
            messagebox.showinfo("Success", "Parsing and Excel update complete.")
        except Exception as e:
            popup.destroy()
            self.status_label.config(text=f"Error: {str(e)}", fg="red")
            messagebox.showerror("Error", str(e))

    def update_password_field(self, event=None):
        bank = self.bank_var.get()
        password = get_password_from_bank(bank)

        if password:
            self.password_entry.config(state="normal")
            self.password_entry.delete(0, tk.END)
            self.password_entry.insert(0, password)
            self.password_entry.config(state="readonly")  # prevent user edit if auto-filled
        else:
            self.password_entry.config(state="normal")
            self.password_entry.delete(0, tk.END)

def main():
    root = tk.Tk()
    app = CreditCardGUI(root)
    root.mainloop()


