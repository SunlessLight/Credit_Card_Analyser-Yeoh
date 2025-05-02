from statement_analyser_personal.logger import get_logger

logger = get_logger(__name__)

def get_password_from_bank(selected_bank:str):
     # Always ask the user for the password
    password = input(f"Enter password for {selected_bank} (leave empty if none): ").strip() or None
    return password