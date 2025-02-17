from logging import Logger
from typing import TypedDict

from .utils.output_manager import LoggingManager


class Config(TypedDict):
    mode: str
    loggingManager: LoggingManager | None
    detectLogger: Logger | None
    refactorLogger: Logger | None


CONFIG: Config = {
    "mode": "development",
    "loggingManager": None,
    "detectLogger": None,
    "refactorLogger": None,
}
