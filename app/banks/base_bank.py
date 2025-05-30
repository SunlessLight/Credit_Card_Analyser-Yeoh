from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
import re
from credit_card_tracker.logger import get_logger

logger = get_logger(__name__)

@dataclass
class BankConfig:
    name: str
    card_pattern: str
    start_keywords: List[str]
    end_keywords: List[str]
    previous_balance_keywords: List[str]
    credit_payment_keywords: List[str]
    debit_fees_keywords: List[str]
    balance_due_keywords: List[str]
    retail_purchase_keywords: List[str]
    minimum_payment_keywords : List[str]
    foreign_currencies: List[str]
    statement_date_keyword : List[str]
    payment_date_keyword : List[str]
    date_pattern: str = r"((?:\d{2} \w{3} \d{4})|(?:\d{2} \w{3} \d{2})|(?:\d{2}/\d{2}/\d{4})|(?:\d{2}/\d{2}/\d{2})|(?:\d{4}-\d{2}-\d{2})|(?:\d{2}-\d{2}-\d{4})|(?:\d{2}-\d{2}-\d{2}))"
    amount_pattern: str = r"(\d{1,3}(?:,\d{3})*\.\d{2})"
    
   
    

class BaseBank(ABC):
    def __init__(self):
        try:
            logger.debug("Initializing BaseBank and fetching configuration.")
            self.config = self.get_config()
            logger.debug(f"Configuration loaded: {self.config}")
        except Exception as e:
            logger.error(f"Error initializing BaseBank: {e}")
            raise

    @classmethod
    @abstractmethod
    def get_config(cls) -> BankConfig:
        """Return bank-specific configuration"""
        pass
    
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
                    
                    two_lines_in_one =  " ".join(lines[lines.index(line)-2: lines.index(line)+2]).strip()
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

    @abstractmethod
    def process_block(self, block: List[str], full_text: List[str]) -> Dict[str, float]:
        """Bank-specific data extraction from a block"""
        pass
    
    @classmethod
    def base_data(self):
        return {
            "card_name" : None,
            "previous_balance": 0.00,
            "credit_payment": 0.00,
            "debit_fees": 0.00,
            "retail_purchase": 0.00,
            "balance_due": 0.00,
            "minimum_payment": 0.00
        }
    
    def extract_previous_balance(self, next_line: str, data: Dict[str, float]) -> None:
            amount = self.extract_amount(next_line.replace("CR", ""))
            if amount is not None:
                data["previous_balance"] = -amount if "CR" in next_line else amount
                logger.debug(f"Extracted previous balance: {data['previous_balance']}")
            else:
                data["previous_balance"] = 0.00
                logger.debug("No amount found for previous balance.")
            

    def extract_credit_payment(self, line:str, data:Dict[str,float]) -> None:
            amount = self.extract_amount(line.replace("CR", "") if "CR" in line else line)
            
            if amount is not None:
                data["credit_payment"] -= amount
                logger.debug(f"Extracted credit payment: {data["credit_payment"]}")
            else:
                data["credit_payment"] -= 0.00
                logger.debug("No amount found for credit payment.")


    def extract_debit_fees(self, next_line:str, data:Dict[str,float]) -> None:
        
            amount = self.extract_amount(next_line)
            if amount is not None:
                data["debit_fees"] += amount
                logger.debug(f"Extracted debit fees: {data["debit_fees"]}")
            else:
                data["debit_fees"] = 0.00
                logger.debug("No amount found for debit fees.")
            
    
    def extract_balance_due(self, next_line:str, data:Dict[str,float]) -> None:
        amount = self.extract_amount(next_line.replace("CR", ""))
        if amount is not None:
                data["balance_due"] = -amount if "CR" in next_line else amount
                logger.debug(f"Extracted balance due: {data['balance_due']}")
        else:
            data["balance_due"] = 0.00
            logger.debug("No amount found for subtotal.")

    def extract_minimum_payment(self, next_line:str, data:Dict[str,float]) -> None:
        amount = self.extract_amount(next_line.replace("CR", ""))
        if amount is not None:
                data["minimum_payment"] = -amount if "CR" in next_line else amount
                logger.debug(f"Extracted balance due: {data['minimum_payment']}")
        else:
            data["minimum_payment"] = 0.00
            logger.debug("No amount found for minimum_payment.")

    def extract_retail_purchase(self, line:str, data:Dict[str,float]) -> None:
        amount = self.extract_amount(line)
        if amount and amount > 0:
            data["retail_purchase"] += amount
            logger.debug(f"Extracted retail purchase: {amount}")
        else:
            data["retail_purchase"] =+ 0.00
            logger.debug("No amount found for retail purchase.")
            
    def extract_amount(self, text: str) -> Optional[float]:
        logger.debug(f"Extracting amount from text: {text}")
        try:
            match = re.search(self.config.amount_pattern, text)
            if match:
                amount = float(match.group(1).replace(",", ""))
                logger.debug(f"Extracted amount: {amount}")
                return amount
            else:
                logger.warning(f"No amount found in text: {text}")
                return None
        except Exception as e:
            logger.error(f"Error extracting amount from text: {text}. Error: {e}")
            return None

    def date_dict(self) -> Dict[str,str]:
        return {
            "statement_date": "",
            "payment_date": ""
        }

    def extract_date(self, line:str) -> str:
        logger.debug(f"Extracting date from line: {line}")
        try:
            match = re.search(self.config.date_pattern, line)
            if match:
                date = match.group(1)
                logger.debug(f"Extracted date: {date}")
                return date
            else:
                logger.warning(f"No date found in line: {line}")
                return None
        except Exception as e:
            logger.error(f"Error extracting date from line: {line}. Error: {e}")


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