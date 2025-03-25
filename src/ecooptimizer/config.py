"""Application configuration settings and type definitions."""

from logging import Logger
import logging
from typing import TypedDict

from .utils.output_manager import LoggingManager


class Config(TypedDict):
    """Type definition for application configuration dictionary.

    Attributes:
        mode: Current application mode ('production' or 'development')
        loggingManager: Central logging manager instance
        detectLogger: Logger for code detection operations
        refactorLogger: Logger for code refactoring operations
    """

    mode: str
    loggingManager: LoggingManager | None
    detectLogger: Logger
    refactorLogger: Logger


# Global application configuration
CONFIG: Config = {
    "mode": "production",
    "loggingManager": None,
    "detectLogger": logging.getLogger("detect"),
    "refactorLogger": logging.getLogger("refactor"),
}
