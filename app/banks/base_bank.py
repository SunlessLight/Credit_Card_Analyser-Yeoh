from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
import re
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

@dataclass
class BankConfig:
    name: str
    card_pattern: str
    start_keywords: List[str]
    end_keywords: List[str]
    previous_balance_keywords: List[str]
    credit_payment_keywords: List[str]
    retail_interest_keywords: List[str]
    subtotal_keywords: List[str]
    minimum_payment_keywords: List[str]
    foreign_currencies: List[str]
    amount_pattern: str = r"(\d{1,3}(?:,\d{3})*\.\d{2})"
    credit_indicator: str = "CR"

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

    @abstractmethod
    def create_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        """Bank-specific block creation logic"""
        pass

    @abstractmethod
    def process_block(self, block: List[str], full_text: List[str]) -> Dict[str, float]:
        """Bank-specific data extraction from a block"""
        pass

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