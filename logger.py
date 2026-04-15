from datetime import datetime
import os

from core.config import Config


def ingestion_logger(logs: str):
    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(Config.LOG_FILE, "a", encoding="utf-8") as f:
        log_entry = f"[{timestamp}] [INFO] {logs}"
        f.write(log_entry + "\n")
