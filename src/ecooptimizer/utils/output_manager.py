"""Logging and file output management utilities."""

from enum import Enum
import json
import logging
from pathlib import Path
import shutil
from typing import Any


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

    def __init__(self, logs_dir: Path = DEV_OUTPUT / "logs", production: bool = False):
        """Initializes logging directory structure and configures loggers.

        Args:
            logs_dir: Directory to store log files
            production: Whether to run in production mode
        """
        self.production = production
        self.logs_dir = logs_dir

        self._initialize_output_structure()
        self.log_files = {
            "main": self.logs_dir / "main.log",
            "detect": self.logs_dir / "detect.log",
            "refactor": self.logs_dir / "refactor.log",
        }
        self._setup_loggers()

    def _initialize_output_structure(self) -> None:
        """Creates required directories and clears old logs if not in production."""
        if not self.production:
            DEV_OUTPUT.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def _clear_logs(self) -> None:
        """Removes existing log files while preserving the log directory structure."""
        if self.logs_dir.exists():
            for log_file in self.logs_dir.iterdir():
                if log_file.is_file():
                    log_file.unlink()
        logging.info("🗑️ Cleared existing log files.")

    def _setup_loggers(self) -> None:
        """Configures root logger and component-specific loggers."""
        logging.root.handlers.clear()
        self._configure_root_logger()

        self.loggers = {
            "detect": self._create_child_logger("detect", self.log_files["detect"]),
            "refactor": self._create_child_logger("refactor", self.log_files["refactor"]),
        }
        logging.info("📝 Loggers initialized successfully.")

    def _configure_root_logger(self) -> None:
        """Sets up the root logger with file handler and formatting."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        main_handler = logging.FileHandler(str(self.log_files["main"]), mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        main_handler.setFormatter(formatter)
        main_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(main_handler)

    def _create_child_logger(self, name: str, log_file: Path) -> logging.Logger:
        """Creates and configures a component-specific logger.

        Args:
            name: Logger name
            log_file: Path to log file

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True

        file_handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
            )
        )
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        logging.info(f"📝 Logger '{name}' initialized and writing to {log_file}.")
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
    logging.info(log_message)


def save_json_files(file_name: str, data: dict[Any, Any] | list[Any]) -> None:
    """Saves data as JSON file in the output directory.

    Args:
        file_name: Target filename
        data: Serializable data to write
    """
    file_path = DEV_OUTPUT / file_name
    file_path.write_text(json.dumps(data, cls=EnumEncoder, sort_keys=True, indent=4))
    logging.info(f"📝 {file_name} saved to {file_path!s} as JSON file")


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
    logging.info(f"📝 {new_file_name} copied to {destination_path!s}")
    return destination_path
