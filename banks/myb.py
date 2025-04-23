from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict


class MYB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        return BankConfig(
            name="MYB",
            card_pattern=r"\d{4} \d{4} \d{4} \d{4}",
            start_keywords=[r"MASTERCARD CLASSIC\s*:\s*\d{4} \d{4} \d{4} \d{4}"],
            end_keywords=["SUB TOTAL/JUMLAH"],
            previous_balance_keywords=["YOUR PREVIOUS STATEMENT BALANCE"],
            credit_payment_keywords=["(JUMLAH KREDIT)"],
            retail_interest_keywords=[],
            subtotal_keywords=["SUB TOTAL/JUMLAH"],
            minimum_payment_keywords=["Minimum Payment", "Bayaran Minima"],
            foreign_currencies=[],
            credit_indicator=""
        )

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        blocks = {}
        current_card = None
        current_block = []
        capture_active = False

        i = 0
        while i < len(lines):
            clean_line = ' '.join(lines[i].strip().split())

            if "MASTERCARD CLASSIC" in clean_line and re.search(self.config.card_pattern, clean_line):
                if current_card and current_block:
                    blocks[current_card] = current_block

                card_match = re.search(self.config.card_pattern, clean_line)
                current_card = card_match.group().replace(" ", "")[-4:]
                current_block = [clean_line]
                capture_active = True
                i += 1
                continue

            if capture_active:
                current_block.append(clean_line)
                if any(end_kw in clean_line for end_kw in self.config.end_keywords):
                    if i + 1 < len(lines):
                        current_block.append(lines[i + 1].strip())
                    blocks[current_card] = current_block
                    current_card = None
                    current_block = []
                    capture_active = False
                    i += 2
                    continue

            i += 1

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

            # Previous Balance
            if "YOUR PREVIOUS STATEMENT BALANCE" in line and i + 1 < len(block):
                amount = self.extract_amount(block[i + 1])
                if amount:
                    data["previous_balance"] = amount
                i += 1

            # Credit Payment (JUMLAH KREDIT)
            elif any(kw in line for kw in self.config.credit_payment_keywords):
                if i + 1 < len(block):
                    amount = self.extract_amount(block[i + 1])
                    if amount:
                        data["credit_payment"] = -abs(amount)
                    i += 1

            # Retail Purchase (JUMLAH DEBIT)
            elif "(JUMLAH DEBIT)" in line and i + 1 < len(block):
                amount = self.extract_amount(block[i + 1])
                if amount:
                    data["retail_purchases"] += amount
                i += 1

            # Balance Due (under SUB TOTAL/JUMLAH)
            elif "SUB TOTAL/JUMLAH" in line and i + 1 < len(block):
                amount = self.extract_amount(block[i + 1])
                if amount:
                    data["balance_due"] = amount
                i += 1

            i += 1

        return data

    def extract_minimum_payments_from_text(self, lines: List[str]) -> Dict[str, float]:
        """
        Scan full text for 16-digit card numbers and extract minimum payment two lines below each.
        Return mapping: last 4 digits -> minimum payment
        """
        card_minimums = {}
        for i, line in enumerate(lines):
            match = re.search(self.config.card_pattern, line)
            if match and i + 2 < len(lines):
                card_number = match.group().replace(" ", "")
                last4 = card_number[-4:]
                amount = self.extract_amount(lines[i + 2])
                if amount is not None:
                    card_minimums[last4] = amount
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
