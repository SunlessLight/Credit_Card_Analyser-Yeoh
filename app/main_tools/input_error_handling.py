import os
from statement_analyser_personal.logger import get_logger
from tkinter import filedialog
import tkinter as tk
logger = get_logger(__name__)

def get_bank_choice(banks):
    while True:
        print("\nAvailable banks:")
        for i, bank in enumerate(banks, 1):
            print(f"{i}. {bank}")
        
        try:
            choice = input("Select bank (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
            
            choice = int(choice) - 1
            if 0 <= choice < len(banks):
                return banks[choice]
            print(f"❌ Please enter a number between 1 and {len(banks)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def select_excel_file() -> str:
    logger.info("Selecting Excel file")
    while True:

        try:
            root = tk.Tk()
            root.withdraw()
            root.lift()
            root.attributes("-topmost", True)
            root.after_idle(root.attributes, "-topmost", False)
            file_path = filedialog.askopenfilename(
                title = "Select Excel File",
                filetypes = [("Excel files", "*.xlsx"), ("Excel files", "*.xls")],
            )
            root.destroy()
            if not file_path:
                logger.error("No Excel file selected.")
                continue
            
            try:
                with open(file_path, "a+b") as f:
                    pass
            except Exception as e:
                logger.error(f"Excel file is opened or locked: {e}")
                print("❌ Excel file is opened or locked. Please close it and try again.")
                continue

            logger.info(f"Excel file selected: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Error selecting Excel file: {e}")
            print(f"❌ Error selecting Excel file: {e}")
            continue

def select_pdf_file() -> str:
    logger.info("Opening file dialog to select PDF file")
    while True:
        try:
            root = tk.Tk()
            root.withdraw()
            root.lift()
            root.attributes('-topmost', True)
            root.after_idle(root.attributes, '-topmost', False)
            file_path = filedialog.askopenfilename(
                title = "Select PDF file",
                filetypes=[("PDF files","*.pdf" )]
            )
            root.destroy()
            if not file_path:
                logger.error("No PDF file selected.")
                continue
            return file_path
        except Exception as e:
            logger.error(f"Error selecting PDF file:{e}")
            print(f"❌ Error selecting PDF file: {e}")
            continue
