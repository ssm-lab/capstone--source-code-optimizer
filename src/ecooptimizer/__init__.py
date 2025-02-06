# Path of current directory
from pathlib import Path

from .utils.outputs_config import OutputConfig
from .utils.logging_config import setup_logging


DIRNAME = Path(__file__).parent
# Path to output folder
OUTPUT_DIR = (DIRNAME / Path("../../outputs")).resolve()
# Path to log file
# LOG_FILE = OUTPUT_DIR / Path("log.log")

# Entire Project directory path
SAMPLE_PROJ_DIR = (DIRNAME / Path("../../tests/input/project_long_parameter_list")).resolve()

SOURCE = SAMPLE_PROJ_DIR / "src/main.py"
TEST_FILE = SAMPLE_PROJ_DIR / "tests/test_main.py"

setup_logging()

OUTPUT_MANAGER = OutputConfig(OUTPUT_DIR)
