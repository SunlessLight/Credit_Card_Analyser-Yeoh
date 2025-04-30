from .processor_tools import ExcelManager, CreditCardProcessor
from .banks import get_password_from_bank
from pathlib import Path 
import sys
import os
from .main_tools import get_bank_choice, select_pdf_file,parser_show_result

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    if getattr(sys, 'frozen', False):  # running from .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

CARD_ORDERED_MAP_PATH = Path(resource_path("card_order_map.json"))

# d:\OneDrive\Documents\Credit_card_programme\Credit_Card_Balances.xlsx
       
def main():
    print("📂 Credit Card Statement Parser")
    
        
    banks = list(CreditCardProcessor.BANK_CLASSES.keys())
    selected_bank = get_bank_choice(banks)
    if not selected_bank:
        return

    processor = CreditCardProcessor(selected_bank, ExcelManager(CARD_ORDERED_MAP_PATH))

    selected_pdf = select_pdf_file(".")  # Directly select a PDF file
    if not selected_pdf:
        return
    
    password = get_password_from_bank(selected_bank)

    parser_show_result(processor, selected_pdf, password)


if __name__ == "__main__":
    main()
