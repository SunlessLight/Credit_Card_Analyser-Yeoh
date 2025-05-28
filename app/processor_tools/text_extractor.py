import fitz
import re
from typing import List
from credit_card_tracker.logger import get_logger


logger = get_logger(__name__)

bank_pdf_matching = {
    "UOB" : { "start" : 1,
             "end": 10 ,
             "keyword": ["UOB", "United Overseas Bank"]},
    "RHB" : { "start" : 1,
             "end": 50 ,
             "keyword": ["RHB Bank", "RHB Bank Berhad"]},
    "PBB" : { "start" : 50,
             "end": 80 ,
             "keyword": ["PUBLIC BANK BERHAD"]},
    "CIMB" : { "start" : 1,
             "end": 30 ,
             "keyword": ["CIMB", "cimb"]},
    "MYB" : { "start" : 1,
             "end": 30 ,
             "keyword": ["Maybank", "MAYBANK"]},
    "HLB" : { "start" : 50,
             "end": 80 ,
             "keyword": ["hlb", "Hong Leong Bank Berhad"]},
}

class TextExtractor:
    @staticmethod
    def extract_text(pdf_path: str,bank_name:str,  password: str = None) -> List[str]:
        """Extract text from PDF and automatically save raw text file"""
        try:
            
            
            doc = fitz.open(pdf_path)
            if doc.is_encrypted:
                if not password or not doc.authenticate(password):
                    raise RuntimeError("Incorrect password. Please try again.")
                        
            logger.info("Received correct password. Proceeding with text extraction.")
            
            lines = [
                line.strip() for page in doc
                for line in page.get_text("text").split("\n")
                if line.strip()
            ]

            details = bank_pdf_matching[bank_name]
            logger.info(f"Loading details for {bank_name}:\n{details}")
            subset_long_lines = " ".join(lines[details["start"]:details["end"]+1])
            if not all (re.search(kw, subset_long_lines) for kw in details["keyword"]):
                logger.info(f"Pdf not matched with bank.")
                raise RuntimeError(f"PDF MATCHING ERROR")

            
                 
            
            logger_lines = "\n".join(lines)
            logger.info(f"Extracted text for {bank_name}:\n {logger_lines}")
            
            return lines
            
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {str(e)}")

    