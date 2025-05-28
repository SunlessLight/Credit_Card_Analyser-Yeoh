from statement_analyser_personal.app.banks.base_bank import BaseBank, BankConfig
import re
from typing import List, Dict
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

class CIMB(BaseBank):
    
    @classmethod
    def get_config(cls) -> BankConfig:
        logger.debug("Fetching CIMB bank configuration.")
        return BankConfig(
            name="CIMB",
            card_pattern = r"(\d{4}-\d{4}-\d{4}-(\d{4}))",
            start_keywords=["Transaction Details / Transaksi Terperinci"],
            end_keywords=["IMPORTANT INFORMATION / MAKLUMAT PENTING", "Summary of Your Total Relationship Bonus Points / Ringkasan Mata Ganjaran "],
            previous_balance_keywords=["PREVIOUS BALANCE"],
            credit_payment_keywords=["CR"],
            debit_fees_keywords=["FINANCE CHARGES"],
            balance_due_keywords=["STATEMENT BALANCE"],
            retail_purchase_keywords= [],
            minimum_payment_keywords= [],
            foreign_currencies=["AUD", "USD", "IDR", "SGD", "THB", "PHP", "GBP"],
            statement_date_keyword=["Tarikh Akhir Bayaran"],
            payment_date_keyword=[]
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
                    date["payment_date"] = self.extract_date(subset[i+2])
                    logger.debug(f"Extracted statement date : {date["statement_date"]}")
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
                    self.extract_credit_payment(line, data)

                # Retail Interest/Fees
                elif any(kw in line for kw in self.config.debit_fees_keywords):
                    self.extract_debit_fees(next_line, data)
                    i += 1

                # Subtotal/Balance Due
                elif any(kw in line for kw in self.config.balance_due_keywords):
                    self.extract_balance_due(next_line, data)
                    i += 1

                # Retail Purchases
                elif self.is_amount_line(line) and not any(curr in block[i-1] for curr in self.config.foreign_currencies):
                    self.extract_retail_purchase(line, data)

            except Exception as e:
                logger.error(f"Error processing line: {line}. Error: {e}")

            i += 1

        logger.debug(f"Processed block data: {data}")
        for key in data:
            if isinstance(data[key],(int,float)):
                data[key] = round(data[key],2)
                logger.info(f"Rounded amount : {data[key]}")
        logger.info(f"Final rounded data: {data}")
        return data

    def extract_minimum_payments_and_name_from_text(self, lines: List[str]) -> Dict[str, float]:
        logger.debug("Extracting minimum payments from text.")
        data =  {}
        for i, line in enumerate(lines):
            try:
                match = re.search(self.config.card_pattern, line)
                if match and i + 4 < len(lines):
                    last4 = match.group(2)
                    logger.debug(f"Detected card number: {last4}")
                    if last4 not in data:
                        data[last4] = {}
                    amount = self.extract_amount(lines[i + 4])  
                    data[last4]["minimum_payment"] = 0.00
                    if amount is not None:
                        logger.info("Inserting amount into data dict")
                        data[last4]["minimum_payment"] = amount
                        logger.debug(f"Extracted minimum payment for card {last4}: {amount}")
                    text = lines[i+1]
                    logger.info(f"Starting extracting card name from line: {text}")
                    matches = re.findall(f"[A-Za-z]+", text)
                    result = " ".join(matches).strip()
                    if result:
                        data[last4]["card_name"] = result
                        logger.debug(f"Extracted card name for {last4}: {result}")
                if any(end_kw in line for end_kw in self.config.end_keywords):
                    break
            except Exception as e:
                logger.error(f"Error extracting minimum payment from line: {line}. Error: {e}")

        if not data:
            logger.warning("No minimum payments were extracted. Check if the input lines contain valid data.")
        else:
            logger.debug(f"Extracted minimum payments: {data}")
            return data

    def extract(self, lines: List[str]) -> Dict[str, Dict[str, float]]:
        logger.debug("Starting extraction process.")
        try:
            blocks = self.create_blocks(lines)
            results = {}

            # Extract card -> minimum payment mapping from full text
            card = self.extract_minimum_payments_and_name_from_text(lines)
            logger.debug("Loading card name and result which contains minimum payment and card name")

            # Process each card block
            for key, block in blocks.items():
                logger.debug(f"Processing block for card: {key}")
                results[key] = self.process_block(block)
                if key in card:
                    logger.info(f"adding min pay and card name")
                    results[key]["minimum_payment"] = card[key]["minimum_payment"]
                    results[key]["card_name"] = card[key]["card_name"]
                    logger.info(f"Finished inserting card name and minimum payment for card:{key}")

            logger.debug(f"Extraction results: {results}")
            return results
        except Exception as e:
            logger.error(f"Error during extraction process. Error: {e}")
            return {}

    