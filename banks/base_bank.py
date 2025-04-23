from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
import re
from pathlib import Path

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
        self.config = self.get_config()
        
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
        match = re.search(self.config.amount_pattern, text)
        return float(match.group(1).replace(",", "")) if match else None
    
    