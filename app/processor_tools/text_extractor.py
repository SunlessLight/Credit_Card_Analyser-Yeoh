from pathlib import Path
import fitz
import os
from typing import List, Optional
from statement_analyser_personal.logger import get_logger
from statement_analyser_personal.app.banks.statement_passwords import get_password_from_bank

logger = get_logger(__name__)

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
            logger_lines = "\n".join(lines)
            logger.info(f"Extracted text for {bank_name}:\n {logger_lines}")
            
            return lines
            
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {str(e)}")

    