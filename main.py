from tools import ExcelManager, TextExtractor, CreditCardProcessor
import os
from pathlib import Path

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
    print("Available banks:")
    banks = list(CreditCardProcessor.BANK_CLASSES.keys())
    for i, bank in enumerate(banks, 1):
        print(f"{i}. {bank}")
    
    try:
        choice = int(input("Select bank: ")) - 1
        selected_bank = banks[choice]
    except (IndexError, ValueError):
        print("Invalid bank selection.")
        return

    processor = CreditCardProcessor(selected_bank)
    # Select PDF file from folder
    print(f"\n🔍 Scanning folder: {PDF_FOLDER}")
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in the folder.")
        return
    
    print("\nAvailable PDF files:")
    for i, filename in enumerate(pdf_files, 1):
        print(f"{i}. {filename}")
    
    file_choice = int(input("Select PDF file: ")) - 1
    selected_pdf = os.path.join(PDF_FOLDER, pdf_files[file_choice])
    password = BANK_PASSWORDS.get(selected_bank)

    # Ask user only if not pre-defined
    if password is None:
        password = input("Enter password (leave empty if none): ") or None
    else:
        print(f"🔐 Using saved password for {selected_bank}")


    try:
        results = processor.parse_statement(selected_pdf, password)

        print("\nResults:")
        print("Card\tPrevious Balance\tCredit Payment\tRetail Purchases\tDebit Fees\tBalance Due\tMinimum Payment")
        for card, data in results.items():
            print(f"{card}\t{data['previous_balance']:.2f}\t{data['credit_payment']:.2f}\t"
                f"{data['retail_purchases']:.2f}\t{data['debit_fees']:.2f}\t"
                f"{data['balance_due']:.2f}\t{data['minimum_payment']:.2f}")
        
        # Ask user if they want to update Excel
        update_excel = input("\nUpdate Excel file with these results? (y/n): ").strip().lower()
        if update_excel == 'y':
            excel_path = input("Enter Excel file path: ").strip()
            try:
                record_number = int(input("Enter record number to update (1 = first, 2 = second, etc.): "))

                while True:
                    try:
                        processor.write_to_excel(results, excel_path, record_number)
                        break  # Success
                    except PermissionError:
                        print("❌ Excel file is open. Please close it before continuing.")
                        retry = input("Try again? (y/n): ").strip().lower()
                        if retry != 'y':
                            print("Skipping Excel update.")
                            break
                    except Exception as e:
                        print(f"❌ Failed to update Excel: {str(e)}")
                        break

            except ValueError:
                print("❌ Invalid record number.")

    except Exception as e:
        print(f"Error: {str(e)}")



if __name__ == "__main__":
    main()
