from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional

class RHB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        return BankConfig(
            name="RHB",
            
            card_pattern=r"(\d{4}-\d{4}-\d{4}-(\d{4}))",
            start_keywords=[r"(\d{4}-\d{4}-\d{4}-(\d{4}))\s*\bTAI LEE SEE\b"],
            end_keywords=["TOTAL OUTSTANDING BALANCE / JUMLAH BAKI TERKINI"],
            previous_balance_keywords=["OPENING BALANCE / BAKI MULA"],
            credit_payment_keywords="CR",
            retail_interest_keywords=["interest charged"],
            subtotal_keywords=["CLOSING BALANCE / BAKI AKHIR"],
            minimum_payment_keywords=["TOTAL Minimum Payment"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"]
        )

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        """RHB-specific block creation logic"""
        blocks = {}
        current_card = None
        current_block = []
        in_block = False

        for line in lines:
            clean_line = ' '.join(line.split())
            
            # Detect card number (e.g., **1234-5678-9012-3456**)
            card_match = re.search(self.config.card_pattern, clean_line)
            if "TAI LEE SEE" in clean_line and card_match:
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

    def process_block(self, block: List[str], full_text: List[str]) -> Dict[str, float]:
        data = {
            "previous_balance": 0.0,
            "credit_payment": 0.0,
            "retail_purchases": 0.0,
            "debit_fees": 0.0,
            "balance_due": 0.0,
            "minimum_payment": 0.0  # Will be injected later
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
            elif self.config.credit_payment_keywords in line:
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
            elif self.is_amount_line(line) :
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

    def extract_minimum_payments_from_text(self, lines: List[str]) -> Dict[str, float]:
        """
        Scan full text for 16-digit card numbers and extract minimum payment two lines below each.
        Return mapping: last 4 digits -> minimum payment
        """
        card_minimums = {}
        for i, line in enumerate(lines):
            match = re.search(self.config.card_pattern, line)
            if match and i + 5 < len(lines):
                card_number = match.group(2).replace("-", "")
                
                amount = self.extract_amount(lines[i + 4])
                if amount is not None:
                    card_minimums[card_number] = amount
            if "IMPORTANT ANNOUNCEMENT / PENGUMUMAN PENTING" in line:
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