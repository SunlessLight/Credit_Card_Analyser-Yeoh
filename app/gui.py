import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from statement_analyser_personal.app.processor_tools import ExcelManager, CreditCardProcessor
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class CreditCardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Statement Analyser")
        self.root.geometry("700x600")

        self.processor = None
        self.excel_manager = None
        self.result = None
        self.dates = None

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

        # Password entry
        tk.Label(self.root, text="PDF Password (if needed):").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        # Parse button
        tk.Button(self.root, text="Parse Statement", command=self.parse_statement).pack(pady=10)

        # Show result area
        self.result_text = tk.Text(self.root, height=8, width=80, state="disabled")
        self.result_text.pack(pady=5)

        # New or update Excel
        self.excel_mode = tk.StringVar(value="c")
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        tk.Radiobutton(frame, text="Create New Excel", variable=self.excel_mode, value="c", command = self.update_excel_info).pack(side=tk.LEFT)
        tk.Radiobutton(frame, text="Update Existing Excel", variable=self.excel_mode, value="u", command=self.update_excel_info).pack(side=tk.LEFT)

        # Excel file selection
        tk.Label(self.root, text="Excel File:").pack(pady=5)
        self.excel_entry = tk.Entry(self.root, width=60)
        self.excel_entry.pack()
        tk.Button(self.root, text="Browse Excel", command=self.select_excel).pack()

        # Info label for Excel file selection
        self.excel_info_label = tk.Label(self.root, text="", fg="blue")
        self.excel_info_label.pack()

        # Record number
        tk.Label(self.root, text="Record Number:").pack(pady=5)
        self.record_entry = tk.Entry(self.root)
        self.record_entry.pack()

        # Button to run Excel operation
        tk.Button(self.root, text="Run Excel Operation", command=self.run_excel_operation).pack(pady=10)

        # Status label
        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.pack(pady=5)

        # Help/Introduction button at bottom right
        help_btn = tk.Button(self.root, text="Help / Introduction", command=self.show_help)
        help_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)  # 10px from bottom right

        self.update_excel_info()

    def show_help(self):
        messagebox.showinfo(
            "Introduction / Help",
            "Welcome to Statement Analyser!\n\n"
            "This program helps you extract key financial information from your credit card statements and\n paste them into an excel file for easy tracking.\n\n"
            "1. Select your bank and statement PDF.\n"
            "2. Enter password if needed.\n"
            "3. Choose to create a new Excel file or update an existing one.\n"
            "4. Do note that 1 excel file can has multiple sheets for different banks.\n"
            "5. For updating, select the Excel file created by this program.\n"
            "6. Enter the record number (usually 1 for new statements).\n"
            "7. For new banks, select update existing excel and chose 'yes' when asked for new bank or not.\n"
            "Note: Ensure the Excel file is closed before updating.\n"
        )

    def update_excel_info(self):
        if self.excel_mode.get() == "c":
            self.excel_info_label.config(
                text = "(Leave Excel file box blank. A new Excel file will be created.)"
            )
        else:
            self.excel_info_label.config(
                text="(Please select an existing Excel file created by this program.)"
            )

    def select_pdf(self):
        while True:
            path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
            if not path:
                if not messagebox.askretrycancel("No PDF Selected", "No PDF file selected. Do you want to try again?"):
                    return
            else:
                self.pdf_entry.delete(0, tk.END)
                self.pdf_entry.insert(0, path)
                break

    def select_excel(self):
        while True:
            path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls")])
            if not path:
                if not messagebox.askretrycancel("No Excel Selected", "No Excel file selected. Do you want to try again?"):
                    return
            else:
                self.excel_entry.delete(0, tk.END)
                self.excel_entry.insert(0, path)
                break

    def ask_new_bank(self):
        """Popup dialog to ask if this is a new bank."""
        win = tk.Toplevel(self.root)
        win.title("New Bank?")
        win.grab_set()  # Make modal

        # Center the popup over the main window
        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()
        win.update_idletasks()
        win_w = win.winfo_width()
        win_h = win.winfo_height()
        # If win_w/h are 1 (not yet drawn), set a default size
        if win_w < 50: win_w = 250
        if win_h < 50: win_h = 120
        x = root_x + (root_w // 2) - (win_w // 2)
        y = root_y + (root_h // 2) - (win_h // 2)
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")


        tk.Label(win, text="Is this a new bank?").pack(padx=20, pady=10)
        result = {"choice": None}

        def choose(choice):
            result["choice"] = choice
            win.destroy()

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Yes", width=10, command=lambda: choose("y")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="No", width=10, command=lambda: choose("n")).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(win)
        return result["choice"]

    def parse_statement(self):
        bank = self.bank_var.get()
        pdf_path = self.pdf_entry.get()
        password = self.password_entry.get()
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
            # Password handling loop
            while True:
                try:
                    result, dates = self.processor.parse_statement(pdf_path,bank, password=password)
                    break
                except Exception as e:
                    logger.error(f"Error parsing statement: {e}")
                    if "password" in str(e).lower() or "decrypt" in str(e).lower():
                        password = self.prompt_password("Incorrect password. Please re-enter the PDF password:")
                        if password is None:
                            self.status_label.config(text="Parsing cancelled.", fg="red")
                            self.result_text.insert(tk.END, "Parsing cancelled by user.\n")
                            self.result_text.config(state="disabled")
                            return
                        self.password_entry.delete(0, tk.END)
                        self.password_entry.insert(0, password)
                        continue
                    else:
                        self.status_label.config(text=f"Error: {e}", fg="red")
                        messagebox.showerror("Error", str(e))
                        self.result_text.insert(tk.END, f"Error: {e}\n")
                        self.result_text.config(state="disabled")
                        return
            self.result = result
            self.dates = dates
            formatted = self.format_results(result, dates)
            self.result_text.insert(tk.END, formatted + "\n")
            self.result_text.config(state="disabled")
            self.status_label.config(text="Statement parsed successfully.", fg="green")
            self.excel_manager = ExcelManager(self.processor.bank_name, dates, result)
        except Exception as e:
            logger.error(f"Error parsing statement: {e}")
            self.status_label.config(text=f"Error: {e}", fg="red")
            messagebox.showerror("Error", str(e))

    def prompt_password(self, prompt):
        pw_win = tk.Toplevel(self.root)
        pw_win.title("Enter PDF Password")
        tk.Label(pw_win, text=prompt).pack(padx=10, pady=10)
        pw_var = tk.StringVar()
        pw_entry = tk.Entry(pw_win, textvariable=pw_var, show="*")
        pw_entry.pack(padx=10, pady=5)
        pw_entry.focus_set()
        result = {"password": None}

        def submit():
            result["password"] = pw_var.get()
            pw_win.destroy()

        def cancel():
            pw_win.destroy()

        tk.Button(pw_win, text="OK", command=submit).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(pw_win, text="Cancel", command=cancel).pack(side=tk.RIGHT, padx=10, pady=10)
        self.root.wait_window(pw_win)
        return result["password"]

    

    def run_excel_operation(self):
        if not self.excel_manager:
            messagebox.showerror("Error", "Please parse a statement first.")
            return
        excel_path = self.excel_entry.get()
        record_no = self.record_entry.get()
        logger.info("getting record number")
        if self.excel_mode.get() == "u" and not excel_path:
            messagebox.showerror("Missing Info", "Please select an Excel file to update.")
            return
        try:
            record_no = int(record_no)
            
        except Exception:
            messagebox.showerror("Invalid Input", "Record number must be an integer >= 1.")
            return

        try:
            if self.excel_mode.get() == "c":
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")],
                    initialfile="Credit Card Tracker.xlsx",
                    title="Save Excel File As"
                )
                if not save_path:
                    messagebox.showwarning("Cancelled", "Save cancelled by user.")
                    return
                self.excel_manager.create_excel_file(save_path=save_path)
                self.status_label.config(text="Excel file created.", fg="green")
                messagebox.showinfo("Success", "Excel file created successfully.")
            elif self.excel_mode.get() == "u":
                
                result_status = self.excel_manager.update_excel(excel_path, record_no)
                if result_status == "inserted":
                    self.status_label.config(text=f"New bank detected, inserting new excel sheet with name {self.processor.bank_name}", fg="green")
                    messagebox.showinfo("Success", f"New bank detected, inserted new excel sheet with name {self.processor.bank_name}")
                elif result_status == "updated":
                    self.status_label.config(text=f"Bank sheet detected, successfully updated it", fg="green")
                    messagebox.showinfo("Success", f"Bank sheet detected, successfully updated it")
        except Exception as e:
            logger.error(f"Excel operation failed: {e}")
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                user_msg = ("Worksheet for this bank already exists. Please retry and choose 'No' when asked after choosing update existing excel.")
            elif "permission denied" in error_msg.lower():
                user_msg = "Permission denied. Please close the Excel file if it is opened"
            elif "not found in the workbook" in error_msg.lower():
                user_msg = "Worksheet not found. Please choose (Update Existing Excel) -> (New Bank)"
            else:
                user_msg = f"An error occurred: {error_msg}"
            self.status_label.config(text=f"Error:{user_msg}", fg="red")
            messagebox.showerror("Error", user_msg)

    def format_results(self, result: dict, dates: dict) -> str:
        lines = []
        lines.append(f"Statement Date: {dates.get('statement_date', '')}")
        lines.append(f"Payment Due Date: {dates.get('payment_date', '')}")
        lines.append("")
        lines.append("Card No. | Prev Bal | Credit Pay | Debit Fees | Retail Purch | Bal Due | Min Pay")
        lines.append("-" * 75)
        for card, values in result.items():
            lines.append(
                f"{card:>7} | "
                f"{values['previous_balance']:>8.2f} | "
                f"{values['credit_payment']:>10.2f} | "
                f"{values['debit_fees']:>10.2f} | "
                f"{values['retail_purchase']:>12.2f} | "
                f"{values['balance_due']:>7.2f} | "
                f"{values['minimum_payment']:>7.2f}"
            )
        return "\n".join(lines)

def main():
    root = tk.Tk()
    app = CreditCardGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()