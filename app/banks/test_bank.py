import unittest
from unittest.mock import patch
from statement_analyser_personal.app.banks.uob import UOB
from statement_analyser_personal.app.banks.base_bank import BankConfig

class TestBank(unittest.TestCase):

    def setUp(self):
        self.bank = UOB()
        self.bank.config = BankConfig(
            name="UOB",
            card_pattern=r"\*\*(\d{4}-\d{4}-\d{4}-(\d{4}))\*\*",
            start_keywords=[r"\*\*\d{4}-\d{4}-\d{4}-\d{4}\*\*"],
            end_keywords=["END OF STATEMENT"],
            previous_balance_keywords=["PREVIOUS BAL"],
            credit_payment_keywords=["CR"],
            debit_fees_keywords=["RETAIL INTEREST"],
            subtotal_keywords=["SUB-TOTAL"],
            minimum_payment_keywords=["MINIMUM PAYMENT DUE"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP"],
        )

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
    
  

if __name__ == "__main__":
    unittest.main()