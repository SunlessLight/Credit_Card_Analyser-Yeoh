from pathlib import Path
import sys
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

def get_resource_path(filename: str) -> Path:
    if getattr(sys, 'frozen', False):  # EXE mode
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / filename
