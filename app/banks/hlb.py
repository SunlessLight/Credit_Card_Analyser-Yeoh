from credit_card_tracker.app.banks.base_bank import BaseBank, BankConfig
import re
from typing import List, Dict
from credit_card_tracker.logger import get_logger

logger = get_logger(__name__)

class HLB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching HLB bank configuration.")
        return BankConfig(
            name="HLB",
            card_pattern=r"(\d{4} \d{4} \d{4} (\d{4}))",  # Full 16-digit card number
            start_keywords=["Deskripsi Transaksi"],  # Combined pattern
            end_keywords=["TOTAL BALANCE","TOTAL Minimum Payment"],
            previous_balance_keywords=["PREVIOUS BALANCE FROM LAST STATEMENT"],
            credit_payment_keywords=["CR"],
            debit_fees_keywords=["interest charged","DCC FEE 1.00%" ],
            balance_due_keywords=["SUB TOTAL"],
            retail_purchase_keywords=[],
            minimum_payment_keywords=["TOTAL Minimum Payment"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"],
            statement_date_keyword=["Statement Date"],
            payment_date_keyword=["Payment Due Date"],
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
                    date["statement_date"] = self.extract_date(next_line)
                    logger.debug(f"Extracted statement date : {date["statement_date"]}")
                    i += 1
                elif any(kw in line for kw in self.config.payment_date_keyword):
                    date["payment_date"] = self.extract_date(subset[i+2])
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
                text = block[0].strip()
                matches = re.findall(r"[A-Za-z]+", text)
                name = " ".join(matches).strip()
                if name:
                    data["card_name"] = name
                    logger.debug(f"Extracted card name: {data['card_name']} ")
                
                # Previous Balance
                if any(kw in line for kw in self.config.previous_balance_keywords):    
                    self.extract_previous_balance(next_line, data)
                    i += 1
                
                # Credit Payments
                elif any(kw in line for kw in self.config.credit_payment_keywords):

                    self.extract_credit_payment(line,data)
                
                # Retail Interest/Fees
                elif any(kw in line for kw in self.config.debit_fees_keywords):
                    self.extract_debit_fees(next_line, data)
                    i += 1

                # Retail Purchases
                elif self.is_amount_line(line) and not any(curr in block[i-1] for curr in self.config.foreign_currencies):
                    self.extract_retail_purchase(line, data)
                
                # Subtotal/Balance Due
                elif any(kw in line for kw in self.config.balance_due_keywords):
                    self.extract_balance_due(next_line, data)
                    i += 1

            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")
            
            i += 1

        logger.debug(f"Processed block data: {data}")
        logger.info("Starting rounding values")
        for key in data:
            if isinstance(data[key], (float, int)):
                data[key] = round(data[key], 2)
        logger.info(f"Final rounded data: {data}")
        return data

    def extract_minimum_payments_from_text(self, lines: List[str]) -> Dict[str, float]:
        logger.debug("Extracting minimum payments from text.")
        card_minimums = {}
        for i, line in enumerate(lines):
            try:
                match = re.search(self.config.card_pattern, line)
                if match and i + 5 < len(lines):
                    last4 = match.group(2)
                    logger.debug(f"Detected card number: {last4}")
                    amount = self.extract_amount(lines[i + 5])
                    if amount is not None:
                        card_minimums[last4] = amount
                        logger.debug(f"Extracted minimum payment for card {last4}: {amount}")
                if any(end_kw in line for end_kw in self.config.end_keywords):
                    break
            except Exception as e:
                logger.error(f"Error extracting minimum payment from line: {line}. Error: {e}")

        if not card_minimums:
            logger.warning("No minimum payments were extracted. Check if the input lines contain valid data.")
        else:
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
                results[key] = self.process_block(block)
                if key in min_payments:
                    results[key]["minimum_payment"] = min_payments[key]

            logger.debug(f"Extraction results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error during extraction process. Error: {e}")
            return {}