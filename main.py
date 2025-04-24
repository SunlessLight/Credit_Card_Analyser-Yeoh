from .processor_tools import ExcelManager, TextExtractor, CreditCardProcessor
from .banks import get_password_from_bank
from pathlib import Path 
from .main_tools import get_bank_choice,get_folder_path, select_pdf_file,parser_show_result



CARD_ORDERED_MAP_PATH = Path(__file__).parent / "card_order_map.json"

# d:\OneDrive\Documents\Credit_card_programme\Credit_Card_Balances.xlsx
       
def main():
    print("📂 Credit Card Statement Parser")
    folder_path = get_folder_path()
        
    banks = list(CreditCardProcessor.BANK_CLASSES.keys())
    selected_bank = get_bank_choice(banks)
    if not selected_bank:
        return

    processor = CreditCardProcessor(selected_bank, ExcelManager(CARD_ORDERED_MAP_PATH))

    selected_pdf = select_pdf_file(folder_path)
    if not selected_pdf:
        return
    
    password = get_password_from_bank(selected_bank)

    parser_show_result(processor, selected_pdf, password)


if __name__ == "__main__":
    main()
