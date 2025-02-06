import json
import logging
import logging.config
import shutil
import sys
from enum import Enum
from pathlib import Path
from typing import Any, Union


class EnumEncoder(json.JSONEncoder):
    def default(self, o: Union[Enum, object]) -> str:
        """Serializes Enums using their value."""
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


class OutputConfig:
    def __init__(self, out_folder: Path, clean_existing: bool = False) -> None:
        """
        Initializes the output configuration.

        Args:
            out_folder (Path): The base output directory.
            clean_existing (bool): Whether to clear existing contents.
        """
        self.out_folder = out_folder
        self.log_folder = out_folder / "logs"
        self.main_log_file = self.log_folder / "main.log"
        self.clean_existing = clean_existing

        self._initialize_output_directory()
        self._setup_bootstrap_logging()
        logging.info("Initializing Eco-Optimizer...")

        if clean_existing:
            logging.info(
                f"Clean up requested. Deleting files from output directory: {self.out_folder}"
            )
            self._clear_output_directory()

        self._close_logging_handlers()
        self._configure_logging()
        logging.info(
            f"Initial setup complete. All output files will be directed to: {self.out_folder}\n"
        )

    def _initialize_output_directory(self):
        """Ensures the output directory and logs folder exist before setting up logging."""
        self.out_folder.mkdir(parents=True, exist_ok=True)
        self.log_folder.mkdir(exist_ok=True)

    def _setup_bootstrap_logging(self):
        """Sets up minimal logging before setting up the main log configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format="[ecooptimizer %(levelname)s @ %(asctime)s] %(message)s",
            datefmt="%H:%M:%S",
        )

    def _clear_output_directory(self):
        """Clears the output directory and ensures the required structure is recreated."""
        if self.out_folder.exists():
            try:
                shutil.rmtree(self.out_folder)
                logging.info(f"Successfully deleted entire output directory: {self.out_folder}")
            except Exception as e:
                logging.error(f"Failed to clear output directory {self.out_folder}: {e}")
                sys.exit(1)
        self._initialize_output_directory()
        self._ensure_log_structure()

    def _close_logging_handlers(self):
        """Closes all logging handlers to prevent permission issues when clearing logs."""
        handlers = logging.root.handlers[:]
        for handler in handlers:
            handler.close()
            logging.root.removeHandler(handler)

    def _ensure_log_structure(self):
        """Ensures all required log files exist."""
        required_logs = [
            "analyzers.log",
            "measurements.log",
            "refactorers.log",
            "testing.log",
            "main.log",
        ]
        for log_name in required_logs:
            log_path = self.log_folder / log_name
            log_path.touch(exist_ok=True)
            if self.clean_existing:
                Path.open(log_path, "w").close()

    def _configure_logging(self):
        """Configures the logging system with multiple loggers and handlers."""
        log_mode = "w" if self.clean_existing else "a"

        LOGGING_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "ecooptimizer_format": {
                    "format": "[ecooptimizer %(levelname)s @ %(asctime)s] %(message)s",
                    "datefmt": "%H:%M:%S",
                }
            },
            "handlers": {
                log: {
                    "class": "logging.FileHandler",
                    "filename": str(self.log_folder / f"{log}.log"),
                    "mode": log_mode,
                    "formatter": "ecooptimizer_format",
                    "level": "DEBUG",
                }
                for log in ["analyzers", "measurements", "refactorers", "testing", "main"]
            },
        }

        LOGGING_CONFIG["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "ecooptimizer_format",
            "level": "INFO",
        }

        LOGGING_CONFIG["loggers"] = {
            log: {"handlers": [log, "main", "console"], "level": "DEBUG", "propagate": False}
            for log in ["analyzers", "measurements", "refactorers", "testing"]
        }

        LOGGING_CONFIG["root"] = {"handlers": ["main", "console"], "level": "DEBUG"}

        logging.config.dictConfig(LOGGING_CONFIG)

    def save_json_files(self, filename: str, data: dict[Any, Any] | list[Any]):
        """
        Saves JSON data to a file in the output folder.

        Args:
            filename (str): The name of the file.
            data (dict[Any, Any] | list[Any]): The data to save.
        """
        file_path = self.out_folder / filename
        file_path.write_text(json.dumps(data, cls=EnumEncoder, sort_keys=True, indent=4))
        logging.info(f"Output saved to {file_path!s}")

    def copy_file_to_output(self, source_file_path: Path, new_file_name: str):
        """
        Copies a file to the output directory with a specified name.

        Args:
            source_file_path (Path): The file to be copied.
            new_file_name (str): The new file name in the output directory.
        """
        destination_path = self.out_folder / new_file_name
        shutil.copy(source_file_path, destination_path)
        logging.info(f"File copied to {destination_path!s}")
        return destination_path

    def save_file(self, filename: str, data: str, mode: str, message: str = ""):
        """
        Saves any data to a file in the output folder.

        :param filename: Name of the file to save data to.
        :param data: Data to be saved.
        :param mode: file IO mode (w,w+,a,a+,etc).
        """
        file_path = self.out_folder / filename

        # Write data to the specified file
        with file_path.open(mode) as file:
            file.write(data)

        message = message if len(message) > 0 else f"Output saved to {file_path!s}"
        logging.info(message)
