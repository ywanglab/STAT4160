# save this file to scripts/logsetup.py
from __future__ import annotations
import logging, os

def setup_logging(name: str = "dspt"):
    level = os.getenv("LOGLEVEL", "INFO").upper()
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger