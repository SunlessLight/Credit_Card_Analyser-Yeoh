from statement_analyser_personal.app.banks.base_bank import BaseBank, BankConfig
import re
from typing import List, Dict
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)


class MYB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching MYB bank configuration.")
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
        logger.debug("Starting to create blocks from statement lines.")
        blocks = {}
        current_card = None
        current_block = []
        capture_active = False

        i = 0
        while i < len(lines):
            clean_line = ' '.join(lines[i].strip().split())
            logger.debug(f"Processing line: {clean_line}")

            try:
                if "MASTERCARD CLASSIC" in clean_line and re.search(self.config.card_pattern, clean_line):
                    if current_card and current_block:
                        logger.debug(f"Ending block for card: {current_card}")
                        blocks[current_card] = current_block

                    card_match = re.search(self.config.card_pattern, clean_line)
                    current_card = card_match.group().replace(" ", "")[-4:]
                    logger.debug(f"Detected card number: {current_card}")
                    current_block = [clean_line]
                    capture_active = True
                    i += 1
                    continue

                if capture_active:
                    current_block.append(clean_line)
                    if any(end_kw in clean_line for end_kw in self.config.end_keywords):
                        logger.debug(f"Ending block for card: {current_card}")
                        if i + 1 < len(lines):
                            current_block.append(lines[i + 1].strip())
                        blocks[current_card] = current_block
                        current_card = None
                        current_block = []
                        capture_active = False
                        i += 2
                        continue
            except Exception as e:
                logger.error(f"Error processing line: {clean_line}. Error: {e}")

            i += 1

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
            "minimum_payment": 0.0  # Will be injected later
        }

        i = 0
        while i < len(block):
            line = block[i].strip()
            logger.debug(f"Processing line: {line}")

            try:
                # Previous Balance
                if "YOUR PREVIOUS STATEMENT BALANCE" in line and i + 1 < len(block):
                    amount = self.extract_amount(block[i + 1])
                    if amount:
                        data["previous_balance"] = amount
                        logger.debug(f"Extracted previous balance: {data['previous_balance']}")
                    i += 1

                # Credit Payment (JUMLAH KREDIT)
                elif any(kw in line for kw in self.config.credit_payment_keywords):
                    if i + 1 < len(block):
                        amount = self.extract_amount(block[i + 1])
                        if amount:
                            data["credit_payment"] = -abs(amount)
                            logger.debug(f"Extracted credit payment: {data['credit_payment']}")
                        i += 1

                # Retail Purchase (JUMLAH DEBIT)
                elif "(JUMLAH DEBIT)" in line and i + 1 < len(block):
                    amount = self.extract_amount(block[i + 1])
                    if amount:
                        data["retail_purchases"] += amount
                        logger.debug(f"Extracted retail purchases: {data['retail_purchases']}")
                    i += 1

                # Balance Due (under SUB TOTAL/JUMLAH)
                elif "SUB TOTAL/JUMLAH" in line and i + 1 < len(block):
                    amount = self.extract_amount(block[i + 1])
                    if amount:
                        data["balance_due"] = amount
                        logger.debug(f"Extracted balance due: {data['balance_due']}")
                    i += 1
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
                if match and i + 2 < len(lines):
                    card_number = match.group().replace(" ", "")
                    last4 = card_number[-4:]
                    amount = self.extract_amount(lines[i + 2])
                    if amount is not None:
                        card_minimums[last4] = amount
                        logger.debug(f"Extracted minimum payment for card {last4}: {amount}")
            except Exception as e:
                logger.error(f"Error extracting minimum payment from line: {line}. Error: {e}")

        if not card_minimums:
            logger.warning("No minimum payments were extracted. Check if the input lines contain valid data.")
        logger.debug(f"Extracted minimum payments: {card_minimums}")
        return card_minimums

    def extract(self, lines: List[str]) -> Dict[str, Dict[str, float]]:
        logger.debug("Starting extraction process.")
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