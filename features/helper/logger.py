import os
import logging
from datetime import datetime

logger = logging.getLogger("bdd_framework_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)