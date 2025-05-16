from statement_analyser_personal.app.banks.base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class PBB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching MYB bank configuration.")
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
        logger.debug("Starting to create blocks from statement lines.")
        blocks = {}
        current_card = None
        current_block = []
        in_block = False

        for line in lines:
            clean_line = ' '.join(line.split())
            logger.debug(f"Processing line: {clean_line}")

            # Detect card number (e.g., **1234-5678-9012-3456**)
            card_match = re.search(self.config.card_pattern, clean_line)
            if "PB GOLD MASTERCARD" in clean_line and "TAI LEE SEE" in clean_line and card_match:
                if current_card:  # Save previous card's block
                    logger.debug(f"Ending block for card: {current_card}")
                    blocks[current_card] = current_block
                full_card = card_match.group(1).replace(" ", "")  # "5472310148793103"
                current_card = full_card[-4:]         
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

        if not blocks:
            logger.warning("No blocks were created. Check if the input lines contain valid data.")
        logger.debug(f"Finished creating blocks: {blocks.keys()}")
        return blocks

    def process_block(self, block: List[str],full_text: List[str]) -> Dict[str, float]:
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

            # Previous Balance (usually appears as "PREVIOUS BAL" followed by amount on next line)
            if any(kw in line for kw in self.config.previous_balance_keywords):
                amount = self.extract_amount(next_line.replace("CR", ""))
                if amount:
                    logger.debug(f"Extracted previous balance: {data['previous_balance']}")
                    data["previous_balance"] = -amount if "CR" in next_line else amount
                i += 1  # Skip next line since we've processed it

            # Credit Payment
            elif any(kw in line for kw in self.config.credit_payment_keywords):
                if i + 1 < len(block):
                    amount = self.extract_amount(block[i + 1])
                    if amount:
                        logger.debug(f"Extracted credit payment: {data['credit_payment']}")
                        data["credit_payment"] = -abs(amount)
                    i += 1

            # Retail Interest/Fees
            elif any(kw in line for kw in self.config.retail_interest_keywords):
                amount = self.extract_amount(next_line)
                if amount:
                    logger.debug(f"Extracted balance due: {data["debit_fees"]}")
                    data["debit_fees"] += amount
                i += 1

            # Subtotal/Balance Due
            elif any(kw in line for kw in self.config.subtotal_keywords):
                amount = self.extract_amount(next_line.replace("CR", ""))
                if amount:
                    logger.debug(f"Extracted balance due: {data['balance_due']}")
                    data["balance_due"] = -amount if "CR" in next_line else amount
                i += 1

            

            # Retail Purchases (individual transactions)
            elif "This month total debit" in line and i + 1 < len(block):
                amount = self.extract_amount(block[i + 1])
                if amount:
                    logger.debug(f"Extracted retail purchases: {data['retail_purchases']}")
                    data["retail_purchases"] += amount
                i += 1

            i += 1
        logger.debug(f"Processed block data: {data}")
        return data

    def extract_minimum_payments_from_text(self, lines: List[str]) -> Dict[str, float]:
        logger.debug("Extracting minimum payments from text.")
        
        card_minimums = {}
        for i, line in enumerate(lines):
            try:
                match = re.search(self.config.card_pattern, line)
                if match and i + 3 < len(lines):
                    
                    card_number = match.group().replace(" ", "")
                    last4 = card_number[-4:]
                    
                    amount = self.extract_amount(lines[i + 3])
                    if amount is not None:
                        logger.debug(f"Extracted minimum payment for card {last4}: {amount}")
                        card_minimums[last4] = amount
                if any(end_kw in line for end_kw in self.config.minimum_payment_keywords):
                    break        
            except Exception as e:
                logger.error(f"Error extracting minimum payment from line: {line}. Error: {e}")
                 
        if not card_minimums:
            logger.warning("No minimum payments were extracted. Check if the input lines contain valid data.")
        logger.debug(f"Extracted minimum payments: {card_minimums}")
        return card_minimums

    def extract(self, lines: List[str]) -> Dict[str, Dict[str, float]]:
        logger.debug("Starting extraction process.")

        try:
            blocks = self.create_blocks(lines)
            results = {}

            # Extract card -> minimum payment mapping from full text
            min_payments = self.extract_minimum_payments_from_text(lines)
            logger.debug(f"Minimum payments extracted: {min_payments}")

            # Process each card block
            for key, block in blocks.items():
                logger.debug(f"Processing block for card: {key}")
                results[key] = self.process_block(block, lines)
                if key in min_payments:
                    results[key]["minimum_payment"] = min_payments[key]

            logger.debug(f"Extraction results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error during extraction process. Error: {e}")
            return {}

    
    