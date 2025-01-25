# Path of current directory
import logging
from pathlib import Path

from .utils.outputs_config import OutputConfig


DIRNAME = Path(__file__).parent
# Path to output folder
OUTPUT_DIR = (DIRNAME / Path("../../outputs")).resolve()
# Path to log file
LOG_FILE = OUTPUT_DIR / Path("log.log")

# Entire Project directory path
SAMPLE_PROJ_DIR = (DIRNAME / Path("../../tests/input/project_multi_file_mim")).resolve()

SOURCE = SAMPLE_PROJ_DIR / "src" / "utils.py"
TEST_FILE = SAMPLE_PROJ_DIR / "test_main.py"

logging.basicConfig(
    filename=LOG_FILE,
    filemode="w",
    level=logging.DEBUG,
    format="[ecooptimizer %(levelname)s @ %(asctime)s] %(message)s",
    datefmt="%H:%M:%S",
)

OUTPUT_MANAGER = OutputConfig(OUTPUT_DIR)
