from pathlib import Path
from copy import copy
from openpyxl.worksheet import worksheet
import json
import os
from openpyxl import load_workbook
from openpyxl.styles import Font, Border, PatternFill, Protection, Alignment
from openpyxl import Workbook
from typing import Dict, List
from statement_analyser_personal.logger import get_logger
from statement_analyser_personal.app.processor_tools.json_file_handling import JSONFileHandler

logger = get_logger(__name__)

class ExcelManager(JSONFileHandler):
    def __init__(self, bank_name:str, date:Dict[str,str], results:Dict[str, Dict[str,float]]):
        self.bank_name = bank_name
        self.date = date
        self.results = results      
        logger.info(f"ExcelManager initialized for {self.bank_name}. date and results obtained")
        
    def get_record_number(self):
        logger.warning("record no entered in GUI mode. This should be handled by the GUI.")
        raise NotImplementedError("get_record_no is not available in GUI mode.")

    def set_alignment(self, ws:worksheet, record_no:int, result: Dict[str, Dict[str, float]] ):
        try:
            logger.info(f"Setting alignment for excel")
            for row in range(3+(record_no-1)*8, 10+(record_no-1)*8):
                for col in range(1, 4+len(result) ):
                    cell = ws.cell(row = row, column = col)
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        except Exception as e:
            logger.error(f"Failed to set alignment: {e}")

    def insert_header(self, ws:worksheet, record_no:int, data: Dict[str, str]):
        logger.info(f"Writing header to excel")
        list = ["Card No.", "Previous Balance", "Credit Payment", "Debit Fees", "Retail Purchases", "Balance Due", "Minimum Payment"]
        ws[f"A{3 + (record_no -1)*8}"] = "Record No."
        ws[f"A{4 + (record_no -1)*8}"] = data["record_number"]
        ws.column_dimensions["A"].width = 10
        ws[f"B{3 + (record_no -1)*8}"] = "Statement Date"
        ws[f"B{4 + (record_no -1)*8}"] = data["statement_date"]
        ws[f"B{8 + (record_no -1)*8}"] = "Payment Due Date"
        ws[f"B{9 + (record_no -1)*8}"] = data["payment_date"]
        ws.column_dimensions["B"].width = 16
        ws.column_dimensions["C"].width = 16.
        for i, header in enumerate(list, start = 1):
            i += 2+(record_no-1)*8
            ws[f"C{i}"] = header
        logger.info(f"Headers written successfully")

    def insert_key_value(self, ws:worksheet, record_no:int, result: Dict[str, Dict[str,float]]):
        logger.info(f"Writing result to excel")
        for i, (card, values) in enumerate(result.items(), start = 1):
                i += 3
                ws.cell(row= 3+(record_no-1)*8, column = i, value = card)
                ws.cell(row= 3+(record_no-1)*8, column = i).font = Font(bold = True)
                ws.cell(row= 4+(record_no-1)*8, column = i, value = values["previous_balance"]),
                ws.cell(row= 5+(record_no-1)*8, column = i, value = values["credit_payment"]),
                ws.cell(row= 6+(record_no-1)*8, column = i, value = values["debit_fees"]),
                ws.cell(row= 7+(record_no-1)*8, column = i, value = values["retail_purchase"]),    
                ws.cell(row= 8+(record_no-1)*8, column = i, value = values["balance_due"]),
                ws.cell(row= 9+(record_no-1)*8, column = i, value = values["minimum_payment"]),
        logger.info(f"Excel file updated successfully")
        
    

    def create_excel_file(self, save_path = None):
        logger.info(f"Creating new Excel file")

        logger.info(f"Creating new json file")
        self.create_json_file()

        data = self.open_json()
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = self.bank_name
            logger.info(f"Worksheet {self.bank_name} created")

            self.insert_header(ws, 1, data)

            result = data["results1"]

            logger.info(f"Writing result to excel")

            self.insert_key_value(ws, 1, result)

            self.set_alignment(ws, 1, result)
        
            

            if not save_path:
                logger.error("No save_path provided for create_excel_file in GUI mode.")
                raise ValueError("No save_path provided for create_excel_file in GUI mode.")
            wb.save(save_path)
            logger.info(f"Excel file saved at: {save_path}")
        except Exception as e:
            logger.error(f"Failed to create Excel file: {e}")
            raise RuntimeError(f"Failed to create Excel file: {str(e)}")

    

    def update_excel(self, excel_path:str, record_no: int):

        logger.info(f"Getting record number")
        self.update_json(record_no)

        data = self.open_json()

        logger.info(f"loading data for updating excel")
        
        try:
            wb = load_workbook(excel_path)
            logger.info(f"Available worksheets: {wb.sheetnames}")

            if self.bank_name in wb.sheetnames:
                ws = wb[self.bank_name]
                logger.info(f"Sheet '{self.bank_name}' found in the workbook.")
            else:
                raise ValueError(f"Sheet '{self.bank_name}' not found in the workbook.")
            
            self.insert_header(ws, record_no, data)

            result = data[f"results{record_no}"]
            logger.info(f"Writing result to excel")

            self.insert_key_value(ws, record_no, result)

            
            self.set_alignment(ws, record_no, result)


            wb.save(excel_path)
            logger.info(f"Excel file updated successfully")
            

        except Exception as e:
            logger.error(f"Failed to update Excel file: {e}")
            raise RuntimeError(f"Failed to update Excel file: {str(e)}")

    def insert_new_bank(self, excel_path:str):

        logger.info(f"Creating new bank in existing excel file")

        logger.info(f"Creating new json file")
        self.create_json_file()
        
        data = self.open_json()

        try:
            wb = load_workbook(excel_path)
            ws = wb.create_sheet(self.bank_name)

            logger.info(f"Inserting header for new bank")
            self.insert_header(ws, 1, data)

            result = data["results1"]

            logger.info(f"Writing result to excel")
            self.insert_key_value(ws, 1, result)

            self.set_alignment(ws, 1, result)

            wb.save(excel_path)
            logger.info(f"Excel file updated successfully")
            

        except Exception as e:
            logger.error(f"Failed to create Excel file: {e}")
            raise RuntimeError(f"Failed to create Excel file: {str(e)}")

    

            



