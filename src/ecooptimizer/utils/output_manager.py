from enum import Enum
import json
import logging
from pathlib import Path
import shutil
from typing import Any


DEV_OUTPUT = Path(__file__).parent / "../../../outputs"


class EnumEncoder(json.JSONEncoder):
    def default(self, o):  # noqa: ANN001
        if isinstance(o, Enum):
            return o.value  # Serialize using the Enum's value
        return super().default(o)


class LoggingManager:
    def __init__(self, logs_dir: Path = DEV_OUTPUT / "logs", production: bool = False):
        """Initializes log paths based on mode."""

        self.production = production
        self.logs_dir = logs_dir

        self._initialize_output_structure()
        self.log_files = {
            "main": self.logs_dir / "main.log",
            "detect": self.logs_dir / "detect.log",
            "refactor": self.logs_dir / "refactor.log",
        }
        self._setup_loggers()

    def _initialize_output_structure(self):
        """Ensures required directories exist and clears old logs."""
        if not self.production:
            DEV_OUTPUT.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def _clear_logs(self):
        """Removes existing log files while preserving the log directory."""
        if self.logs_dir.exists():
            for log_file in self.logs_dir.iterdir():
                if log_file.is_file():
                    log_file.unlink()
        logging.info("🗑️ Cleared existing log files.")

    def _setup_loggers(self):
        """Configures loggers for different EcoOptimizer processes."""
        logging.root.handlers.clear()

        logging.basicConfig(
            filename=str(self.log_files["main"]),
            filemode="a",
            level=logging.INFO,
            format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            force=True,
        )

        self.loggers = {
            "detect": self._create_logger(
                "detect", self.log_files["detect"], self.log_files["main"]
            ),
            "refactor": self._create_logger(
                "refactor", self.log_files["refactor"], self.log_files["main"]
            ),
        }

        logging.info("📝 Loggers initialized successfully.")

    def _create_logger(self, name: str, log_file: Path, main_log_file: Path):
        """
        Creates a logger that logs to both its own file and the main log file.

        Args:
            name (str): Name of the logger.
            log_file (Path): Path to the specific log file.
            main_log_file (Path): Path to the main log file.

        Returns:
            logging.Logger: Configured logger instance.
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        file_handler = logging.FileHandler(str(log_file), mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        main_handler = logging.FileHandler(str(main_log_file), mode="a", encoding="utf-8")
        main_handler.setFormatter(formatter)
        logger.addHandler(main_handler)

        logging.info(f"📝 Logger '{name}' initialized and writing to {log_file}.")
        return logger


def save_file(file_name: str, data: str, mode: str, message: str = ""):
    """Saves data to a file in the output directory."""
    file_path = DEV_OUTPUT / file_name
    with file_path.open(mode) as file:
        file.write(data)
    log_message = message if message else f"📝 {file_name} saved to {file_path!s}"
    logging.info(log_message)


def save_json_files(file_name: str, data: dict[Any, Any] | list[Any]):
    """Saves data to a JSON file in the output directory."""
    file_path = DEV_OUTPUT / file_name
    file_path.write_text(json.dumps(data, cls=EnumEncoder, sort_keys=True, indent=4))
    logging.info(f"📝 {file_name} saved to {file_path!s} as JSON file")


def copy_file_to_output(source_file_path: Path, new_file_name: str):
    """Copies a file to the output directory with a new name."""
    destination_path = DEV_OUTPUT / new_file_name
    shutil.copy(source_file_path, destination_path)
    logging.info(f"📝 {new_file_name} copied to {destination_path!s}")
    return destination_path
