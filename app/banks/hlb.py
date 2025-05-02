from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class HLB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching HLB bank configuration.")
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
        logger.debug("Starting to create blocks from statement lines.")
        blocks = {}
        current_card = None
        current_block = []
        capture_active = False
        
        for i, line in enumerate(lines):
            clean_line = ' '.join(line.strip().split())
            logger.debug(f"Processing line: {clean_line}")
            
            try:
                # Detect EXACT start: "WISE VISA GOLD" followed by card number in SAME line
                if "WISE VISA GOLD" in clean_line and re.search(self.config.card_pattern, clean_line):
                    card_match = re.search(self.config.card_pattern, clean_line)
                    current_card = card_match.group(1).replace(" ", "")[-4:]  # Last 4 digits
                    logger.debug(f"Detected card number: {current_card}")
                    current_block = [clean_line]
                    capture_active = True
                    continue
                
                # Only capture between start and SUB TOTAL
                if current_card and capture_active:
                    current_block.append(clean_line)
                    if any(kw in clean_line for kw in self.config.end_keywords):
                        logger.debug(f"Ending block for card: {current_card}")
                        blocks[current_card] = current_block
                        current_card = None
                        current_block = []
                        capture_active = False
            except Exception as e:
                logger.error(f"Error processing line: {clean_line}. Error: {e}")
        
        if not blocks:
            logger.warning("No blocks were created. Check if the input lines contain valid data.")
        logger.debug(f"Finished creating blocks: {blocks.keys()}")
        return blocks

    def process_block(self, block: List[str], full_text: List[str]) -> Dict[str, float]:
        logger.debug("Processing a block of financial data.")
        data = {
            "previous_balance": 0.0,
            "credit_payment": 0.0,  # Will store as negative values
            "retail_purchases": 0.0,
            "debit_fees": 0.0,
            "balance_due": 0.0,
            "minimum_payment": 0.0
        }

        prev_line = ""
        i = 0
        while i < len(block):
            line = block[i].strip()
            clean_line = ' '.join(line.split())
            logger.debug(f"Processing line: {clean_line}")
            
            try:
                # Previous Balance
                if "PREVIOUS BALANCE FROM LAST STATEMENT" in clean_line and i+1 < len(block):
                    amount = self.extract_amount(block[i+1])
                    if amount:
                        data["previous_balance"] = amount
                        logger.debug(f"Extracted previous balance: {data['previous_balance']}")
                    i += 1
                
                # Credit Payments
                elif "CR" in clean_line:
                    amount = self.extract_amount(clean_line.replace("CR", ""))
                    if amount:
                        data["credit_payment"] -= abs(amount)
                        logger.debug(f"Extracted credit payment: {data['credit_payment']}")
                
                # Retail Purchases
                elif (self.is_amount_line(clean_line) and 
                      not any(curr in prev_line for curr in self.config.foreign_currencies) and
                      not self.is_financial_keyword_line(prev_line)):
                    amount = self.extract_amount(clean_line)
                    if amount and amount > 0:
                        data["retail_purchases"] += amount
                        logger.debug(f"Extracted retail purchases: {data['retail_purchases']}")
                
                # Balance Due
                elif "SUB TOTAL" in clean_line:
                    amount = self.extract_amount(block[i+1])
                    if amount:
                        data["balance_due"] = amount
                        logger.debug(f"Extracted balance due: {data['balance_due']}")
            except Exception as e:
                logger.error(f"Error processing line: {clean_line}. Error: {e}")
            
            prev_line = clean_line
            i += 1

        logger.debug(f"Processed block data: {data}")
        return data

    def is_amount_line(self, line: str) -> bool:
        logger.debug(f"Checking if line is an amount: {line}")
        try:
            line = line.strip()
            is_amount = (re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})*\.\d{2}', line) is not None 
                         and not any(c.isalpha() for c in line))
            logger.debug(f"Is amount line: {is_amount}")
            return is_amount
        except Exception as e:
            logger.error(f"Error checking if line is an amount: {line}. Error: {e}")
            return False

    def is_financial_keyword_line(self, line: str) -> bool:
        logger.debug(f"Checking if line contains financial keywords: {line}")
        try:
            keywords = (self.config.previous_balance_keywords + 
                        self.config.credit_payment_keywords +
                        self.config.subtotal_keywords +
                        self.config.minimum_payment_keywords)
            contains_keywords = any(kw in line for kw in keywords)
            logger.debug(f"Contains financial keywords: {contains_keywords}")
            return contains_keywords
        except Exception as e:
            logger.error(f"Error checking financial keywords in line: {line}. Error: {e}")
            return False