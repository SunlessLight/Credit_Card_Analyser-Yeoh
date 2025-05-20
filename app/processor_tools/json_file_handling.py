import json
import os
from statement_analyser_personal.logger import get_logger
from typing import Dict, Any

logger = get_logger(__name__)

class JSONFileHandler:
    def create_json_file(self):
        data = {
            "record_number" : 1,
            "statement_date" : self.date["statement_date"],
            "payment_date" : self.date["payment_date"],
            "bank_name" : self.bank_name,
            "results1" : self.results
        }
        try:
            data_folder = os.path.join(os.path.expanduser("~"), "Documents", "Credit Card Tracker")
            os.makedirs(data_folder, exist_ok=True)
            json_path = os.path.join(data_folder, f"{self.bank_name}.json")
            with open(json_path, "w") as f:
                json.dump(data, f, indent = 2)
                logger.info(f"JSON file created successfully at {self.bank_name}.json")
            
        except Exception as e:
            logger.error(f"Failed to create JSON file: {e}")
            raise RuntimeError(f"Failed to create JSON file: {str(e)}")
        
    def update_json(self, record_no:int):
        data = {
            "record_number" : record_no,
            "statement_date" : self.date["statement_date"],
            "payment_date" : self.date["payment_date"],
            "bank_name" : self.bank_name,
            f"results{record_no}" : self.results
        }

        try:
            data_folder = os.path.join(os.path.expanduser("~"), "Documents", "Credit Card Tracker")
            os.makedirs(data_folder, exist_ok=True)
            json_path = os.path.join(data_folder, f"{self.bank_name}.json")
            with open(json_path, "w") as f:
                json.dump(data, f, indent = 2)
                logger.info(f"JSON file updated successfully at {self.bank_name}.json")
            
        except Exception as e:
            logger.error(f"Failed to create JSON file: {e}")
            raise RuntimeError(f"Failed to create JSON file: {str(e)}")
        
    def open_json(self):
        try:
            data_folder = os.path.join(os.path.expanduser("~"), "Documents", "Credit Card Tracker")
            json_path = os.path.join(data_folder, f"{self.bank_name}.json")
            with open(json_path, "r") as f:
                data = json.load(f)
                logger.info(f"JSON file opened successfully at {self.bank_name}.json")
            return data
        except FileNotFoundError:
            logger.error(f"JSON file not found: {self.bank_name}.json")
            raise RuntimeError(f"JSON file not found: {self.bank_name}.json")
