# logger.py
import logging
from .config import DEBUG

# Configure basic logger settings
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.WARNING,  # Default log level
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename = "app.log",
    filemode = "a"
    )

# This returns a logger object you can reuse
def get_logger(name):
    return logging.getLogger(name)
