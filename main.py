from .processor_tools import ExcelManager, TextExtractor, CreditCardProcessor
import os
from pathlib import Path
from .main_tools import get_bank_choice, get_pdf_choice,parser_show_result


CARD_ORDERED_MAP_PATH = Path(__file__).parent / "card_order_map.json"
excel_manager = ExcelManager(CARD_ORDERED_MAP_PATH)

# Auto password mapping: Bank name -> password
BANK_PASSWORDS = {
    "PBB": "02APR1969",
    "UOB": None,
    "HLB": None,   # No password
    "RHB": "6096690402",
    "MYB": "02Apr1969",
    "CIMB": "t@026096",
}

# d:\OneDrive\Documents\Credit_card_programme\Credit_Card_Balances.xlsx
while True:
    PDF_FOLDER = input(r"Enter folder path: ").strip()
    if os.path.isdir(PDF_FOLDER):
        break
    print("❌ Invalid folder path. Please try again.")

        
def main():
    banks = list(CreditCardProcessor.BANK_CLASSES.keys())
    selected_bank = get_bank_choice(banks)
    if not selected_bank:
        return

    processor = CreditCardProcessor(selected_bank, excel_manager)
    
    # Select PDF file from folder
    print(f"\n🔍 Scanning folder: {PDF_FOLDER}")
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in the folder.")
        return
    
    selected_pdf = get_pdf_choice(pdf_files)
    if not selected_pdf:
        return
    
    selected_pdf = os.path.join(PDF_FOLDER, selected_pdf)
    
    password = BANK_PASSWORDS.get(selected_bank)

    # Ask user only if not pre-defined
    if not password :
        password = input("Enter password (leave empty if none): ").strip() or None
    else:
        print(f"🔐 Using saved password for {selected_bank}")

    parser_show_result(processor, selected_pdf, password)


if __name__ == "__main__":
    main()
