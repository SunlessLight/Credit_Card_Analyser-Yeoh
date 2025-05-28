# main_gui.py
from credit_card_tracker.app.gui import main
from credit_card_tracker.logger import get_logger

logger = get_logger(__name__)


if __name__ == "__main__":
    main()
