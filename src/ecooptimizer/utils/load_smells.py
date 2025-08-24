from pathlib import Path
import logging
import json
from typing import Any, TypedDict

logger = logging.getLogger()


class SmellDict(TypedDict):
    smells: dict[str, dict[str, Any]]
    dirty: bool


def load_smells_from_file(file_path: Path) -> dict[str, SmellDict]:  # type: ignore
    """Load smells data from a JSON file."""
    logger.debug(f"Attempting to load smells from file: {file_path}")
    try:
        with file_path.open() as f:
            data = json.load(f)
            if not isinstance(data, dict):
                error_msg = "Smells file should contain a dictionary of smell objects"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Detect legacy 2-level dict structure
            if data and all(isinstance(v, dict) and "path" in v for v in data.values()):
                logger.debug("Legacy 2-level smells format detected, converting...")
                converted: dict[str, SmellDict] = {}
                for smell_id, smell_obj in data.items():
                    path = smell_obj.get("path")
                    if not path:
                        error_msg = f"Missing 'path' attribute in smell {smell_id}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    if path not in converted:
                        converted[path] = {"smells": {}, "dirty": False}
                    converted[path]["smells"][smell_id] = smell_obj
                data = converted
                logger.debug("Legacy format successfully converted")

            logger.debug(f"Successfully loaded {len(data)} smells from file")
            return data
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format in smells file: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"Error loading smells file: {e}"
        logger.error(error_msg, exc_info=True)
        raise ValueError(error_msg) from e
