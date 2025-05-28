from credit_card_tracker.logger import get_logger

logger = get_logger(__name__)

def get_password_from_bank():
     # Always ask the user for the password
    password = input(f"Enter password (leave empty if none): ").strip() or None
    logger.info("Getting password for pdf")
    return password