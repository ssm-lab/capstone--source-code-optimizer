# Path of current directory
from pathlib import Path

from ecooptimizer.utils.output_manager import OutputManager

DIRNAME = Path(__file__).parent

# Entire project directory path
SAMPLE_PROJ_DIR = (DIRNAME / Path("../../tests/input/project_car_stuff")).resolve()
SOURCE = SAMPLE_PROJ_DIR / "main.py"
TEST_FILE = SAMPLE_PROJ_DIR / "test_main.py"

LOG_PATH = DIRNAME / Path("../../outputs")

OUTPUT_MANAGER = OutputManager(LOG_PATH)
