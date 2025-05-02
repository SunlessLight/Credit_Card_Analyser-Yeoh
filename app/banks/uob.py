from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class UOB(BaseBank):


    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching UOB bank configuration.")
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
        logger.debug("Starting to create blocks from statement lines.")
        blocks = {}
        current_card = None
        current_block = []
        in_block = False

        for line in lines:
            clean_line = ' '.join(line.split())
            logger.debug(f"Processing line: {clean_line}")
            
            try:
                # Detect card number
                card_match = re.search(self.config.card_pattern, clean_line)
                if card_match:
                    if current_card:
                        logger.debug(f"Ending block for card: {current_card}")
                        blocks[current_card] = current_block
                    current_card = card_match.group(2)
                    logger.debug(f"Detected card number: {current_card}")
                    current_block = [line]
                    in_block = True
                    continue
                
                # Detect end of block
                if in_block and any(end_kw in clean_line for end_kw in self.config.end_keywords):
                    logger.debug(f"Ending block for card: {current_card}")
                    blocks[current_card] = current_block + [line]
                    current_card = None
                    current_block = []
                    in_block = False
                    continue
                
                if in_block:
                    current_block.append(line)
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
            logger.debug(f"Processing line: {line}")

            try:
                # Previous Balance
                if any(kw in line for kw in self.config.previous_balance_keywords):
                    amount = self.extract_amount(next_line.replace("CR", ""))
                    if amount:
                        data["previous_balance"] = -amount if "CR" in next_line else amount
                        logger.debug(f"Extracted previous balance: {data['previous_balance']}")
                    i += 1

                # Credit Payments
                elif self.config.credit_indicator in line:
                    amount = self.extract_amount(line.replace("CR", ""))
                    if amount is not None:
                        data["credit_payment"] += -amount
                        logger.debug(f"Extracted credit payment: {data['credit_payment']}")

                # Retail Interest/Fees
                elif any(kw in line for kw in self.config.retail_interest_keywords):
                    amount = self.extract_amount(next_line)
                    if amount:
                        data["debit_fees"] += amount
                        logger.debug(f"Extracted debit fees: {data['debit_fees']}")
                    i += 1

                # Subtotal/Balance Due
                elif any(kw in line for kw in self.config.subtotal_keywords):
                    amount = self.extract_amount(next_line.replace("CR", ""))
                    if amount:
                        data["balance_due"] = -amount if "CR" in next_line else amount
                        logger.debug(f"Extracted balance due: {data['balance_due']}")
                    i += 1

                # Minimum Payment
                elif any(kw in line for kw in self.config.minimum_payment_keywords):
                    amount = self.extract_amount(next_line)
                    if amount:
                        data["minimum_payment"] = amount
                        logger.debug(f"Extracted minimum payment: {data['minimum_payment']}")
                    i += 1

                # Retail Purchases
                elif self.is_amount_line(line) and not any(curr in block[i-1] for curr in self.config.foreign_currencies):
                    amount = self.extract_amount(line)
                    if amount and amount > 0:
                        data["retail_purchases"] += amount
                        logger.debug(f"Extracted retail purchases: {data['retail_purchases']}")
            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")

            i += 1

        logger.debug(f"Processed block data: {data}")
        return data

    def is_amount_line(self, line: str) -> bool:
        logger.debug(f"Checking if line is an amount: {line}")
        try:
            line = line.strip()
            is_amount = (re.fullmatch(self.config.amount_pattern, line) is not None 
                         and not any(c.isalpha() for c in line))
            logger.debug(f"Is amount line: {is_amount}")
            return is_amount
        except Exception as e:
            logger.error(f"Error checking if line is an amount: {line}. Error: {e}")
            return False