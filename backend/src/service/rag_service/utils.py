"""Shared logging and configuration helpers for the RAG service."""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv


class Logger:
    """Simple stdout logger factory shared across modules."""

    @staticmethod
    def get_logger(name: str | None = None) -> logging.Logger:
        """Return a configured stdout logger at INFO level by default.

        Attaches a single handler and avoids duplicate parents."""
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


class Config:
    """Loads environment variables required for RAG integrations."""

    def __init__(self, dotenv_filename: str = ".env"):
        """Locate an .env file and expose the relevant secrets."""
        dotenv_path = self._find_env_file(dotenv_filename)
        logger = Logger.get_logger()
        if dotenv_path:
            load_dotenv(dotenv_path)
            logger.info(f"Loaded environment from: {dotenv_path}")
        else:
            logger.warning(".env file not found in current or parent directories.")

        self.aws_access_key = os.getenv("AWS_ACCESS_KEY", "")
        self.aws_secret_key = os.getenv("AWS_SECRET_KEY", "")

    def _find_env_file(self, filename: str) -> str | None:
        """Search current and parent directories for the .env file."""
        current_dir = Path(__file__).resolve().parent
        for parent in [current_dir, *current_dir.parents]:
            env_path = parent / filename
            if env_path.exists():
                return str(env_path)
        return None
