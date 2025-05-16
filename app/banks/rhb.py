from statement_analyser_personal.app.banks.base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Optional
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class RHB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching RHB bank configuration.")
        return BankConfig(
            name="RHB",
            card_pattern=r"(\d{4}-\d{4}-\d{4}-(\d{4}))",
            start_keywords=["Tarikh Transaksi"],
            end_keywords=["TOTAL OUTSTANDING BALANCE / JUMLAH BAKI TERKINI","Total / Jumlah"],
            previous_balance_keywords=["OPENING BALANCE / BAKI MULA"],
            credit_payment_keywords=["CR"],
            debit_fees_keywords=["interest charged"],
            balance_due_keywords=["CLOSING BALANCE / BAKI AKHIR"],
            retail_purchase_keywords=[],
            minimum_payment_keywords=[],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"],
            statement_date_keyword= ["Statement Date"],
            payment_date_keyword=["Tarikh Bayaran Matang"],
            
        )

    def process_date(self, lines: List[str]) -> Dict[str,str]:
        logger.debug("Processing statement and payment dates.")
        date = self.date_dict()
        subset = lines[0:50]
        i = 0
        while i < len(subset):
            line = subset[i].strip()
            next_line = subset[i+1].strip()
            logger.debug(f"processing line: {line}")
            try:
                if any(kw in line for kw in self.config.statement_date_keyword):
                    date["statement_date"] = self.extract_date(line)
                    logger.debug(f"Extracted statement date : {date["statement_date"]}")
                    
                elif any(kw in line for kw in self.config.payment_date_keyword):
                    date["payment_date"] = self.extract_date(next_line)
                    logger.debug(f"Extracted payment date : {date["payment_date"]}")
                    i += 1
                elif date["statement_date"] and date["payment_date"]:
                    logger.debug("Both statement and payment dates have been extracted, stopping further processing.")
                    break
            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")
            i += 1  
        logger.debug(f"Extracted dates: {date}")
        return date

    def process_block(self, block: List[str]) -> Dict[str, float]:
        logger.debug("Processing a block of financial data.")
        data = self.base_data()

        i = 0
        while i < len(block):
            line = block[i].strip()
            next_line = block[i+1].strip() if i+1 < len(block) else ""
            logger.debug(f"Processing line: {line}")

            try:
                # Previous Balance , amount on next line
                if any(kw in line for kw in self.config.previous_balance_keywords):
                    self.extract_previous_balance(next_line, data)
                    i += 1  # Skip next line since we've processed it

                # Credit Payments (marked with "CR")
                elif any(kw in line for kw in self.config.credit_payment_keywords):
                    self.extract_credit_payment(line, data)

                # Retail Interest/Fees
                elif any(kw in line for kw in self.config.debit_fees_keywords):
                    self.extract_debit_fees(next_line, data)
                    
                    i += 1

                # Subtotal/Balance Due
                elif any(kw in line for kw in self.config.balance_due_keywords):
                    self.extract_balance_due(next_line, data)
                    i += 1

                # Retail Purchases (individual transactions)
                elif self.is_amount_line(line) :
                    self.extract_retail_purchase(line, data)

            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")

            i += 1

        logger.debug(f"Processed block data: {data}")
        for key in data:
            data[key] = round(data[key],2)
        return data

    def extract_minimum_payments_from_text(self, lines: List[str]) -> Dict[str, float]:
        logger.debug("Extracting minimum payments from text.")
        
        card_minimums = {}
        for i, line in enumerate(lines):
            
            try:
                match = re.search(self.config.card_pattern, line)
                if match and i + 4 < len(lines):
                    
                    last4 = match.group(2)
                    logger.debug(f"Detected card number: {last4}")
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
        logger.debug("Starting extraction process.")
        try:
            blocks = self.create_blocks(lines)
            results = {}

            # Extract card -> minimum payment mapping from full text
            min_payments = self.extract_minimum_payments_from_text(lines)
            logger.debug(f"Minimum payments extracted: {min_payments}")
            # Process each card block
            for key, block in blocks.items():
                results[key] = self.process_block(block)
                if key in min_payments:
                    results[key]["minimum_payment"] = min_payments[key]
            logger.debug(f"Extraction results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error during extraction: {e}")
            return{}