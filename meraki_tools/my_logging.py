import logging
import os
from typing import Optional

# In-memory log storage for UI consumption
log_entries = []


class ListHandler(logging.Handler):
    """Custom logging handler that appends log messages to a shared list."""

    def emit(self, record):
        log_entry = self.format(record)
        log_entries.append(log_entry)


# Internal singleton state
_LOGGER: Optional[logging.Logger] = None
_CONFIG = {
    "enable_logging": True,
    "console_logging": False,
    "file_logging": False,
    "log_file_path": "app.log",
    "level": logging.INFO,
}


def _close_and_remove_handlers(logger: logging.Logger) -> None:
    """Remove and close all handlers to avoid Windows file lock errors."""
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass


def setup_logger(
    enable_logging: bool = True,
    console_logging: bool = False,
    file_logging: bool = False,
    *,
    log_file_path: str = "app.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Create or reconfigure a process-wide singleton logger named 'app_logger'.

    - Safe to call multiple times across modules.
    - Closes old file handlers before reconfiguring to prevent Windows file locks.
    - Appends to the log file by default.
    """
    global _LOGGER, _CONFIG

    # If configuration is unchanged, just return existing logger
    if _LOGGER is not None and _CONFIG == {
        "enable_logging": enable_logging,
        "console_logging": console_logging,
        "file_logging": file_logging,
        "log_file_path": log_file_path,
        "level": level,
    }:
        return _LOGGER

    logger = logging.getLogger("app_logger")
    logger.propagate = False
    logger.setLevel(level if enable_logging else logging.CRITICAL + 1)

    # Reconfigure: ensure previous handlers are fully closed
    _close_and_remove_handlers(logger)

    if not enable_logging:
        _LOGGER = logger
        _CONFIG = {
            "enable_logging": enable_logging,
            "console_logging": console_logging,
            "file_logging": file_logging,
            "log_file_path": log_file_path,
            "level": level,
        }
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s - %(message)s"
    )

    # Always attach the in-memory list handler
    list_handler = ListHandler()
    list_handler.setFormatter(formatter)
    logger.addHandler(list_handler)

    if console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if file_logging:
        # Resolve to absolute path for stability
        log_path = os.path.abspath(log_file_path)
        os.makedirs(os.path.dirname(log_path), exist_ok=True) if os.path.dirname(log_path) else None
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _LOGGER = logger
    _CONFIG = {
        "enable_logging": enable_logging,
        "console_logging": console_logging,
        "file_logging": file_logging,
        "log_file_path": log_file_path,
        "level": level,
    }
    return logger


def get_logger() -> logging.Logger:
    """Return the shared app logger, creating it with defaults if needed."""
    return setup_logger(
        enable_logging=_CONFIG["enable_logging"],
        console_logging=_CONFIG["console_logging"],
        file_logging=_CONFIG["file_logging"],
        log_file_path=_CONFIG["log_file_path"],
        level=_CONFIG["level"],
    )


# Keep the old main block out of the library to avoid side effects on import