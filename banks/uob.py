from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional

class UOB(BaseBank):

    column_map = {
            "6726": "C",  # column letter for card ending 6726
            "7951": "D",
            "8363": "E",
            "6840": "F",
            "4769": "G",
            "6114": "H",
            "2379": "I",
            "4525": "J", 
              # another example
        }

    @classmethod
    def get_config(cls) -> BankConfig:
        return BankConfig(
            name="UOB",
            card_pattern=r"\*\*(\d{4}-\d{4}-\d{4}-(\d{4}))\*\*",
            start_keywords=[r"\*\*\d{4}-\d{4}-\d{4}-\d{4}\*\*"],
            end_keywords=["END OF STATEMENT"],
            previous_balance_keywords=["PREVIOUS BAL"],
            credit_payment_keywords=["CR"],
            retail_interest_keywords=["RETAIL INTEREST"],
            subtotal_keywords=["SUB-TOTAL"],
            minimum_payment_keywords=["MINIMUM PAYMENT DUE"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP"],
            credit_indicator="CR"
        )

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        """UOB-specific block creation logic"""
        blocks = {}
        current_card = None
        current_block = []
        in_block = False

        for line in lines:
            clean_line = ' '.join(line.split())
            
            # Detect card number (e.g., **1234-5678-9012-3456**)
            card_match = re.search(self.config.card_pattern, clean_line)
            if card_match:
                if current_card:  # Save previous card's block
                    blocks[current_card] = current_block
                current_card = card_match.group(2)  # Last 4 digits
                current_block = [line]
                in_block = True
                continue
            
            # Detect end of block
            if in_block and any(end_kw in clean_line for end_kw in self.config.end_keywords):
                blocks[current_card] = current_block + [line]
                current_card = None
                current_block = []
                in_block = False
                continue
            
            if in_block:
                current_block.append(line)

        return blocks

    def process_block(self, block: List[str],full_text: List[str]) -> Dict[str, float]:
        """Extract financial data from a UOB statement block"""
        data = {
            "previous_balance": 0.0,
            "credit_payment": 0.0,
            "retail_purchases": 0.0,
            "debit_fees": 0.0,
            "balance_due": 0.0,
            "minimum_payment": 0.0
        }

        i = 0
        while i < len(block):
            line = block[i].strip()
            next_line = block[i+1].strip() if i+1 < len(block) else ""
            line_lower = line.lower()

            # Previous Balance (usually appears as "PREVIOUS BAL" followed by amount on next line)
            if any(kw in line for kw in self.config.previous_balance_keywords):
                amount = self.extract_amount(next_line.replace("CR", ""))
                if amount:
                    data["previous_balance"] = -amount if "CR" in next_line else amount
                i += 1  # Skip next line since we've processed it

            # Credit Payments (marked with "CR" in UOB)
            elif self.config.credit_indicator in line:
                amount = self.extract_amount(line.replace("CR", ""))
                if amount is not None:
                    data["credit_payment"] += -amount

            # Retail Interest/Fees
            elif any(kw in line for kw in self.config.retail_interest_keywords):
                amount = self.extract_amount(next_line)
                if amount:
                    data["debit_fees"] += amount
                i += 1

            # Subtotal/Balance Due
            elif any(kw in line for kw in self.config.subtotal_keywords):
                amount = self.extract_amount(next_line.replace("CR", ""))
                if amount:
                    data["balance_due"] = -amount if "CR" in next_line else amount
                i += 1

            # Minimum Payment
            elif any(kw in line for kw in self.config.minimum_payment_keywords):
                amount = self.extract_amount(next_line)
                if amount:
                    data["minimum_payment"] = amount
                i += 1

            # Retail Purchases (individual transactions)
            elif self.is_amount_line(line) and not any(curr in block[i-1] for curr in self.config.foreign_currencies):
                amount = self.extract_amount(line)
                if amount and amount > 0:  # Positive amounts are purchases
                    data["retail_purchases"] += amount

            i += 1

        return data

    def is_amount_line(self, line: str) -> bool:
        """UOB-specific check for lines containing just an amount"""
        line = line.strip()
        return (re.fullmatch(self.config.amount_pattern, line) is not None 
                and not any(c.isalpha() for c in line))
    
    
