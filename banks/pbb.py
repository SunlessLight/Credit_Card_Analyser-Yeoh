from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional

class PBB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        return BankConfig(
            name="PBB",
            card_pattern = r"(\d{4} \d{4} \d{4} \d{4})",
            start_keywords=[r"PB GOLD MASTERCARD 5472 3101 4879 3103 TAI LEE SEE"],
            end_keywords=["Sila semak penyata dengan segera"],
            previous_balance_keywords=["Previous Balance"],
            credit_payment_keywords=["This month total credit"],
            credit_indicator="CR",
            retail_interest_keywords=["RETAIL INTEREST RATE = 15.00%"],
            subtotal_keywords=["Jumlah besar untuk akaun ini / Grand total for this account"],
            minimum_payment_keywords=["PAGE 1 OF 3"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"]
        )

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:

        blocks = {}
        current_card = None
        current_block = []
        in_block = False

        for line in lines:
            clean_line = ' '.join(line.split())
            
            # Detect card number (e.g., **1234-5678-9012-3456**)
            card_match = re.search(self.config.card_pattern, clean_line)
            if "PB GOLD MASTERCARD" in clean_line and "TAI LEE SEE" in clean_line and card_match:
                if current_card:  # Save previous card's block
                    blocks[current_card] = current_block
                full_card = card_match.group(1).replace(" ", "")  # "5472310148793103"
                current_card = full_card[-4:]         
                
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

            # Credit Payment
            elif any(kw in line for kw in self.config.credit_payment_keywords):
                if i + 1 < len(block):
                    amount = self.extract_amount(block[i + 1])
                    if amount:
                        data["credit_payment"] = -abs(amount)
                    i += 1

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

            

            # Retail Purchases (individual transactions)
            elif "This month total debit" in line and i + 1 < len(block):
                amount = self.extract_amount(block[i + 1])
                if amount:
                    data["retail_purchases"] += amount
                i += 1

            i += 1
        print(data)
        return data

    def extract_minimum_payments_from_text(self, lines: List[str]) -> Dict[str, float]:
        print("[DEBUG] Entered extract_minimum_payments_from_text")
        """
        Scan full text for 16-digit card numbers and extract minimum payment two lines below each.
        Return mapping: last 4 digits -> minimum payment
        """
        card_minimums = {}
        for i, line in enumerate(lines):
            match = re.search(self.config.card_pattern, line)
            if match and i + 3 < len(lines):
                
                card_number = match.group().replace(" ", "")
                last4 = card_number[-4:]
                
                amount = self.extract_amount(lines[i + 3])
                if amount is not None:
                    card_minimums[last4] = amount
            if "PAGE 1 OF 3" in line:
                break        
                 
        return card_minimums

    def extract(self, lines: List[str]) -> Dict[str, Dict[str, float]]:
        

        blocks = self.create_blocks(lines)
        results = {}

        # Extract card -> minimum payment mapping from full text
        min_payments = self.extract_minimum_payments_from_text(lines)
        

        # Process each card block
        for key, block in blocks.items():
            results[key] = self.process_block(block, lines)
            if key in min_payments:
                results[key]["minimum_payment"] = min_payments[key]

        return results
    
    