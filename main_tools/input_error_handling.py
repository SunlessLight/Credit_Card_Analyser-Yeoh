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

def get_pdf_choice(pdf_files):
    while True:
        print("\nAvailable PDF files:")
        for i, filename in enumerate(pdf_files, 1):
            print(f"{i}. {filename}")
        
        try:
            choice = input("Select PDF file (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
                
            choice = int(choice) - 1
            if 0 <= choice < len(pdf_files):
                return pdf_files[choice]
            print(f"❌ Please enter a number between 1 and {len(pdf_files)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
