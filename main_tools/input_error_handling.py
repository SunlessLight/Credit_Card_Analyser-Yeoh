import os


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

def select_pdf_file(folder_path: str = ".") -> str:
    print("\n📄 Select a PDF file:")
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("❌ No PDF files found.")
        return None
    for i, file in enumerate(pdf_files):
        print(f"  {i + 1}. {file}")
    try:
        file_choice = int(input("Select file number: ")) - 1
        return os.path.join(folder_path, pdf_files[file_choice])
    except (ValueError, IndexError):
        print("❌ Invalid file choice.")
        return None
