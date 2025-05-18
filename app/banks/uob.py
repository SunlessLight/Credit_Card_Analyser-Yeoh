from statement_analyser_personal.app.banks.base_bank import BaseBank, BankConfig
import re
from typing import List, Dict
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class UOB(BaseBank):


    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching UOB bank configuration.")
        return BankConfig(
            name="UOB",
            card_pattern=r"\*\*(\d{4}-\d{4}-\d{4}-(\d{4}))\*\*",
            start_keywords=["Transaction Amount"],
            end_keywords=["END OF STATEMENT"],
            previous_balance_keywords=["PREVIOUS BAL"],
            credit_payment_keywords=["CR"],
            debit_fees_keywords=["RETAIL INTEREST"],
            balance_due_keywords=["SUB-TOTAL"],
            retail_purchase_keywords= [],
            minimum_payment_keywords=["MINIMUM PAYMENT DUE"],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP"],
            statement_date_keyword=["Tarikh Penyata"],
            payment_date_keyword=["Tarikh Akhir Bayaran"],
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

                # Subtotal/Balance Due
                elif any(kw in line for kw in self.config.balance_due_keywords):
                    self.extract_balance_due(next_line, data)
                    i += 1

                # Minimum Payment
                elif any(kw in line for kw in self.config.minimum_payment_keywords):
                    self.extract_minimum_payment(next_line, data)
                    i += 1

                # Retail Purchases
                elif self.is_amount_line(line) and not any(curr in block[i-1] for curr in self.config.foreign_currencies):
                    self.extract_retail_purchase(line, data)

                
            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")

            i += 1

        logger.debug(f"Processed block data: {data}")
        return data

