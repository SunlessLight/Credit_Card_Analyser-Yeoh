import unittest
from unittest.mock import patch
from statement_analyser_personal.app.banks.uob import UOB
from statement_analyser_personal.app.banks.test_block import create_blocks, extract_lines
from statement_analyser_personal.app.processor_tools.text_extractor import TextExtractor

class TestBank(unittest.TestCase):

    def setUp(self):
        self.bank = UOB()
        

    def test_process_block_with_valid_data(self):
        block = [
            "**4141-7000-0684-6726**",
            "PREVIOUS BAL",
            "15,680.18",
            "Payment",
            "3,000.00 CR",
            "cash rebate",
            "15.00 CR",
            "MY",
            "200.00",
            "RETAIL INTEREST",
            "228.00",
            "SUB-TOTAL",
            "3,000.00",
            "MINIMUM PAYMENT DUE",
            "806.99",
        ]

        expected_data = {
            "previous_balance": 15680.18,
            "credit_payment": -3015.00,
            "retail_purchases": 200.00,
            "debit_fees": 228.00,
            "balance_due": 3000.00,
            "minimum_payment": 806.99,
        }

        result = self.bank.process_block(block)
        self.assertEqual(result, expected_data)

    def test_process_block_with_negative_data(self):
        block = [
            "**4141-7000-0684-6726**",
            "PREVIOUS BAL",
            "15,680.18 CR",
            "Payment",
            "3,000.00 CR",
            "cash rebate",
            "15.00 CR",
            "MY",
            "200.00",
            "RETAIL INTEREST",
            "228.00",
            "SUB-TOTAL",
            "3,000.00 CR",
            "MINIMUM PAYMENT DUE",
            "806.99",
        ]

        expected_data = {
            "previous_balance": -15680.18,
            "credit_payment": -3015.00,
            "retail_purchases": 200.00,
            "debit_fees": 228.00,
            "balance_due": -3000.00,
            "minimum_payment": 806.99,
        }

        result = self.bank.process_block(block)
        self.assertEqual(result, expected_data)


    def test_process_block_with_invalid_data(self):
        block = [
            "**4141-7000-0684-6726**",
            "cash rebate",
            "15.00 CR",
            "MY",
            "200.00",
            "RETAIL INTEREST",
            "228.00",
            "SUB-TOTAL",
            "3,000.00",
        ]

        expected_data = {
            "previous_balance": 0.00,
            "credit_payment": -15.00,
            "retail_purchases": 200.00,
            "debit_fees": 228.00,
            "balance_due": 3000.00,
            "minimum_payment": 0.00,
        }

        result = self.bank.process_block(block)
        self.assertEqual(result, expected_data)

    
    def test_real_data(self):
        lines = TextExtractor.extract_text(r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\second record\eStatement_76605.76854609993.pdf")
        blocks = self.bank.create_blocks(lines)
        print(blocks)
        result = {}
        for key, block in blocks.items():
            result[key] = self.bank.process_block(block)
            
        for card, data in result.items():
                print(f"{card}\t{data['previous_balance']:.2f}\t{data['credit_payment']:.2f}\t"
                    f"{data['debit_fees']:.2f}\t{data['retail_purchase']:.2f}\t"
                    f"{data['balance_due']:.2f}\t{data['minimum_payment']:.2f}")
    

if __name__ == "__main__":
    unittest.main()