from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

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

def parser_show_result(processor, selected_pdf):
        try:
                results, date = processor.parse_statement(selected_pdf)
                
                print("\nResults:")
                print(f"Statement Date: {date["statement_date"]}\tPayment Date: {date["payment_date"]}")
                print("Card\tPrevious Balance\tCredit Payment\tRetail Purchases\tDebit Fees\tBalance Due\tMinimum Payment")
                for card, data in results.items():
                    print(f"{card}\t{data['previous_balance']:.2f}\t{data['credit_payment']:.2f}\t"
                        f"{data['debit_fees']:.2f}\t{data['retail_purchase']:.2f}\t"
                        f"{data['balance_due']:.2f}\t{data['minimum_payment']:.2f}")
                
        except Exception as e:
            print(f"Error: {str(e)}")