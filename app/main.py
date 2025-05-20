from .processor_tools import ExcelManager, CreditCardProcessor
from .main_tools import get_bank_choice,select_excel_file, select_pdf_file,parser_show_result
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

# d:\OneDrive\Documents\Credit_card_programme\Credit_Card_Balances.xlsx
       
def main():
    print("📂 Credit Card Statement Parser")
    banks = list(CreditCardProcessor.BANK_CLASSES.keys())
    selected_bank = get_bank_choice(banks)
    if not selected_bank:
        return
    logger.info(f"Selected bank: {selected_bank}")
    processor = CreditCardProcessor(selected_bank)
    logger.info(f"Processor initialised for bank: {selected_bank}")

    selected_pdf = select_pdf_file()  # Directly select a PDF file
    logger.info(f"Selected PDF file: {selected_pdf}")

    logger.info(f"Starting to parse statement for {selected_bank}")

    parser_show_result(processor, selected_pdf) 
    result,dates = processor.parse_statement(selected_pdf) #show resu
    
    logger.info(f"Initialising ExcelManager")
    excel_manager = ExcelManager(processor.bank_name, dates, result)

    while True:
        excel_choice = input("Do you want to create a new Excel file? (c) or update an existing excel file? (u): ").strip().lower()
        if excel_choice not in ["c", "u"]:
            print("❌ Invalid choice. Please enter 'c' to create a new file or 'u' to update an existing file.")
            continue
        break
    logger.info(f"User choice: {excel_choice}")

    if excel_choice == "c":
        logger.info("Creating new Excel file")
        
        excel_manager.create_excel_file()
        
    elif excel_choice == "u":

        excel_path = select_excel_file()
        if not excel_path:
            logger.error("No Excel file selected.")
            raise RuntimeError("No Excel file selected.")
        while True:
            new_bank = input("Is this a new bank? (y/n): ").strip().lower()
            if new_bank not in ["y", "n"]:
                print("❌ Invalid choice. Please enter 'y' for new bank or 'n' for existing bank.")
                continue
            break
        logger.info(f"User choice for new bank: {new_bank}")

        if new_bank == "y":
            excel_manager.insert_new_bank(excel_path)
        elif new_bank == "n":
            excel_manager.update_excel(excel_path)


if __name__ == "__main__":
    main()
