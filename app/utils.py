import logging
import hashlib
import os

# Logging configuration
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_version(file_path: str) -> str:
    with open(os.getcwd() + file_path, "rb") as f:
        file_content = f.read()
    return hashlib.md5(file_content).hexdigest()[:8]