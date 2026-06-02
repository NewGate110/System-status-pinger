import os
import sys
import logging
import socket
import time
import subprocess
from datetime import datetime, timezone

import psutil
import requests
from dotenv import load_dotenv


def load_config() -> dict:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)
    if not chat_id:
        print("ERROR: TELEGRAM_CHAT_ID is not set.", file=sys.stderr)
        sys.exit(1)
    return {"token": token, "chat_id": chat_id}


def setup_logging(log_path: str = "/var/log/pinger.log") -> logging.Logger:
    logger = logging.getLogger("pinger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(handler)
    return logger


def check_connectivity(retries: int = 3, wait: int = 30) -> bool:
    for attempt in range(1, retries + 1):
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            if attempt < retries:
                time.sleep(wait)
    return False


def get_emoji(value: float, warn: float, crit: float) -> str:
    if value > crit:
        return "🔴"
    if value > warn:
        return "⚠️"
    return "✅"
