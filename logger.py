import logging
from .config import DEBUG

# Create a logger
def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if DEBUG else logging.WARNING)

    # Create a file handler
    file_handler = logging.FileHandler("app.log", mode="a")
    file_handler.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    file_formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG else logging.WARNING)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger