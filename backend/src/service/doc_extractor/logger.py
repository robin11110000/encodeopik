import logging
import sys


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured logger.

    - Logs to stdout
    - Simple, beginner-friendly format
    - Default level INFO (override via LOG_LEVEL env or code if needed)
    """
    logger = logging.getLogger(name if name else __name__)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.propagate = False
    return logger



