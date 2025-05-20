from typing import Dict, Optional
from ..banks import UOB, HLB, MYB, RHB, PBB, CIMB
from .text_extractor import TextExtractor
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)


class CreditCardProcessor:
    BANK_CLASSES = {
        "UOB": UOB,
        "HLB": HLB,
        "MYB": MYB,
        "RHB": RHB,
        "PBB": PBB,
        "CIMB": CIMB,
    }
    
    def __init__(self, bank: str):
        self.bank = self.BANK_CLASSES[bank]()
        self.bank_name = bank

    def parse_statement(self, pdf_path: str) -> Dict[str, Dict[str, float]]:
        """Always generates both raw text and blocks files"""
        lines = TextExtractor.extract_text(pdf_path)  # extract_text now saves raw text
        blocks = self.bank.create_blocks(lines)
        
        TextExtractor.save_blocks(pdf_path,blocks)
        
        if hasattr(self.bank, "extract"):
            results = self.bank.extract(lines)
            dates = self.bank.process_date(lines)
            return results,dates
        else:
            results = {card: self.bank.process_block(block)
                for card, block in blocks.items()}
            dates = self.bank.process_date(lines)
            return results,dates
    
        
    

        
    