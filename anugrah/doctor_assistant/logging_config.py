import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_LEVEL = os.getenv("DA_LOG_LEVEL", "INFO").upper()
_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")

# Ensure log directory exists
os.makedirs(_LOG_DIR, exist_ok=True)

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_file_handler = RotatingFileHandler(
    _LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(_formatter)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)

_initialized_loggers = set()

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger with rotating file handler and console output.
    Set level via env DA_LOG_LEVEL. Logs to doctor_assistant/logs/app.log.
    """
    logger = logging.getLogger(name)
    if name not in _initialized_loggers:
        logger.setLevel(_LOG_LEVEL)
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
        logger.propagate = False
        _initialized_loggers.add(name)
    return logger
