from .base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class RHB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching CIMB bank configuration.")
        return BankConfig(
            name="RHB",
            card_pattern=r"(\d{4}-\d{4}-\d{4}-(\d{4}))",
            start_keywords=["YOUR TRANSACTION DETAILS / TRANSAKSI TERPERINCI ANDA"],
            end_keywords=["INSTALMENT PLAN SUMMARY / RINGKASAN PELAN ANSURAN BULANAN"],
            previous_balance_keywords=["OPENING BALANCE / BAKI MULA"],
            credit_payment_keywords="CR",
            retail_interest_keywords=["interest charged"],
            subtotal_keywords=["CLOSING BALANCE / BAKI AKHIR"],
            minimum_payment_start_keywords=["Bayaran Minima (RM)"],
            minimum_payment_end_keywords=["Total / Jumlah"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"]
        )

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        logger.debug("Starting to create blocks from statement lines.")
        """RHB-specific block creation logic"""
        blocks = {}
        current_card = None
        current_block = []
        in_block = False
        found_start = False

        for line in lines:
            clean_line = ' '.join(line.split())
            logger.debug(f"Processing line: {clean_line}")
            # Only start processing *after* start keyword is found
            if not found_start:
                if any(start_kw in clean_line for start_kw in self.config.start_keywords):
                    found_start = True  # Now we can start parsing
                    logger.debug("Found start keyword. Beginning block parsing.")
                continue  # Skip until start keyword is found

            # Detect card number (e.g., **1234-5678-9012-3456**)
            card_match = re.search(self.config.card_pattern, clean_line)
            if card_match:
                if current_card:  # Save previous card's block
                    blocks[current_card] = current_block
                    logger.debug(f"Ending block for card: {current_card}")
                current_card = card_match.group(2)  # Last 4 digits
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

    def process_block(self, block: List[str]) -> Dict[str, float]:
        logger.debug("Processing a block of financial data.")
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
            logger.debug(f"Processing line: {line}")

            try:
                # Previous Balance , amount on next line
                if any(kw in line for kw in self.config.previous_balance_keywords):
                    amount = self.extract_amount(next_line.replace("CR", ""))
                    if amount:
                        logger.debug(f"Extracted previous balance: {data['previous_balance']}")
                        data["previous_balance"] = -amount if "CR" in next_line else amount
                    i += 1  # Skip next line since we've processed it

                # Credit Payments (marked with "CR")
                elif self.config.credit_payment_keywords in line:
                    amount = self.extract_amount(line.replace("CR", ""))
                    if amount:
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

                # Retail Purchases (individual transactions)
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

    def extract_minimum_payments_from_text(self, lines: List[str]) -> Dict[str, float]:
        logger.debug("Extracting minimum payments from text.")
        
        card_minimums = {}
        for i, line in enumerate(lines):
            
            try:
                match = re.search(self.config.card_pattern, line)
                if match and i + 4 < len(lines):
                    card_number = match.group().replace("-", "")
                    last4 = card_number[-4:]
                    amount = self.extract_amount(lines[i + 4])
                    if amount is not None:
                        card_minimums[last4] = amount
                        logger.debug(f"Extracted minimum payment for card {last4}: {amount}")
                if any(end_kw in line for end_kw in self.config.end_keywords):
                    break
            except Exception as e:
                logger.error(f"Error extracting minimum payment from line: {line}. Error: {e}")

        if not card_minimums:
            logger.warning("No minimum payments were extracted. Check if the input lines contain valid data.")
        logger.debug(f"Extracted minimum payments: {card_minimums}")
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