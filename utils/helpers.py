"""Small utilities: file helpers, logging setup, and constants."""
from __future__ import annotations
import logging
import os

LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s: %(message)s'


def setup_logging(log_file: Optional[str] = None, level=logging.INFO):
    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    logging.basicConfig(level=level, format=LOG_FORMAT, handlers=handlers)


