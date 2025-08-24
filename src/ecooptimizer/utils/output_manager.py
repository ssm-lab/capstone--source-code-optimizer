"""Logging and file output management utilities."""

from enum import Enum
import json
import logging
from pathlib import Path
import shutil
from typing import Any

logger = logging.getLogger()


DEV_OUTPUT = Path(__file__).parent / "../../../outputs"


class EnumEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Enum serialization."""

    def default(self, o):  # noqa: ANN001
        """Converts Enum objects to their values for JSON serialization.

        Args:
            o: Object to serialize

        Returns:
            Serialized value for Enums, default JSON serialization for other types
        """
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


class LoggingManager:
    """Manages log file setup and configuration for different application components."""

    logs_dir: Path = DEV_OUTPUT / "logs"
    log_files: dict[str, str] = {}  # only store file names
    production: bool = False

    @staticmethod
    def get_log_file(logger: str):
        return LoggingManager.log_files[logger]

    @staticmethod
    def initialize(
        logs_dir: Path, level: str = "INFO", production: bool = False, reset: bool = False
    ) -> None:
        """Initializes logging directory structure and configures loggers.

        Args:
            logs_dir: Directory to store log files
            level: Default logging level
            production: Whether to run in production mode
        """
        LoggingManager.production = production
        # LoggingManager.logs_dir = logs_dir

        LoggingManager._initialize_output_structure()

        if reset:
            LoggingManager._clear_logs()

        # Store only filenames here
        LoggingManager.log_files = {
            "main": "main.log",
            "detect": "detect.log",
            "refactor": "refactor.log",
        }

        LoggingManager._setup_loggers(level)
        logging.info("📝 Loggers initialized successfully.")

    @staticmethod
    def _clear_logs() -> None:
        """Removes existing log files while preserving the log directory structure."""
        if LoggingManager.logs_dir.exists():
            for log_file in LoggingManager.logs_dir.iterdir():
                if log_file.is_file():
                    log_file.unlink()
        logging.info("🗑️ Cleared existing log files.")

    @staticmethod
    def _initialize_output_structure() -> None:
        """Creates required directories and clears old logs if not in production."""
        if not LoggingManager.production:
            LoggingManager.logs_dir.parent.mkdir(exist_ok=True)
        LoggingManager.logs_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _setup_loggers(level: str = "INFO") -> None:
        """Configures root logger and component-specific loggers."""
        logging.root.handlers.clear()
        LoggingManager._configure_root_logger()

        LoggingManager._create_child_logger("detect", LoggingManager.log_files["detect"], level)
        LoggingManager._create_child_logger("refactor", LoggingManager.log_files["refactor"], level)

    @staticmethod
    def _configure_root_logger() -> None:
        """Sets up the root logger with file handler and formatting."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        main_path = LoggingManager.logs_dir / LoggingManager.log_files["main"]
        main_handler = logging.FileHandler(main_path, mode="a", encoding="utf-8")

        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        main_handler.setFormatter(formatter)
        main_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(main_handler)

    @staticmethod
    def _create_child_logger(name: str, log_file: str, log_level: str = "INFO") -> logging.Logger:
        """Creates and configures a component-specific logger.

        Args:
            name: Logger name
            log_file: Log file name

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

        log_path = LoggingManager.logs_dir / log_file
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        logging.info(f"📝 Logger '{name}' initialized and writing to {log_path}.")
        return logger


def save_file(file_name: str, data: str, mode: str, message: str = "") -> None:
    """Saves text data to a file in the output directory.

    Args:
        file_name: Target filename
        data: Content to write
        mode: File open mode
        message: Optional custom success message
    """
    file_path = DEV_OUTPUT / file_name
    with file_path.open(mode) as file:
        file.write(data)
    log_message = message if message else f"📝 {file_name} saved to {file_path!s}"
    logger.info(log_message)


def save_json_files(file_path: Path, data: dict[Any, Any] | list[Any]) -> None:
    """Saves data as JSON file in the output directory.

    Args:
        file_name: Target filename
        data: Serializable data to write
    """
    file_path.write_text(json.dumps(data, cls=EnumEncoder, sort_keys=True, indent=4))
    logger.info(f"📝 {file_path.name} saved to {file_path!s} as JSON file")


def copy_file_to_output(source_file_path: Path, new_file_name: str) -> Path:
    """Copies a file to the output directory with a new name.

    Args:
        source_file_path: Source file to copy
        new_file_name: Destination filename

    Returns:
        Path to the copied file
    """
    destination_path = DEV_OUTPUT / new_file_name
    shutil.copy(source_file_path, destination_path)
    logger.info(f"📝 {new_file_name} copied to {destination_path!s}")
    return destination_path
