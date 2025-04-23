from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict

class HLB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        return BankConfig(
            name="HLB",
            card_pattern=r"(\d{4} \d{4} \d{4} \d{4})",  # Full 16-digit card number
            start_keywords=[r"WISE VISA GOLD.*\d{4} \d{4} \d{4} \d{4}"],  # Combined pattern
            end_keywords=["TOTAL BALANCE"],
            previous_balance_keywords=["PREVIOUS BALANCE FROM LAST STATEMENT"],
            credit_payment_keywords=["CR"],
            retail_interest_keywords=["interest charged"],
            subtotal_keywords=["SUB TOTAL"],
            minimum_payment_keywords=["TOTAL Minimum Payment"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"],
            credit_indicator="CR"
        )

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        """Precise block creation starting with card header line"""
        blocks = {}
        current_card = None
        current_block = []
        capture_active = False
        
        for i, line in enumerate(lines):
            clean_line = ' '.join(line.strip().split())
            
            # Detect EXACT start: "WISE VISA GOLD" followed by card number in SAME line
            if "WISE VISA GOLD" in clean_line and re.search(self.config.card_pattern, clean_line):
                card_match = re.search(self.config.card_pattern, clean_line)
                current_card = card_match.group(1).replace(" ", "")[-4:]  # Last 4 digits
                current_block = [clean_line]
                capture_active = True
                continue
            
            # Only capture between start and SUB TOTAL
            if current_card and capture_active:
                current_block.append(clean_line)
                if any(kw in clean_line for kw in self.config.end_keywords):
                    blocks[current_card] = current_block
                    current_card = None
                    current_block = []
                    capture_active = False
        
        return blocks

    def process_block(self, block: List[str], full_text: List[str]) -> Dict[str, float]:
        """Enhanced data extraction with precise rules"""
        data = {
            "previous_balance": 0.0,
            "credit_payment": 0.0,  # Will store as negative values
            "retail_purchases": 0.0,
            "debit_fees": 0.0,
            "balance_due": 0.0,
            "minimum_payment": 0.0
        }

        # Track previous line for currency detection
        prev_line = ""
        
        # Process block lines
        i = 0
        while i < len(block):
            line = block[i].strip()
            clean_line = ' '.join(line.split())
            
            # Previous Balance (line after keyword)
            if "PREVIOUS BALANCE FROM LAST STATEMENT" in clean_line and i+1 < len(block):
                amount = self.extract_amount(block[i+1])
                if amount:
                    data["previous_balance"] = amount
                i += 1  # Skip amount line
            
            # Credit Payments (only lines with CR suffix)
            elif "CR" in clean_line:
                amount = self.extract_amount(clean_line.replace("CR", ""))
                if amount:
                    data["credit_payment"] -= abs(amount)  # Store as negative value
            
            # Retail Purchases (standalone amounts not in foreign currency)
            elif (self.is_amount_line(clean_line) and 
                  not any(curr in prev_line for curr in self.config.foreign_currencies) and
                  not self.is_financial_keyword_line(prev_line)):
                amount = self.extract_amount(clean_line)
                if amount and amount > 0:  # Only positive amounts
                    data["retail_purchases"] += amount
            
            # Balance Due (from SUB TOTAL line)
            elif "SUB TOTAL" in clean_line:
                amount = self.extract_amount(block[i+1])
                if amount:
                    data["balance_due"] = amount
            
            prev_line = clean_line
            i += 1

        # Extract minimum payment from full text
        for i, line in enumerate(full_text):
            if "TOTAL Minimum Payment" in line:
                # Look upwards for the amount
                for j in range(i-1, max(-1, i-5), -1):
                    amount = self.extract_amount(full_text[j])
                    if amount:
                        data["minimum_payment"] = amount
                        break
        
        return data

    def is_amount_line(self, line: str) -> bool:
        """Strict check for standalone amounts"""
        line = line.strip()
        return (re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})*\.\d{2}', line) is not None 
                and not any(c.isalpha() for c in line))

    def is_financial_keyword_line(self, line: str) -> bool:
        """Check if line contains financial keywords"""
        keywords = (self.config.previous_balance_keywords + 
                   self.config.credit_payment_keywords +
                   self.config.subtotal_keywords +
                   self.config.minimum_payment_keywords)
        return any(kw in line for kw in keywords)