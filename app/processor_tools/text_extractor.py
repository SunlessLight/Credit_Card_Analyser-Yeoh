from pathlib import Path
import fitz
from typing import List, Optional
from statement_analyser_personal.logger import get_logger
from statement_analyser_personal.app.banks.statement_passwords import get_password_from_bank

logger = get_logger(__name__)

class TextExtractor:
    @staticmethod
    def extract_text(pdf_path: str) -> List[str]:
        """Extract text from PDF and automatically save raw text file"""
        try:
            while True:
                password = get_password_from_bank()
                doc = fitz.open(pdf_path)
                if doc.is_encrypted:
                    if not password or not doc.authenticate(password):
                        print("❌ Incorrect password. Please try again.")
                        logger.info("Incorrect password. Prompting user to ty again")
                        continue
                break
            logger.info("Received correct password. Proceeding with text extraction.")
            
            lines = [
                line.strip() for page in doc
                for line in page.get_text("text").split("\n")
                if line.strip()
            ]
            
            # Always save raw text
            text_path = str(Path(pdf_path).with_suffix('.raw.txt'))
            with open(text_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            print(f"Saved raw text to: {text_path}")
            
            return lines
            
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {str(e)}")

    @staticmethod
    def save_blocks(pdf_path: str, blocks: dict):
        try:
            """Save parsed blocks to file"""
            blocks_path = str(Path(pdf_path).with_suffix('.blocks.txt'))
            with open(blocks_path, "w", encoding="utf-8") as f:
                for card, block_lines in blocks.items():
                    f.write(f"===== Card: {card} =====\n")
                    f.write("\n".join(block_lines) + "\n\n")
            print(f"Saved blocks to: {blocks_path}")
        except Exception as e:
            logger.error(f"Encountered error: {e}")