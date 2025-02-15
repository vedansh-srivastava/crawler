import json
import os
import sys

LOG_FILE = "logs/crawler.log"

# Ensure the logs directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log(message, error=False):
    """Logs messages to console and a file."""
    prefix = "❌ ERROR:" if error else "ℹ️ INFO:"
    log_message = f"{prefix} {message}"
    print(log_message)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

    if error:
        sys.stderr.write(log_message + "\n")

def load_start_urls(file_path):
    """Loads start URLs from a file."""
    if not os.path.exists(file_path):
        log(f"⚠️ Start URLs file {file_path} not found!", error=True)
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]
    
    log(f"📄 Loaded {len(urls)} start URLs from {file_path}")
    return urls
