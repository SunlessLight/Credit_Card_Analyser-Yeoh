from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional

class CIMB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        return BankConfig(
            name="CIMB",
            card_pattern = r"(\d{4}-\d{4}-\d{4}-\d{4})",
            start_keywords=r"Transaction Details / Transaksi Terperinci",
            end_keywords=["IMPORTANT INFORMATION / MAKLUMAT PENTING"],
            previous_balance_keywords=["PREVIOUS BALANCE"],
            credit_payment_keywords=["This month total credit"],
            credit_indicator="CR",
            retail_interest_keywords=["FINANCE CHARGES"],
            subtotal_keywords=["STATEMENT BALANCE"],
            minimum_payment_keywords=["PAGE 1 OF 3"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"]
        )

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        blocks = {}
        current_card = None
        current_block = []
        in_block = False
        found_start = False

        for line in lines:
            clean_line = ' '.join(line.split())

            # Only start processing *after* start keyword is found
            if not found_start:
                if any(start_kw in clean_line for start_kw in self.config.start_keywords):
                    found_start = True  # Now we can start parsing
                continue  # Skip until start keyword is found

            # Detect card number (e.g., 1234 5678 9012 3456)
            card_match = re.search(self.config.card_pattern, clean_line)
            if card_match:
                if current_card:
                    blocks[current_card] = current_block
                full_card = card_match.group(1).replace(" ", "")
                current_card = full_card[-4:]
                current_block = [line]
                in_block = True
                continue

            # Detect end of block
            if in_block and any(end_kw in clean_line for end_kw in self.config.end_keywords):
                current_block.append(line)
                blocks[current_card] = current_block
                current_card = None
                current_block = []
                in_block = False
                break  # Optional: stop parsing after first card block if only one card per statement
                # If multiple cards are expected, remove this break

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
                amount = -self.extract_amount(line.replace("CR", ""))
                if amount:
                    data["credit_payment"] += amount

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
            elif self.is_amount_line(line) and not any(curr in block[i-1] for curr in self.config.foreign_currencies):
                amount = self.extract_amount(line)
                if amount and amount > 0:  # Positive amounts are purchases
                    data["retail_purchases"] += amount

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
            if match and i + 4 < len(lines):
                
                card_number = match.group().replace(" ", "")
                last4 = card_number[-4:]
                
                amount = self.extract_amount(lines[i + 4])
                if amount is not None:
                    card_minimums[last4] = amount
            if any(end_kw in line for end_kw in self.config.end_keywords):
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
    
    def is_amount_line(self, line: str) -> bool:
        """UOB-specific check for lines containing just an amount"""
        line = line.strip()
        return (re.fullmatch(self.config.amount_pattern, line) is not None 
                and not any(c.isalpha() for c in line))
    
    