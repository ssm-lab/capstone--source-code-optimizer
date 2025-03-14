from logging import Logger
import logging
from typing import TypedDict

from .utils.output_manager import LoggingManager


class Config(TypedDict):
    mode: str
    loggingManager: LoggingManager | None
    detectLogger: Logger
    refactorLogger: Logger


CONFIG: Config = {
    "mode": "production",
    "loggingManager": None,
    "detectLogger": logging.getLogger("detect"),
    "refactorLogger": logging.getLogger("refactor"),
}
