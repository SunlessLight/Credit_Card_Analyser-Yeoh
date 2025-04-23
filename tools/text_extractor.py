from pathlib import Path
import fitz
from typing import List, Optional

class TextExtractor:
    @staticmethod
    def extract_text(pdf_path: str, password: Optional[str] = None) -> List[str]:
        """Extract text from PDF and automatically save raw text file"""
        try:
            doc = fitz.open(pdf_path)
            if doc.is_encrypted:
                if not password or not doc.authenticate(password):
                    raise ValueError("Failed to decrypt PDF")
            
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
        """Save parsed blocks to file"""
        blocks_path = str(Path(pdf_path).with_suffix('.blocks.txt'))
        with open(blocks_path, "w", encoding="utf-8") as f:
            for card, block_lines in blocks.items():
                f.write(f"===== Card: {card} =====\n")
                f.write("\n".join(block_lines) + "\n\n")
        print(f"Saved blocks to: {blocks_path}")