from statement_analyser_personal.app.banks.rhb import RHB
from statement_analyser_personal.app.processor_tools.text_extractor import TextExtractor
from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

def extract_lines(pdf,password):
    lines = TextExtractor.extract_text(pdf,password)
    return lines

def create_blocks(bank, lines):
    blocks = bank.create_blocks(lines)
    return blocks

def save_blocks(pdf, blocks):
    TextExtractor.save_blocks(pdf, blocks)

if __name__ == "__main__":
    pdf = r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\cc_ind_con_060962_20250324_0000226-rhb.pdf"
    password = "6096690402"
    bank = RHB()
    lines = extract_lines(pdf,password)
    result = bank.extract(lines)
    print(result)
    