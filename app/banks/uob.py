from credit_card_tracker.app.banks.base_bank import BaseBank, BankConfig
import re
from typing import List, Dict, Union
from credit_card_tracker.logger import get_logger

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


    def process_block(self, block: List[str]) -> Dict[str,Union[float,str]]:
        logger.debug("Processing a block of financial data.")
        data = self.base_data()
        i = 0
        while i < len(block):
            line = block[i].strip()
            next_line = block[i+1].strip() if i+1 < len(block) else ""
            logger.debug(f"Processing line: {line}")

            try:
                text = block[1].strip()
                matches =re.findall(r"[A-Za-z]+", text)
                result = " ".join(matches).strip()
                if result:
                    data["card_name"] = result
                    logger.debug(f"Extracted card name: {data['card_name']}")

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

    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        logger.debug("Starting to create blocks from statement lines.")
        blocks = {}
        current_card = None
        current_block = []
        in_block = False
        found_start = False

        for line in lines:
            clean_line = ' '.join(line.split())
            logger.debug(f"Processing line: {clean_line}")
            
            try:
                if not found_start:
                    if any(start_kw in clean_line for start_kw in self.config.start_keywords):
                        found_start = True  # Now we can start parsing
                        logger.debug("Found start keyword. Beginning block parsing.")
                    continue  # Skip until start keyword is found

                # Detect card number
                card_match = re.search(self.config.card_pattern, clean_line)
                if card_match:
                    if current_card:
                        logger.debug(f"Ending block for card: {current_card}")
                        blocks[current_card] = current_block
                    current_card = card_match.group(2)
                    logger.debug(f"Detected card number: {current_card}")
                    current_block = [line]
                    two_lines_in_one =  " ".join(lines[lines.index(line)-2: lines.index(line)]).strip()
                    current_block.append(two_lines_in_one)
                    logger.info(f"Appended {two_lines_in_one} to current block for card: {current_card}")
                    in_block = True
                    continue
                
                # Detect end of block
                if in_block and any(end_kw in clean_line for end_kw in self.config.end_keywords):
                    logger.debug(f"Detected end keyword. Ending block for card: {current_card}")
                    blocks[current_card] = current_block + [line]
                    current_card = None
                    current_block = []
                    in_block = False
                    break
                
                if in_block:
                    current_block.append(line)
            except Exception as e:
                logger.error(f"Error processing line: {clean_line}. Error: {e}")

        if not blocks:
            logger.warning("No blocks were created. Check if the input lines contain valid data.")
        logger.info("Finished creating blocks")
        for key, block in blocks.items():
            logger.info(f"====Card: {key}====\n")
            logger.info("\n".join(block) + "\n\n")
        return blocks
