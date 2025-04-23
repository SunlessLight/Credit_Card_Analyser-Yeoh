def get_record_number():
    while True:
        try:
            num = input("Enter record number to update (1 = first, 2 = second, etc.): ").strip()
            if num.lower() == 'q':
                return None
                
            num = int(num)
            if num >= 1:
                return num
            print("❌ Record number must be 1 or higher")
        except ValueError:
            print("❌ Please enter a valid number")

def parser_show_result(processor, selected_pdf, password):
        try:
                results = processor.parse_statement(selected_pdf, password)

                print("\nResults:")
                print("Card\tPrevious Balance\tCredit Payment\tRetail Purchases\tDebit Fees\tBalance Due\tMinimum Payment")
                for card, data in results.items():
                    print(f"{card}\t{data['previous_balance']:.2f}\t{data['credit_payment']:.2f}\t"
                        f"{data['retail_purchases']:.2f}\t{data['debit_fees']:.2f}\t"
                        f"{data['balance_due']:.2f}\t{data['minimum_payment']:.2f}")
                
                # Ask user if they want to update Excel
                excel_path = input("Enter Excel file path: ").strip()
                try:
                    record_number = get_record_number()
                    if record_number :

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