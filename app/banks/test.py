from statement_analyser_personal.app.banks import UOB, HLB, MYB, RHB, CIMB, PBB
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

class TestUOB():
     
     def __init__(self):
          self.pdf = r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\20250226 eStatement_uob cc.pdf"
          self.password = ""
          self.lines = extract_lines(self.pdf, self.password)
          self.bank = UOB()

     def test_create_blocks(self):
          return create_blocks(self.bank, self.lines)
     
     def test_process_block(self):
          result = {}
          blocks = self.test_create_blocks()
          for key, block in blocks.items():
               result[key] = self.bank.process_block(block)
          return result
     
     def test_get_dates(self):
          return self.bank.process_date(self.lines)
        
          
class TestHLB():
     def __init__(self):
          self.pdf = r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\WISE VISA GOLD 032025.pdf"
          self.password = ""
          self.lines = extract_lines(self.pdf, self.password)
          self.bank = HLB()

     def test_create_blocks(self):
          return create_blocks(self.bank, self.lines)
     
     def test_process_block(self):
          return self.bank.extract(self.lines)
     
     def test_get_dates(self):
          return self.bank.process_date(self.lines)
     
     
class TestCIMB():
     def __init__(self):
          self.pdf = r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\WISE VISA GOLD 032025.pdf"
          self.password = ""
          self.lines = extract_lines(self.pdf, self.password)
          self.bank = HLB()

     def test_create_blocks(self):
          return create_blocks(self.bank, self.lines)
     
     def test_process_block(self):
          return self.bank.extract(self.lines)
     
     def test_get_dates(self):
          return self.bank.process_date(self.lines)

class TestMYB():
     def __init__(self):
          self.pdf = r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\WISE VISA GOLD 032025.pdf"
          self.password = ""
          self.lines = extract_lines(self.pdf, self.password)
          self.bank = HLB()

     def test_create_blocks(self):
          return create_blocks(self.bank, self.lines)
     
     def test_process_block(self):
          return self.bank.extract(self.lines)
     
     def test_get_dates(self):
          return self.bank.process_date(self.lines)

class TestPBB():
     def __init__(self):
          self.pdf = r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\WISE VISA GOLD 032025.pdf"
          self.password = ""
          self.lines = extract_lines(self.pdf, self.password)
          self.bank = HLB()

     def test_create_blocks(self):
          return create_blocks(self.bank, self.lines)
     
     def test_process_block(self):
          return self.bank.extract(self.lines)
     
     def test_get_dates(self):
          return self.bank.process_date(self.lines)

class TestRHB():
     def __init__(self):
          self.pdf = r"c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\WISE VISA GOLD 032025.pdf"
          self.password = ""
          self.lines = extract_lines(self.pdf, self.password)
          self.bank = HLB()

     def test_create_blocks(self):
          return create_blocks(self.bank, self.lines)
     
     def test_process_block(self):
          return self.bank.extract(self.lines)
     
     def test_get_dates(self):
          return self.bank.process_date(self.lines)


#hlb 1  c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\WISE VISA GOLD 032025.pdf
#     2  c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\second record\WISE VISA GOLD 042025.pdf

# pbb 02APR1969
#     1 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\PBB_EMAIL_STMT_C55040595429_20250206.PDF
#     2 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\second record\PBB_EMAIL_STMT_C55040088986_20250406.PDF

# cimb t@026096
#    1  c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\1220250328202503291638530002021.PDF
#    2  c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\second record\1220250428202504291639270002004-cimb.PDF

# myb 02Apr1969
#    1 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\315015284_20250321-mbb.pdf
#      2 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\second record\359353840_20250421-mbb.pdf

# rhb 6096690402
#     1 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\cc_ind_con_060962_20250324_0000226-rhb.pdf
#     2 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\second record\cc_ind_con_060962_20250424_0000228-rhb.pdf

#uob 1 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\first record\20250226 eStatement_uob cc.pdf
#    2 c:\Users\User\OneDrive\Documents\Credit_card_programme\credit_card_statements\second record\eStatement_76605.76854609993.pdf

# python -m statement_analyser_personal.app.banks.test_block