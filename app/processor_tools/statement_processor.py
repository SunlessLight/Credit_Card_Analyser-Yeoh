from typing import Dict
from credit_card_tracker.app.banks import UOB, HLB, MYB, RHB, PBB, CIMB
from credit_card_tracker.app.processor_tools.text_extractor import TextExtractor
from credit_card_tracker.logger import get_logger

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

    def parse_statement(self, pdf_path: str,bank_name:str, password: str = None) -> Dict[str, Dict[str, float]]:
        """Always generates both raw text and blocks files"""
        lines = TextExtractor.extract_text(pdf_path, bank_name, password = password)  # extract_text now saves raw text
        blocks = self.bank.create_blocks(lines)
        
        if hasattr(self.bank, "extract"):
            results = self.bank.extract(lines)
            dates = self.bank.process_date(lines)
            logger.info("parse_statement: Starting to remove CR from card name")
            for card, result in results.items():
                name = result["card_name"]
                if "CR" in name:
                    new_name = name.replace("CR", "")
                    result["card_name"] = new_name
                    logger.info(f"Removed CR from card name: {name}. Now is {new_name}")
                else:
                    logger.info(f"No CR in card name: {name}")
            return results,dates
        else:
            results = {card: self.bank.process_block(block)
                for card, block in blocks.items()}
            dates = self.bank.process_date(lines)
            logger.info("parse_statement: Starting to remove CR from card name")
            for card, result in results.items():
                name = result["card_name"]
                if "CR" in name:
                    new_name = name.replace("CR", "")
                    result["card_name"] = new_name
                    logger.info(f"Removed CR from card name: {name}. Now is {new_name}")
            return results,dates
    
        
    

        
    