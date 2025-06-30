# backend/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR   = Path("logs")
LOG_FILE  = LOG_DIR / "api.log"
LOG_DIR.mkdir(exist_ok=True)

def setup_logging() -> None:
    """Configure root logger & uvicorn loggers."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # ───── Root logger → file (rotating) ─────
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(fmt, datefmt))

    # ───── Root logger → console ─────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt, datefmt))

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
    )

    # Sync uvicorn loggers với root
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).handlers = []
        logging.getLogger(uvicorn_logger).propagate = True
