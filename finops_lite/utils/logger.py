"""
Logging configuration for FinOps Lite.
Professional logging with structured output and rich formatting.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logger(
    name: str = "finops_lite",
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Set up structured logging for FinOps Lite.

    Args:
        name: Logger name
        verbose: Enable debug logging
        quiet: Only log warnings and errors
        log_file: Optional file to write logs to

    Returns:
        Configured logger instance
    """
    # Determine log level
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler with Rich formatting
    console = Console(stderr=True)
    rich_handler = RichHandler(
        console=console,
        show_time=verbose,
        show_path=verbose,
        rich_tracebacks=True,
        tracebacks_show_locals=verbose,
    )

    # Set format
    if verbose:
        format_string = "%(name)s: %(message)s"
    else:
        format_string = "%(message)s"

    rich_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(rich_handler)

    # File handler if specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for files

        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_default_log_file() -> Path:
    """Get default log file path."""
    log_dir = Path.home() / ".config" / "finops" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d")
    return log_dir / f"finops-lite-{timestamp}.log"


class OperationLogger:
    """Context manager for logging operations with structured output."""

    def __init__(
        self, logger: logging.Logger, operation: str, details: Optional[str] = None
    ):
        self.logger = logger
        self.operation = operation
        self.details = details
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        msg = f"Starting {self.operation}"
        if self.details:
            msg += f": {self.details}"
        self.logger.info(msg)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation} in {duration.total_seconds():.2f}s"
            )
        else:
            self.logger.error(
                f"Failed {self.operation} after {duration.total_seconds():.2f}s: {exc_val}"
            )

        return False  # Don't suppress exceptions
