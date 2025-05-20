import os
from statement_analyser_personal.logger import get_logger
from tkinter import filedialog
import tkinter as tk
logger = get_logger(__name__)

def get_bank_choice(banks):
    logger.warning("get_bank_choice called in GUI mode. This should be handled by the GUI.")
    raise NotImplementedError("get_bank_choice is not available in GUI mode.")

def select_excel_file() -> str:
    logger.warning("select_excel_file called in GUI mode. This should be handled by the GUI.")
    raise NotImplementedError("select_excel_file is not available in GUI mode.")

def select_pdf_file() -> str:
    logger.warning("select_pdf_file called in GUI mode. This should be handled by the GUI.")
    raise NotImplementedError("select_pdf_file is not available in GUI mode.")
